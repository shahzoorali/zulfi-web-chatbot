#!/usr/bin/env python3
"""
Setup script for the Web Chatbot Pipeline
Installs all dependencies and pre-loads models to ensure smooth pipeline execution.
"""

import sys
import subprocess
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n🔄 {description}...")
    print(f"   Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"   ✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ {description} failed:")
        print(f"   Error: {e.stderr}")
        return False
    except Exception as e:
        print(f"   ❌ {description} failed with exception: {e}")
        return False

def install_python_dependencies():
    """Install Python dependencies from requirements.txt."""
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt not found!")
        return False
    
    return run_command([
        sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
    ], "Installing Python dependencies")

def install_playwright_browsers():
    """Install Playwright browsers."""
    return run_command([
        sys.executable, "-m", "playwright", "install", "chromium"
    ], "Installing Playwright browsers")

def check_env_file():
    """Check if .env file exists and is properly configured."""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found!")
        print("Please create a .env file with your configuration.")
        return False
    
    print("✅ .env file found")
    return True

def run_dependency_check():
    """Run the comprehensive dependency check."""
    return run_command([
        sys.executable, "check_dependencies.py"
    ], "Running dependency check")

def main():
    """Main setup function."""
    print("🚀 Web Chatbot Pipeline - Setup Script")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("run_all.py").exists():
        print("❌ run_all.py not found! Please run this script from the project root directory.")
        sys.exit(1)
    
    success = True
    
    # Step 1: Install Python dependencies
    if not install_python_dependencies():
        success = False
    
    # Step 2: Install Playwright browsers
    if not install_playwright_browsers():
        success = False
    
    # Step 3: Check .env file
    if not check_env_file():
        success = False
    
    # Step 4: Run comprehensive dependency check
    if success and not run_dependency_check():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Setup completed successfully!")
        print("\nYour environment is ready to run the pipeline.")
        print("\nNext steps:")
        print("1. Start the backend server:")
        print("   python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload")
        print("\n2. Start the frontend (in another terminal):")
        print("   cd frontend && npm run dev")
        print("\n3. Or run the pipeline directly:")
        print("   python run_all.py <URL> <MAX_DEPTH> <MAX_PAGES>")
    else:
        print("❌ Setup failed. Please check the errors above and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()
