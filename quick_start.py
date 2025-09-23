#!/usr/bin/env python3
"""
Quick Start Script for the Web Chatbot Pipeline
Runs dependency check and then starts the pipeline with the provided URL.
"""

import sys
import subprocess
import time
from pathlib import Path

def run_dependency_check():
    """Run the dependency check."""
    print("🔍 Running dependency check...")
    try:
        result = subprocess.run([
            sys.executable, "check_dependencies.py"
        ], check=True)
        print("✅ Dependency check passed!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Dependency check failed!")
        return False

def run_pipeline(start_url, max_depth, max_pages):
    """Run the main pipeline."""
    print(f"\n🚀 Starting pipeline with:")
    print(f"   URL: {start_url}")
    print(f"   Max Depth: {max_depth}")
    print(f"   Max Pages: {max_pages}")
    
    try:
        result = subprocess.run([
            sys.executable, "run_all.py", start_url, str(max_depth), str(max_pages)
        ], check=True)
        print("✅ Pipeline completed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Pipeline failed!")
        return False

def main():
    """Main function."""
    if len(sys.argv) < 4:
        print("Usage: python quick_start.py <START_URL> <MAX_DEPTH> <MAX_PAGES>")
        print("\nExample:")
        print("  python quick_start.py https://www.incede.ai 2 50")
        sys.exit(1)
    
    start_url = sys.argv[1]
    max_depth = int(sys.argv[2])
    max_pages = int(sys.argv[3])
    
    print("🚀 Web Chatbot Pipeline - Quick Start")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("run_all.py").exists():
        print("❌ run_all.py not found! Please run this script from the project root directory.")
        sys.exit(1)
    
    # Run dependency check
    if not run_dependency_check():
        print("\n❌ Dependencies are not ready. Please run setup first:")
        print("   python setup.py")
        sys.exit(1)
    
    # Run the pipeline
    if not run_pipeline(start_url, max_depth, max_pages):
        sys.exit(1)
    
    print("\n🎉 Pipeline completed successfully!")

if __name__ == "__main__":
    main()
