"""
feature_engineering.py
======================
URL-based phishing feature engineering module.

Production entry point
----------------------
    from feature_engineering import url_feature_extractor
    features = url_feature_extractor(email_text)

Dependencies: Python standard library only (re, urllib.parse, typing)
"""

import re
from urllib.parse import urlparse
from typing import List, Dict, Any

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

PHISHING_KEYWORDS: List[str] = [
    "login", "verify", "secure", "update", "account", "bank",
    "signin", "password", "confirm", "billing", "support",
    "recover", "validate", "suspend", "alert", "unlock",
]

SHORTENER_DOMAINS: List[str] = [
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly",
    "is.gd", "buff.ly", "rebrand.ly", "short.io", "bl.ink",
    "shorte.st", "adf.ly", "lnk.bio", "snip.ly", "cutt.ly",
    "rb.gy", "tiny.cc", "qr.io", "s.id", "clck.ru",
]

DOMAIN_SCORE_WEIGHTS = {
    "hyphen_penalty":           0.20,
    "subdomain_depth_penalty":  0.15,
    "keyword_penalty":          0.25,
    "hyphen_penalty_cap":       0.40,
    "keyword_penalty_cap":      0.50,
}

URL_PATTERN = re.compile(
    r'https?://'
    r'(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)'
    r'+[A-Za-z]{2,}'
    r'(?:/[^\s<>"{}|\\^`\[\]]*)?',
    re.IGNORECASE,
)

# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

def extract_urls(text: str) -> List[str]:
    if not isinstance(text, str) or not text.strip():
        return []
    matches = URL_PATTERN.findall(text)
    seen, unique_urls = set(), []
    for url in matches:
        url_clean = url.rstrip(".,;:'\")")
        if url_clean not in seen:
            seen.add(url_clean)
            unique_urls.append(url_clean)
    return unique_urls


def extract_domain(url: str) -> str:
    if not isinstance(url, str) or not url.strip():
        return ""
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower().strip().split(":")[0]
        return netloc
    except Exception:
        return ""


def _compute_domain_score(domain: str) -> float:
    if not domain:
        return 0.0
    w = DOMAIN_SCORE_WEIGHTS
    score = 0.0
    parts = domain.split(".")
    registrable = parts[-2] if len(parts) >= 2 else domain
    hyphen_count = registrable.count("-")
    score += min(hyphen_count * w["hyphen_penalty"], w["hyphen_penalty_cap"])
    subdomain_depth = max(0, len(parts) - 2 - 1)
    score += min(subdomain_depth * w["subdomain_depth_penalty"], 0.45)
    keyword_hits = sum(1 for kw in PHISHING_KEYWORDS if kw in domain.lower())
    score += min(keyword_hits * w["keyword_penalty"], w["keyword_penalty_cap"])
    return round(min(score, 1.0), 2)


def extract_url_features(text: str) -> Dict[str, Any]:
    urls = extract_urls(text)
    has_url = 1 if urls else 0
    primary_domain = extract_domain(urls[0]) if urls else ""
    is_shortened = int(any(extract_domain(u) in SHORTENER_DOMAINS for u in urls))
    all_urls_str = " ".join(urls).lower()
    suspicious_keywords = int(any(kw in all_urls_str for kw in PHISHING_KEYWORDS))
    domain_score = _compute_domain_score(primary_domain) if primary_domain else 0.0
    return {
        "has_url":                  has_url,
        "num_urls":                 len(urls),
        "extracted_urls":           urls,
        "domain":                   primary_domain,
        "is_shortened_url":         is_shortened,
        "suspicious_url_keywords":  suspicious_keywords,
        "domain_score":             domain_score,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Production Entry Point
# ─────────────────────────────────────────────────────────────────────────────

def url_feature_extractor(text: str) -> Dict[str, Any]:
    """
    Production entry point: extract URL-based phishing features from raw email text.
    Call this on the ORIGINAL (uncleaned) email text so URLs are still present.

    Usage
    -----
        from feature_engineering import url_feature_extractor
        features = url_feature_extractor(email_text)  # raw text, before cleaning

    Returns
    -------
    dict with keys:
        has_url               (int)   : 1 if any URL present
        num_urls              (int)   : count of unique URLs
        domain                (str)   : primary domain string
        is_shortened_url      (int)   : 1 if known shortener detected
        suspicious_url_keywords (int) : 1 if phishing keywords in URL
        domain_score          (float) : heuristic suspicion score [0.0, 1.0]
    """
    if not isinstance(text, str):
        text = str(text) if text is not None else ""
    all_features = extract_url_features(text)
    return {
        "has_url":                  all_features["has_url"],
        "num_urls":                 all_features["num_urls"],
        "domain":                   all_features["domain"],
        "is_shortened_url":         all_features["is_shortened_url"],
        "suspicious_url_keywords":  all_features["suspicious_url_keywords"],
        "domain_score":             all_features["domain_score"],
    }
