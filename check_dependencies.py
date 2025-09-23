#!/usr/bin/env python3
"""
Dependency Checker and Pre-installer for the Web Chatbot Pipeline
Ensures all required models and dependencies are installed before running the pipeline.
"""

import sys
import subprocess
import os
import importlib
from pathlib import Path
import time

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, continue without it

def check_python_packages():
    """Check if all required Python packages are installed."""
    required_packages = [
        'astrapy',
        'sentence_transformers',
        'huggingface_hub',
        'python-dotenv',
        'requests',
        'beautifulsoup4',
        'lxml',
        'playwright',
        'fastapi',
        'uvicorn',
        'numpy',
        'torch',
        'transformers'
    ]
    
    missing_packages = []
    
    print("🔍 Checking Python packages...")
    for package in required_packages:
        try:
            # Handle package name variations
            import_name = package.replace('-', '_')
            if package == 'python-dotenv':
                import_name = 'dotenv'
            elif package == 'beautifulsoup4':
                import_name = 'bs4'
            
            importlib.import_module(import_name)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("✅ All Python packages are installed!")
    return True

def check_playwright_browsers():
    """Check if Playwright browsers are installed."""
    print("\n🔍 Checking Playwright browsers...")
    try:
        result = subprocess.run([
            sys.executable, '-m', 'playwright', 'install', '--dry-run'
        ], capture_output=True, text=True)
        
        if "chromium" in result.stdout and "already installed" in result.stdout:
            print("  ✅ Chromium browser is installed")
            return True
        else:
            print("  ❌ Chromium browser is missing")
            return False
    except Exception as e:
        print(f"  ❌ Error checking Playwright: {e}")
        return False

def install_playwright_browsers():
    """Install Playwright browsers."""
    print("\n📦 Installing Playwright browsers...")
    try:
        result = subprocess.run([
            sys.executable, '-m', 'playwright', 'install', 'chromium'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("  ✅ Playwright browsers installed successfully")
            return True
        else:
            print(f"  ❌ Failed to install Playwright browsers: {result.stderr}")
            return False
    except Exception as e:
        print(f"  ❌ Error installing Playwright: {e}")
        return False

def preload_sentence_transformer():
    """Pre-load the sentence transformer model to avoid download delays."""
    print("\n🤖 Pre-loading sentence transformer model...")
    try:
        from sentence_transformers import SentenceTransformer
        
        # Load the model (this will download if not cached)
        model_name = os.getenv('EMBED_MODEL', 'sentence-transformers/all-mpnet-base-v2')
        print(f"  📥 Loading model: {model_name}")
        
        start_time = time.time()
        model = SentenceTransformer(model_name)
        load_time = time.time() - start_time
        
        print(f"  ✅ Model loaded successfully in {load_time:.2f} seconds")
        
        # Test the model with a sample text
        test_text = "This is a test sentence for embedding."
        embedding = model.encode([test_text])
        print(f"  ✅ Model test successful - embedding shape: {embedding.shape}")
        
        return True
    except Exception as e:
        print(f"  ❌ Error loading sentence transformer: {e}")
        return False

def preload_cross_encoder():
    """Pre-load the cross-encoder model for re-ranking."""
    print("\n🎯 Pre-loading cross-encoder model...")
    try:
        from sentence_transformers import CrossEncoder
        
        model_name = "cross-encoder/ms-marco-TinyBERT-L-2-v2"
        print(f"  📥 Loading model: {model_name}")
        
        start_time = time.time()
        model = CrossEncoder(model_name)
        load_time = time.time() - start_time
        
        print(f"  ✅ Cross-encoder loaded successfully in {load_time:.2f} seconds")
        
        # Test the model
        test_pairs = [("This is a test query", "This is a test document")]
        scores = model.predict(test_pairs)
        print(f"  ✅ Cross-encoder test successful - scores: {scores}")
        
        return True
    except Exception as e:
        print(f"  ❌ Error loading cross-encoder: {e}")
        return False

def check_environment_variables():
    """Check if required environment variables are set."""
    print("\n🔧 Checking environment variables...")
    
    required_vars = [
        'IBM_API_KEY',
        'WATSONX_PROJECT_ID',
        'WATSONX_URL',
        'WATSONX_MODEL_ID',
        'ASTRA_COLLECTION_NAME',
        'ASTRA_KEYSPACE',
        'ASTRA_DEVOPS_TOKEN',
        'ASTRA_REGION',
        'ASTRA_CLOUD',
        'ASTRA_TIER',
        'ASTRA_DB_TYPE',
        'ASTRA_ORG_ID',
        'ASTRA_DB_API_ENDPOINT',
        'ASTRA_DB_APPLICATION_TOKEN'
    ]
    
    missing_vars = []
    
    for var in required_vars:
        if os.getenv(var):
            print(f"  ✅ {var}")
        else:
            print(f"  ❌ {var} - MISSING")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("Make sure your .env file is properly configured")
        return False
    
    print("✅ All environment variables are set!")
    return True

def check_astra_connection():
    """Test Astra DB connection."""
    print("\n🗄️  Testing Astra DB connection...")
    try:
        from astra_db_manager import ensure_db
        
        # Test with a dummy URL
        test_url = "https://example.com"
        ensure_db(test_url)
        
        print("  ✅ Astra DB connection successful")
        return True
    except Exception as e:
        print(f"  ❌ Astra DB connection failed: {e}")
        return False

def main():
    """Main dependency check function."""
    print("🚀 Web Chatbot Pipeline - Dependency Checker")
    print("=" * 50)
    
    all_checks_passed = True
    
    # Check Python packages
    if not check_python_packages():
        all_checks_passed = False
    
    # Check Playwright browsers
    if not check_playwright_browsers():
        print("\n📦 Installing Playwright browsers...")
        if not install_playwright_browsers():
            all_checks_passed = False
    
    # Check environment variables
    if not check_environment_variables():
        all_checks_passed = False
    
    # Pre-load models (only if other checks pass)
    if all_checks_passed:
        if not preload_sentence_transformer():
            all_checks_passed = False
        
        if not preload_cross_encoder():
            all_checks_passed = False
        
        # Test Astra connection
        if not check_astra_connection():
            all_checks_passed = False
    
    print("\n" + "=" * 50)
    if all_checks_passed:
        print("🎉 All dependencies are ready! You can now run the pipeline.")
        print("\nTo start the pipeline:")
        print("  python run_all.py <URL> <MAX_DEPTH> <MAX_PAGES>")
        print("\nTo start the web interface:")
        print("  # Terminal 1: python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload")
        print("  # Terminal 2: cd frontend && npm run dev")
    else:
        print("❌ Some dependencies are missing. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
