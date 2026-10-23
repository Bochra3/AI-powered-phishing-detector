[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://ai-powered-phishing-detector.streamlit.app/)

# 🛡️ AI-Powered Phishing Email Detector

> A two-path phishing classifier that combines a fine-tuned **BERT** model with **handcrafted linguistic features** and a transparent **rule-based URL scorer**, served through an interactive **Streamlit** app.

[![Model on Hugging Face](https://img.shields.io/badge/🤗%20Model-Hugging%20Face-FFD21E)](https://huggingface.co/hiiikaaaa/phishing-detector-models)

**Course:** Information Security and Assurance, Tunis Business School, May 2026

---

## 📌 Table of Contents

- [Motivation](#-motivation)
- [How It Works](#️-how-it-works)
- [Layer 1: URL Scoring](#-layer-1--url-scoring)
- [Layer 2: Hybrid BERT Model](#-layer-2--hybrid-bert-model)
- [Layer 3: Fusion and Verdict](#-layer-3--fusion-and-verdict)
- [Results](#-results)
- [Project Structure](#-project-structure)
- [Tech Stack](#-tech-stack)
- [Design Decisions](#️-design-decisions)
- [Limitations](#️-limitations)
- [Team](#-team)

---

## 🎯 Motivation

In January 2025, a mid-sized financial firm (*FinSecure Ltd*, the case study for this project) suffered three successful phishing attacks in a single quarter. All three emails **bypassed the rule-based spam filter**: no spelling mistakes, no blacklisted domains, and perfect grammar. They were traced back to **AI-generated content** (LLMs such as ChatGPT).

Classic filters rely on signals like bad grammar and known-bad signatures, and AI-written phishing removes those signals. Effective detection now has to analyze two things at once:

1. **The semantic content** of the email body (meaning and tone), and
2. **The structural signals** hidden in embedded URLs.

This project uses the same category of technology attackers are exploiting to defend against them.

### Background: what is phishing?

Phishing is a social-engineering attack in which the attacker impersonates a trusted entity to steal credentials or money. It exploits **human psychology** rather than technical vulnerabilities:

| Trigger | Example |
|---|---|
| Urgency | "Act now or your account will be suspended" |
| Fear | "Unauthorized access has been detected" |
| Authority | "Message from the IT Department" |
| Curiosity | "You have a confidential document pending review" |

Common types include **mass phishing** (generic bulk emails), **spear phishing** (targeted, personalized) and **whaling** (targeting executives for large-scale fraud).

---

## ⚙️ How It Works

The system runs **two independent detection paths** and combines them at inference time. Each path catches a class of attack the other may miss.

```
                    Raw Email Text
                          │
        ┌─────────────────┴─────────────────┐
        ▼                                   ▼
 URL Feature Extractor                 Text Cleaning
 (raw text, URLs intact)         (strip URLs, HTML, lowercase)
        │                                   │
   6 URL features                    11 linguistic features
        │                            + BERT [CLS] embedding
  url_risk_score()                          │
        │                           HybridPhishingDetector
  URL probability                           │
        │                            Hybrid BERT score
        └─────────────────┬─────────────────┘
                          ▼
                       Fusion
              final = max(BERT, URL)
                          ▼
                    Streamlit UI
          PHISHING / SAFE + confidence
               + both sub-scores
```

**Step by step:**

1. **Input:** the raw email text is pasted into the app.
2. **URL analysis:** performed *before* any cleaning, so links are still intact.
3. **Text cleaning:** URLs and HTML are stripped, text is lowercased and normalized (mirrors training preprocessing).
4. **Linguistic feature extraction:** 11 semantic and frequency-based signals.
5. **BERT inference:** cleaned text and the 11 features are passed jointly through the hybrid model.
6. **Fusion:** the higher of the two scores becomes the final phishing probability.
7. **Verdict:** compared against a threshold (θ = 0.5) and displayed with both sub-scores.

---

## 🔗 Layer 1 · URL Scoring

Implemented in `feature_engineering.py` using **only the Python standard library** (`re`, `urllib.parse`). It needs no trained model and is fully interpretable.

### The 6 URL features

| Feature | Type | Description |
|---|---|---|
| `has_url` | Binary | At least one URL is present |
| `num_urls` | Integer | Count of unique URLs extracted |
| `domain` | String | Primary domain (from the first URL) |
| `is_shortened_url` | Binary | Domain matches a 20-entry URL-shortener blocklist (e.g. bit.ly) |
| `suspicious_url_keywords` | Binary | A phishing keyword appears in the URL string |
| `domain_score` | Float [0, 1] | Heuristic domain suspicion score |

### Domain suspicion score

Three weighted penalties, each capped independently before summing, with the total clamped to [0, 1]:

| Signal | Weight per unit | Cap |
|---|---|---|
| Hyphens in registrable domain | ×0.20 | 0.40 |
| Subdomain depth (levels beyond root) | ×0.15 | 0.45 |
| Phishing keyword hits in domain | ×0.25 | 0.50 |

### URL risk score

```text
url_prob = 0.15
         + min(domain_score × 0.35, 0.35)
         + 0.30 · [suspicious URL keyword found]
         + 0.20 · [shortened URL]
         + min(#matched_terms × 0.12, 0.45)
```

**Floor guarantees:**

- ≥ 2 phishing terms matched in the URL → `url_prob ≥ 0.75`
- Suspicious URL keyword present → `url_prob ≥ 0.65`
- `domain_score ≥ 0.50` → `url_prob ≥ 0.60`

The score is capped at **0.98**. Emails with no URL receive `url_prob = 0.0`.

---

## 🧠 Layer 2 · Hybrid BERT Model

BERT understands *meaning*, while handcrafted signals count *explicit red flags*. The two are merged inside one neural network.

### The 11 handcrafted linguistic features

| Category | Features |
|---|---|
| Suspicious (29-term lexicon) | `suspicious_count`, `suspicious_score` |
| Urgency (18 terms) | `urgency_count`, `urgency_score` |
| Financial (25 terms) | `financial_count`, `financial_score` |
| Medical / pharma scam (20 terms) | `medical_count`, `medical_score` |
| Text statistics | `word_count`, `char_count`, `unique_word_ratio` |

`*_score` features are `count / word_count`, which keeps them robust to long emails. `unique_word_ratio` is an inverse "spamminess" signal.

### Architecture (`HybridPhishingDetector`)

| Stage | Detail |
|---|---|
| BERT encoder | `bert-base-uncased`, `[CLS]` token → 768-d embedding |
| Projection | Linear(768→256) + ReLU + Dropout(0.3) |
| Concatenation | 256-d BERT projection ‖ 11-d LayerNorm(features) = **267-d** |
| Classifier | Linear(267→64) + ReLU + Dropout(0.3) → Linear(64→2) |
| Output | Softmax → `phishing_prob ∈ [0, 1]` |

### Training setup

- **Base model:** `bert-base-uncased` from the Hugging Face Hub, fine-tuned end to end.
- **Loss:** class-weighted cross-entropy, which penalizes *missed phishing* more than false alarms (biased toward recall to minimize credential-theft risk).
- **Epochs:** 5, evaluated at the end of each epoch.
- **Model selection:** best checkpoint chosen by **F1 score** (prioritized over raw accuracy).

---

## 🔀 Layer 3 · Fusion and Verdict

```python
final_prob = max(phishing_prob, url_prob)

label      = "PHISHING" if final_prob >= threshold else "SAFE"   # threshold = 0.5 (configurable)
confidence = final_prob if label == "PHISHING" else 1.0 - final_prob
```

Either signal alone is enough to flag an email:

- Clean, well-written prose containing a **malicious link** → caught by the URL path.
- A **link-free** email with manipulative language → caught by the BERT path.

---

## 📊 Results

Evaluated on the held-out test set (6,000 emails):

|  | Predicted Ham | Predicted Phishing |
|---|:---:|:---:|
| **Actual Ham** | 3,977 | 63 |
| **Actual Phishing** | 61 | 1,899 |

| Metric | Value |
|---|---|
| Accuracy | ≈ 97.9% |
| Precision (phishing) | ≈ 96.8% |
| **Recall (phishing)** | **≈ 96.9%** |
| F1 (phishing) | ≈ 96.8% |

The best validation checkpoint (epoch 3) reached roughly **0.975 F1** and **98.4% accuracy**. These figures evaluate the **Hybrid BERT model alone**; the URL layer is rule-based and was not benchmarked separately.

---

## 📁 Project Structure

```
.
├── main.ipynb              # Training notebook (run once, never at serving time)
├── utils.py                # Inference hub: model loading, features, URL scoring, fusion
├── feature_engineering.py  # URL extraction and domain heuristics (stdlib only)
├── app.py                  # Streamlit user interface
└── streamlit_artifacts/    # Saved model (hosted on Hugging Face, see below)
```

| File | Responsibility |
|---|---|
| `app.py` | UI layer, calls `utils.predict_email()` |
| `utils.py` | Single inference entry point (`predict_email()`), returns `label`, `confidence`, `phishing_prob`, `url_prob` |
| `feature_engineering.py` | Regex-based URL parser and domain scorer |
| `streamlit_artifacts/` | `bert_backbone/`, `tokenizer/`, `hybrid_model_weights.pt`, `class_weights.pt`, `feature_names.json`, `keyword_dicts.json`, `model_config.json` |

---

## 🧰 Tech Stack

| Layer | Tool | Role |
|---|---|---|
| Language model | Hugging Face Transformers (`bert-base-uncased`) | Text classification backbone |
| Model hosting | Hugging Face Hub | Stores the trained weights and artifacts |
| Deep learning | PyTorch (`nn.Module`) | Custom hybrid classifier |
| Experimentation | Jupyter (`main.ipynb`) | Training pipeline |
| URL analysis | Python stdlib (`re`, `urllib.parse`) | URL parsing and domain scoring |
| Serving | Streamlit | Interactive web demo |
| Model caching | `@st.cache_resource` | Model loaded once at startup |

---

## 🏗️ Design Decisions

1. **Two independent paths fused with `max()`.** A failure in one path never masks a true positive caught by the other.
2. **Linguistic features inside the model, URL features outside.** The 11 text features are injected after the BERT projection. URL features never touch BERT and are scored by a transparent formula, so both paths stay interpretable.
3. **URL analysis on raw text, BERT on cleaned text.** Links must be intact for URL inspection, while the model sees the same cleaned format it was trained on.
4. **No training code at inference.** `app.py` depends only on `load_model()` and `predict_email()`, keeping the serving surface minimal.
5. **Stdlib-only URL layer.** Zero extra dependencies improves portability and reduces supply-chain risk.

---

## ⚠️ Limitations

- `max()` fusion favors recall: a high score from either path flags the email, which can raise false positives, for example on legitimate emails containing shortened links.
- URL scoring is heuristic and keyword-based. It does not check domain age, redirect chains, homograph attacks, or live reputation databases.
- The domain score is computed from the **first URL** in the email only.
- The system analyzes email body text only. Headers (SPF/DKIM/DMARC), attachments, and sender reputation are not considered.
- Performance depends on the training data distribution and may degrade on new attack styles without retraining.

---

## 👥 Team

- Soujoud Khaled
- Khouloud Gabsi
- Menyare Zitouni
- Bochra Messaoud
- Ryhem Ben Slama

*Information Security and Assurance, Tunis Business School, May 2026*

