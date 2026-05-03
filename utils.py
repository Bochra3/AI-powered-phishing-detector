"""
utils.py
========
Inference utilities for the Streamlit phishing detector.

Relationship between files:
- app.py: Streamlit user interface.
- utils.py: loads saved artifacts and runs one-email inference.
- feature_engineering.py: optional URL-signal helper used only after model scoring.
- streamlit_artifacts/: trained model, tokenizer, config, keywords, feature order.

Model Hosting:
- Models hosted on Hugging Face Hub (huggingface.co)
- Downloaded automatically on first run, cached locally
- Set HF_MODEL_REPO to your repository ID
"""

from pathlib import Path
import json
import re

import torch
import torch.nn as nn
from transformers import BertModel, BertTokenizer

try:
    from huggingface_hub import snapshot_download
except ImportError:
    snapshot_download = None

try:
    from feature_engineering import url_feature_extractor
except Exception:
    url_feature_extractor = None

# ─────────────────────────────────────────────────────────────────────────────
# Hugging Face Configuration
# ─────────────────────────────────────────────────────────────────────────────
# Replace with YOUR Hugging Face repository ID
# Format: "username/repository-name"
# Example: "john-smith/phishing-detector-models"
HF_MODEL_REPO = "hiiikaaaa/phishing-detector-models"
HF_CACHE_DIR = Path.home() / ".cache" / "phishing_detector"


DEVICE = torch.device("cpu")
KEYWORD_DICTS = {}
FEATURE_ORDER = [
    "suspicious_count",
    "urgency_count",
    "financial_count",
    "medical_count",
    "suspicious_score",
    "urgency_score",
    "financial_score",
    "medical_score",
    "word_count",
    "char_count",
    "unique_word_ratio",
]

PHISHING_URL_TERMS = [
    "account",
    "bank",
    "banking",
    "billing",
    "claim",
    "confirm",
    "delivery",
    "document",
    "expiration",
    "expire",
    "gift",
    "hr",
    "login",
    "mail",
    "password",
    "policy",
    "reset",
    "reward",
    "secure",
    "security",
    "signin",
    "track",
    "update",
    "verification",
    "verify",
    "winner",
]


class HybridPhishingDetector(nn.Module):
    def __init__(
        self,
        num_hand_features: int,
        num_labels: int = 2,
        dropout_p: float = 0.3,
        bert_model_path: str = "bert-base-uncased",
    ):
        super().__init__()
        self.bert = BertModel.from_pretrained(bert_model_path)

        self.bert_proj = nn.Sequential(
            nn.Linear(768, 256),
            nn.ReLU(),
            nn.Dropout(dropout_p),
        )
        self.feat_norm = nn.LayerNorm(num_hand_features)

        combined_dim = 256 + num_hand_features
        self.classifier = nn.Sequential(
            nn.Linear(combined_dim, 64),
            nn.ReLU(),
            nn.Dropout(dropout_p),
            nn.Linear(64, num_labels),
        )
        self.loss_fn = None

    def forward(self, input_ids, attention_mask, hand_features=None, labels=None, **kwargs):
        bert_out = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        cls_embed = bert_out.last_hidden_state[:, 0, :]
        bert_proj = self.bert_proj(cls_embed)

        if hand_features is not None:
            feat_norm = self.feat_norm(hand_features)
            combined = torch.cat([bert_proj, feat_norm], dim=1)
        else:
            combined = bert_proj

        logits = self.classifier(combined)
        return {"loss": None, "logits": logits}


def clean_for_model(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_features(text: str) -> dict:
    words = text.split()
    found_by_category = {
        category: [keyword for keyword in KEYWORD_DICTS.get(category, []) if keyword in text]
        for category in ["suspicious", "urgency", "financial", "medical"]
    }

    feature_values = {
        "suspicious_count": len(found_by_category["suspicious"]),
        "urgency_count": len(found_by_category["urgency"]),
        "financial_count": len(found_by_category["financial"]),
        "medical_count": len(found_by_category["medical"]),
        "word_count": len(words),
        "char_count": len(text),
        "unique_word_ratio": len(set(words)) / max(len(words), 1),
    }
    feature_values["suspicious_score"] = feature_values["suspicious_count"] / max(len(words), 1)
    feature_values["urgency_score"] = feature_values["urgency_count"] / max(len(words), 1)
    feature_values["financial_score"] = feature_values["financial_count"] / max(len(words), 1)
    feature_values["medical_score"] = feature_values["medical_count"] / max(len(words), 1)

    return {name: feature_values[name] for name in FEATURE_ORDER}


def explain_keywords(text: str) -> dict:
    return {
        category: [keyword for keyword in keywords if keyword in text]
        for category, keywords in KEYWORD_DICTS.items()
    }


def load_model(artifact_dir: str = "streamlit_artifacts"):
    """
    Load model from local cache or download from Hugging Face Hub.
    
    On first run: downloads from HF and caches locally (~800 MB, takes 2-5 min)
    On subsequent runs: loads from local cache instantly
    """
    global KEYWORD_DICTS, FEATURE_ORDER

    # Try to use local artifacts first
    artifact_dir = Path(artifact_dir)
    
    # If local path doesn't exist or is incomplete, download from HF
    if not _check_artifacts_exist(artifact_dir):
        if HF_MODEL_REPO == "YOUR_REPO_ID_HERE":
            raise ValueError(
                "❌ ERROR: HF_MODEL_REPO not configured in utils.py\n"
                "Please set it to your Hugging Face repository ID first.\n"
                "See DEPLOYMENT_SETUP.md for instructions."
            )
        
        if snapshot_download is None:
            raise ImportError(
                "❌ huggingface_hub not installed.\n"
                "Run: pip install huggingface_hub"
            )
        
        # Download from Hugging Face
        artifact_dir = Path(
            snapshot_download(
                repo_id=HF_MODEL_REPO,
                cache_dir=HF_CACHE_DIR,
                repo_type="model",
            )
        )

    # Load model as before
    with open(artifact_dir / "model_config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    with open(artifact_dir / "keyword_dicts.json", "r", encoding="utf-8") as f:
        KEYWORD_DICTS = json.load(f)

    with open(artifact_dir / "feature_names.json", "r", encoding="utf-8") as f:
        FEATURE_ORDER = json.load(f)

    model = HybridPhishingDetector(
        num_hand_features=config["num_hand_features"],
        num_labels=config["num_labels"],
        dropout_p=config["dropout_p"],
        bert_model_path=str(artifact_dir / "bert_backbone"),
    ).to(DEVICE)

    state_dict = torch.load(
        artifact_dir / "hybrid_model_weights.pt",
        map_location=DEVICE,
    )
    state_dict = {
        key: value
        for key, value in state_dict.items()
        if not key.startswith("loss_fn.")
    }
    model.load_state_dict(state_dict)
    model.eval()

    tokenizer = BertTokenizer.from_pretrained(str(artifact_dir / "tokenizer"))
    return model, tokenizer, config


def _check_artifacts_exist(artifact_dir: Path) -> bool:
    """Check if all required model files exist locally."""
    required_files = [
        "model_config.json",
        "keyword_dicts.json",
        "feature_names.json",
        "hybrid_model_weights.pt",
        "bert_backbone/config.json",
        "tokenizer/tokenizer.json",
    ]
    return all((artifact_dir / f).exists() for f in required_files)


def _empty_url_signals() -> dict:
    return {
        "has_url": 0,
        "num_urls": 0,
        "domain": "",
        "is_shortened_url": 0,
        "suspicious_url_keywords": 0,
        "domain_score": 0.0,
    }


def _extract_raw_urls(email_text: str) -> list[str]:
    if not isinstance(email_text, str):
        return []
    return re.findall(r"https?://\S+|www\.\S+", email_text.lower())


def url_risk_score(url_signals: dict, email_text: str) -> tuple[float, str | None, list[str]]:
    domain_score = url_signals.get("domain_score", 0.0)
    has_url = url_signals.get("has_url", 0)
    is_shortened = url_signals.get("is_shortened_url", 0)
    suspicious_kw = url_signals.get("suspicious_url_keywords", 0)

    if not has_url:
        return 0.0, None, []

    url_blob = " ".join(_extract_raw_urls(email_text))
    matched_terms = [term for term in PHISHING_URL_TERMS if term in url_blob]

    score = 0.15
    score += min(float(domain_score) * 0.35, 0.35)

    if suspicious_kw:
        score += 0.30
    if is_shortened:
        score += 0.20

    score += min(len(matched_terms) * 0.12, 0.45)

    if len(matched_terms) >= 2:
        score = max(score, 0.75)
    elif suspicious_kw:
        score = max(score, 0.65)
    elif domain_score >= 0.50:
        score = max(score, 0.60)

    score = round(min(score, 0.98), 4)

    if len(matched_terms) >= 2:
        reason = "URL contains multiple phishing terms: " + ", ".join(matched_terms[:5])
    elif suspicious_kw:
        reason = "Phishing keyword detected in URL"
    elif domain_score >= 0.50:
        reason = f"Suspicious domain structure (score: {domain_score})"
    elif is_shortened:
        reason = "Shortened URL detected"
    else:
        reason = "URL detected"

    return score, reason, matched_terms


def fuse_bert_and_url(
    phishing_prob: float,
    url_signals: dict,
    email_text: str,
) -> tuple[float, float, str | None, list[str]]:
    url_prob, reason, matched_terms = url_risk_score(url_signals, email_text)
    final_prob = max(phishing_prob, url_prob)

    if url_prob > phishing_prob and reason:
        fusion_reason = f"URL risk raised the final verdict: {reason}"
    elif reason:
        fusion_reason = f"BERT score was stronger; URL signal also found: {reason}"
    else:
        fusion_reason = None

    return round(final_prob, 4), url_prob, fusion_reason, matched_terms


def predict_email(
    email_text: str,
    model: HybridPhishingDetector,
    tokenizer: BertTokenizer,
    config: dict,
    threshold: float | None = None,
) -> dict:
    text = clean_for_model(email_text)
    feats = extract_features(text)
    feat_tensor = torch.tensor(list(feats.values()), dtype=torch.float).unsqueeze(0).to(DEVICE)

    encoding = tokenizer(
        text,
        truncation=True,
        padding=True,
        max_length=config.get("max_len", 256),
        return_tensors="pt",
    )
    input_ids = encoding["input_ids"].to(DEVICE)
    attention_mask = encoding["attention_mask"].to(DEVICE)

    model.eval()
    with torch.no_grad():
        output = model(input_ids, attention_mask, hand_features=feat_tensor)

    probs = torch.softmax(output["logits"], dim=1).cpu().numpy()[0]
    phishing_prob = float(probs[1])

    url_signals = _empty_url_signals()
    if url_feature_extractor is not None:
        url_signals = url_feature_extractor(email_text)
    final_prob, url_prob, fusion_reason, url_terms = fuse_bert_and_url(
        phishing_prob,
        url_signals,
        email_text,
    )

    threshold = config.get("threshold", 0.5) if threshold is None else threshold
    label = "PHISHING" if final_prob >= threshold else "SAFE"
    confidence = final_prob if label == "PHISHING" else 1.0 - final_prob

    return {
        "label": label,
        "confidence": round(confidence * 100, 1),
        "phishing_prob": round(phishing_prob, 4),
        "final_prob": round(final_prob, 4),
        "url_prob": round(url_prob, 4),
        "url_terms": url_terms,
        "features": feats,
        "explanation": explain_keywords(text),
        "url_signals": url_signals,
        "override_reason": fusion_reason,
        "fusion_reason": fusion_reason,
    }