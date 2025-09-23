# 🔧 Dependency Setup Guide

This guide helps you ensure all dependencies are properly installed before running the Web Chatbot Pipeline.

## 🚀 Quick Setup (Recommended)

Run the automated setup script to install everything:

```bash
python setup.py
```

This will:
- ✅ Install all Python dependencies
- ✅ Install Playwright browsers
- ✅ Check environment variables
- ✅ Pre-load AI models
- ✅ Test Astra DB connection

## 🔍 Manual Dependency Check

To check if everything is ready without installing:

```bash
python check_dependencies.py
```

This will verify:
- ✅ Python packages are installed
- ✅ Playwright browsers are available
- ✅ Environment variables are set
- ✅ AI models can be loaded
- ✅ Astra DB connection works

## ⚡ Quick Start Pipeline

To run the pipeline with automatic dependency checking:

```bash
python quick_start.py <URL> <MAX_DEPTH> <MAX_PAGES>
```

Example:
```bash
python quick_start.py https://www.incede.ai 2 50
```

## 📋 Manual Setup Steps

If you prefer to set up manually:

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install Playwright Browsers
```bash
python -m playwright install chromium
```

### 3. Configure Environment Variables
Make sure your `.env` file contains all required variables:
- `IBM_API_KEY`
- `WATSONX_PROJECT_ID`
- `WATSONX_URL`
- `WATSONX_MODEL_ID`
- `ASTRA_COLLECTION_NAME`
- `ASTRA_KEYSPACE`
- `ASTRA_DEVOPS_TOKEN`
- `ASTRA_REGION`
- `ASTRA_CLOUD`
- `ASTRA_TIER`
- `ASTRA_DB_TYPE`
- `ASTRA_ORG_ID`
- `ASTRA_DB_API_ENDPOINT`
- `ASTRA_DB_APPLICATION_TOKEN`

### 4. Pre-load AI Models (Optional but Recommended)
```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-mpnet-base-v2')"
python -c "from sentence_transformers import CrossEncoder; CrossEncoder('cross-encoder/ms-marco-TinyBERT-L-2-v2')"
```

## 🎯 What Gets Pre-loaded

The dependency checker pre-loads these models to avoid download delays during pipeline execution:

1. **Sentence Transformer**: `sentence-transformers/all-mpnet-base-v2`
   - Used for generating embeddings
   - ~438MB download
   - Cached after first download

2. **Cross-Encoder**: `cross-encoder/ms-marco-TinyBERT-L-2-v2`
   - Used for re-ranking search results
   - ~17.6MB download
   - Cached after first download

## 🚨 Common Issues and Solutions

### Issue: "Address already in use"
**Solution**: Kill existing processes on port 8000
```bash
lsof -ti:8000 | xargs kill -9
```

### Issue: "Playwright executable not found"
**Solution**: Install Playwright browsers
```bash
python -m playwright install chromium
```

### Issue: "ImportError: cannot import name 'cached_download'"
**Solution**: This is fixed in the current requirements.txt with compatible versions

### Issue: "NumPy compatibility warnings"
**Solution**: The requirements.txt specifies `numpy<2.0` to avoid compatibility issues

### Issue: "Astra DB connection failed"
**Solution**: Check your `.env` file and ensure all Astra DB credentials are correct

## 🔄 Running the Pipeline

### Option 1: Direct Pipeline
```bash
python run_all.py <URL> <MAX_DEPTH> <MAX_PAGES>
```

### Option 2: Web Interface
```bash
# Terminal 1: Backend
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend
cd frontend && npm run dev
```

### Option 3: Quick Start (with dependency check)
```bash
python quick_start.py <URL> <MAX_DEPTH> <MAX_PAGES>
```

## 📊 Pipeline Steps

The pipeline runs these steps in order:
1. **Web Crawling** - Extract content using Playwright
2. **Page Type Detection** - Analyze content types
3. **Chunking Strategy** - Determine text processing approach
4. **Collection Setup** - Create Astra DB collection
5. **Vector Upload** - Generate embeddings and store in database
6. **Q&A Interface** - Launch chat interface

## 🎉 Success Indicators

You'll know everything is working when you see:
- ✅ All dependency checks pass
- ✅ Models load without download delays
- ✅ Astra DB connection succeeds
- ✅ Pipeline runs without import errors
- ✅ Web interface loads at http://localhost:5173

## 🆘 Getting Help

If you encounter issues:
1. Run `python check_dependencies.py` to diagnose problems
2. Check the error messages for specific missing components
3. Ensure your `.env` file is properly configured
4. Verify your internet connection for model downloads
5. Check that all required ports (8000, 5173) are available
