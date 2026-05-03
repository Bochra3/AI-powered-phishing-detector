# 🛡️ AI-Powered Phishing Email Detector

A Streamlit-based inference app that uses a hybrid BERT model combined with URL-based heuristics to detect phishing emails in real time.

## Features

- **Hybrid Detection**: Combines deep learning (BERT) with URL-based risk signals
- **Real-time Inference**: Analyzes emails instantly with pre-trained model
- **Explainability**: Shows confidence scores and keyword/URL-based reasoning
- **Production-Ready**: Optimized for Streamlit Community Cloud deployment

---

## Running Locally

### Prerequisites
- Python 3.9+
- pip or conda

### Installation

1. **Clone the repository** (or download the files):
   ```bash
   cd AI-Powered-Phishing-Detector
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Running the App

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

### How to Use
1. Paste email content into the text area
2. Click "Analyze Email"
3. View results:
   - **Label**: PHISHING or SAFE
   - **Confidence**: Overall confidence score
   - **BERT Score**: Deep learning model confidence
   - **URL Score**: Heuristic-based URL risk assessment

---

## Deployment to Streamlit Community Cloud

### Quick Start

1. **Commit to GitHub** (skip this if using other methods):
   ```bash
   git add .
   git commit -m "Prepare for Streamlit Cloud deployment"
   git push origin main
   ```

2. **Deploy on Streamlit Cloud**:
   - Go to [Streamlit Community Cloud](https://streamlit.io/cloud)
   - Click "New app"
   - Select your GitHub repo, branch, and main file (`app.py`)
   - Click "Deploy"

### Important Notes

#### Large Model Files
The `streamlit_artifacts/` folder contains pre-trained model weights (~836 MB total):
- `hybrid_model_weights.pt`: 418 MB (BERT fine-tuned hybrid model)
- `bert_backbone/model.safetensors`: 417 MB (BERT base backbone)
- `tokenizer/`: ~0.7 MB (tokenizer files)

**GitHub Limit**: GitHub blocks files >100 MB by default. If you encounter this:

**Option 1: Use Git LFS** (Large File Storage)
```bash
# Install Git LFS
git lfs install

# Track large files
git lfs track "streamlit_artifacts/*.pt"
git lfs track "streamlit_artifacts/bert_backbone/*.safetensors"

# Commit
git add .gitattributes streamlit_artifacts/
git commit -m "Add large model files with Git LFS"
git push origin main
```

**Option 2: Use Streamlit Secrets + External Storage**
- Host model files on cloud storage (AWS S3, Google Cloud Storage, etc.)
- Download at app startup via secrets configuration
- *(More complex but doesn't require Git LFS)*

**Option 3: Keep Files Locally**
- If testing locally, files are already in `streamlit_artifacts/`
- App loads them from relative path `"streamlit_artifacts"`

#### Environment Variables (if using external storage)
Create `.streamlit/secrets.toml` in your local repo (add to `.gitignore`):
```toml
# Example: if hosting models on S3
aws_access_key = "your-key"
aws_secret_key = "your-secret"
s3_bucket = "your-bucket"
```

Then update `utils.py` to load from secrets if needed.

#### Data Files
- ✅ **NOT needed for deployment**: `modified_dataset.xlsx`, `original_dataset.xlsx`
- These are only used for training (excluded via `.gitignore`)
- App runs inference only; no retraining occurs

---

## Project Structure

```
.
├── app.py                     # Streamlit UI (main entry point)
├── utils.py                   # Model loading & inference
├── feature_engineering.py     # URL-based feature extraction
├── requirements.txt           # Python dependencies
├── .gitignore                 # Files to exclude from git
├── .streamlit/
│   └── config.toml           # Streamlit deployment config
├── streamlit_artifacts/      # Pre-trained model & tokenizer
│   ├── model_config.json
│   ├── hybrid_model_weights.pt (418 MB)
│   ├── keyword_dicts.json
│   ├── feature_names.json
│   ├── class_weights.pt
│   ├── bert_backbone/
│   │   ├── config.json
│   │   └── model.safetensors (417 MB)
│   └── tokenizer/
│       ├── tokenizer.json
│       └── tokenizer_config.json
└── README.md                 # This file
```

---

## Technical Details

### Model Architecture
- **BERT Base**: Pre-trained BERT backbone (uncased)
- **Hand-Crafted Features**: Keyword counts, email metrics (word count, char count, unique word ratio)
- **Hybrid Classifier**: Combines BERT embeddings + hand features via concatenation
- **URL Heuristics**: Domain risk scoring, shortener detection, keyword matching

### Runtime Dependencies
- `streamlit`: Web UI framework
- `torch`: Deep learning (inference only)
- `transformers`: BERT model loading
- `safetensors`: Safe model file format

**No training dependencies required** — all code is inference-only.

---

## Troubleshooting

### App won't start: "ModuleNotFoundError"
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Model files not found locally
- Ensure `streamlit_artifacts/` folder exists with all files
- Check relative path in `app.py`: `load_model("streamlit_artifacts")`

### Slow startup on Streamlit Cloud
- Model loading (~800 MB) can take 30-60 seconds on first load
- Streamlit caches the model with `@st.cache_resource` — subsequent requests are instant

### "CUDA not available" warning
- This is normal — the app uses CPU inference by default
- On cloud, GPU is not available anyway; CPU is fine for batch inference

---

## Files to Exclude from Git

Already handled by `.gitignore`:
- `*.xlsx`, `*.csv`: Raw/processed data (training only)
- `*.ipynb`: Training notebook (see `main.ipynb` for reference)
- `__pycache__/`: Python cache
- `.env`: Environment secrets
- Large PDFs and documentation

---

## Future Enhancements

- [ ] Add A/B testing capabilities
- [ ] Implement batch email analysis
- [ ] Add admin dashboard for model performance monitoring
- [ ] Support multiple languages

---

## License

[Your License Here]

---

## Contact

For questions or issues, open a GitHub issue or contact the maintainer.