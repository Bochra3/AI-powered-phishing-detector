"""
app.py
======
Phishing Email Detection — Streamlit Demo App.
Inference only. No training code.

Run with:
    streamlit run app.py
"""

import streamlit as st
from utils import load_model, predict_email

# ─────────────────────────────────────────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Phishing Detector",
    page_icon="🛡️",
    layout="centered",
)

# ─────────────────────────────────────────────────────────────────────────────
# Custom CSS  (minimal, presentation-ready)
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    /* Page background */
    .stApp { background-color: #0f1117; }

    /* Title */
    .title-block {
        text-align: center;
        padding: 2rem 0 1.5rem 0;
    }
    .title-block h1 {
        font-size: 2.2rem;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: -0.5px;
        margin: 0;
    }
    .title-block p {
        color: #8b8fa8;
        font-size: 0.95rem;
        margin-top: 0.4rem;
    }

    /* Text area */
    .stTextArea textarea {
        background-color: #1c1f2e !important;
        color: #e8eaf6 !important;
        border: 1px solid #2d3150 !important;
        border-radius: 10px !important;
        font-size: 0.95rem !important;
        line-height: 1.6 !important;
    }
    .stTextArea textarea:focus {
        border-color: #5c6bc0 !important;
        box-shadow: 0 0 0 2px rgba(92, 107, 192, 0.2) !important;
    }

    /* Analyze button */
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #5c6bc0, #3949ab) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.75rem 1.5rem !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.3px !important;
        transition: opacity 0.2s ease !important;
        margin-top: 0.5rem;
    }
    .stButton > button:hover { opacity: 0.88 !important; }

    /* Result cards */
    .result-card {
        border-radius: 14px;
        padding: 2rem 2.5rem;
        margin-top: 1.5rem;
        text-align: center;
    }
    .result-phishing {
        background-color: #1a0a0a;
        border: 2px solid #c62828;
    }
    .result-safe {
        background-color: #0a1a0e;
        border: 2px solid #2e7d32;
    }
    .result-label {
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: 2px;
        margin: 0;
    }
    .result-label-phishing { color: #ef5350; }
    .result-label-safe     { color: #66bb6a; }
    .result-confidence {
        font-size: 1rem;
        color: #8b8fa8;
        margin-top: 0.5rem;
    }
    .score-row {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.6rem;
        margin-top: 1.2rem;
    }
    .score-pill {
        background-color: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 10px;
        padding: 0.75rem 0.5rem;
    }
    .score-label {
        color: #8b8fa8;
        font-size: 0.75rem;
        margin: 0 0 0.25rem 0;
    }
    .score-value {
        color: #ffffff;
        font-size: 1.05rem;
        font-weight: 700;
        margin: 0;
    }
    /* Divider */
    hr { border-color: #2d3150 !important; }

    /* Hide Streamlit default chrome */
    #MainMenu { visibility: hidden; }
    footer     { visibility: hidden; }
    header     { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Load Model (cached — runs once at startup)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner="Loading model…")
def get_model():
    return load_model("streamlit_artifacts")

model, tokenizer, config = get_model()

# ─────────────────────────────────────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="title-block">
    <h1>🛡️ Phishing Email Detector</h1>
</div>
""", unsafe_allow_html=True)

email_input = st.text_area(
    label="Email content",
    label_visibility="collapsed",
    placeholder="Paste email text here…",
    height=220,
)

analyze = st.button("Analyze Email", use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# Inference
# ─────────────────────────────────────────────────────────────────────────────

if analyze:
    if not email_input.strip():
        st.warning("Please paste an email to analyze.")
    else:
        with st.spinner("Analyzing…"):
            result = predict_email(
                email_text=email_input,
                model=model,
                tokenizer=tokenizer,
                config=config,
            )

        label      = result["label"]
        confidence = result["confidence"]
        bert_prob  = result["phishing_prob"] * 100
        url_prob   = result["url_prob"] * 100

        is_phishing = label == "PHISHING"

        card_class   = "result-phishing" if is_phishing else "result-safe"
        label_class  = "result-label-phishing" if is_phishing else "result-label-safe"
        icon         = "⚠️" if is_phishing else "✅"

        st.markdown(f"""
        <div class="result-card {card_class}">
            <p class="result-label {label_class}">{icon} {label}</p>
            <p class="result-confidence">Confidence: {confidence:.1f}%</p>
            <div class="score-row">
                <div class="score-pill">
                    <p class="score-label">Hybrid BERT score</p>
                    <p class="score-value">{bert_prob:.1f}%</p>
                </div>
                <div class="score-pill">
                    <p class="score-label">URL score</p>
                    <p class="score-value">{url_prob:.1f}%</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
