[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://ai-powered-phishing-detector.streamlit.app/)

---

The system is a two-path phishing email classifier. The first path runs a trained Hybrid BERT
model that combines a fine-tuned BERT language model with 11 handcrafted linguistic features
extracted from the cleaned email body. The second path runs a rule-based URL scoring
module that analyzes the structural signals of embedded links in the original (uncleaned) email
text. Both paths produce an independent probability, and the final verdict is determined by
taking the higher of the two scores.
Predictions are served through an interactive Streamlit web application. No training code is
exposed at inference time