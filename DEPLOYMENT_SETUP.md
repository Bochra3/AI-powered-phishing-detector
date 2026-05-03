# 🚀 Deployment Setup — Beginner's Guide

**You need to do this ONCE before pushing to GitHub.**

---

## Step 1: Create a Hugging Face Account (5 min)

1. Go to https://huggingface.co/
2. Click **"Sign up"** (top right)
3. Fill in:
   - Email
   - Password
   - Username (pick anything, e.g., `john-phishing-detector`)
4. Click "Sign up"
5. Check your email and verify

✅ **Done!** You now have a free account.

---

## Step 2: Create a Model Repository on Hugging Face (2 min)

1. After signing up, go to https://huggingface.co/new
2. Fill in the form:
   - **Repository name**: `phishing-detector-models` (or any name you like)
   - **Repository type**: Select "Model" (should be default)
   - **License**: "openrail" (or "mit", doesn't matter)
   - **Private**: Select "Private" (keeps your files private) ← **IMPORTANT**
3. Click **"Create repository"**

✅ **Done!** You now have a repo. Keep this page open — you'll need it next.

---

## Step 3: Upload Model Files (10 min)

You're still on your new repository page. Look for an **"Upload file"** button.

1. Click **"Upload file"** (or drag and drop area)
2. Go to your computer:
   - Navigate to: `AI-Powered-Phishing-Detector\streamlit_artifacts\`
3. Select these files to upload (one at a time or all together):

   **MUST UPLOAD:**
   - `hybrid_model_weights.pt` (418 MB)
   - `bert_backbone/model.safetensors` (417 MB)
   - `bert_backbone/config.json` (small)
   - `tokenizer/tokenizer.json` (~0.7 MB)
   - `tokenizer/tokenizer_config.json` (small)
   - `model_config.json` (small)
   - `keyword_dicts.json` (small)
   - `feature_names.json` (small)

   **DO NOT UPLOAD:**
   - `class_weights.pt` (not needed for inference)

4. Upload them (you can drag & drop all at once)
5. Wait for uploads to finish (the big files take 2-5 min each)

✅ **Done!** All model files are now hosted on Hugging Face.

---

## Step 4: Get Your Repository ID (30 seconds)

On your Hugging Face repo page, look at the URL in the address bar. It looks like:

```
https://huggingface.co/YOUR_USERNAME/phishing-detector-models
```

Your **Repository ID** is: `YOUR_USERNAME/phishing-detector-models`

**Copy this ID and save it somewhere** — you'll need it in the next step.

Example: If your username is `john-smith` and repo is `phishing-detector-models`, then your ID is:
```
john-smith/phishing-detector-models
```

---

## Step 5: Update Your Code (2 min)

The code has already been modified to download models from Hugging Face automatically. 

**You just need to:**

1. Open the file: `AI-Powered-Phishing-Detector\utils.py`
2. Find the line that says: `HF_MODEL_REPO = "YOUR_REPO_ID_HERE"`
3. Replace `YOUR_REPO_ID_HERE` with your Repository ID from Step 4

**Example:**
```python
# BEFORE:
HF_MODEL_REPO = "YOUR_REPO_ID_HERE"

# AFTER:
HF_MODEL_REPO = "john-smith/phishing-detector-models"
```

✅ **Done!** The app will now download models from Hugging Face.

---

## Step 6: Push to GitHub (3 min)

1. Open VS Code
2. Click the **Source Control** icon (left sidebar, looks like branching lines)
3. You should see all your files listed as changes
4. Type a message in the box at the top, e.g.: `Initial commit: phishing detector with HF models`
5. Click **"Commit"** (checkmark button)
6. Click **"Sync Changes"** (should say "Publish branch" if first time)

✅ **Done!** Your code is now on GitHub (model files stay on Hugging Face).

---

## Step 7: Deploy to Streamlit Cloud (5 min)

1. Go to https://streamlit.io/cloud
2. Click **"New app"**
3. Connect your GitHub account if asked
4. Select:
   - **Repository**: `YOUR_USERNAME/AI-Powered-Phishing-Detector`
   - **Branch**: `main`
   - **Main file path**: `app.py`
5. Click **"Deploy"**

⏳ **Wait 2-3 minutes** while Streamlit builds and starts the app.

✅ **DONE!** Your app is now live! 🎉

---

## Troubleshooting

### "Model files not found" error
- Check that your HF repository ID in `utils.py` is spelled correctly
- Make sure all files were uploaded to Hugging Face

### "Connection timeout" error
- The first startup downloads ~800 MB of models (can take 2-5 min)
- This is normal — wait and refresh the page

### "Permission denied" on Hugging Face
- Make sure your repository is set to **Public** or you added a Hugging Face token to Streamlit secrets (advanced)

---

## That's it! 🚀

Your app will now:
1. ✅ Start on Streamlit Cloud
2. ✅ Download models from Hugging Face (cached after first load)
3. ✅ Run inference on phishing emails
4. ✅ Never push 800 MB to GitHub

**Questions?** Everything is already set up in the code — just follow the steps above!
