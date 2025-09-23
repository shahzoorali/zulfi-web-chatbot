@echo off
setlocal

echo ===============================
echo Setting up website-chatbot env (Python 3.11)
echo ===============================

REM Create virtual environment with Python 3.11
py -3.11 -m venv .venv
if errorlevel 1 (
  echo ❌ Failed to create venv. Make sure Python 3.11 is installed and on PATH.
  exit /b 1
)

REM Activate venv
call .venv\Scripts\activate

REM Upgrade pip
python -m pip install --upgrade pip wheel setuptools

REM Install requirements
pip install -r requirements.txt
if errorlevel 1 (
  echo ❌ Pip install failed.
  exit /b 1
)

REM Install Playwright browsers (needed for crawl.py/scrape_one.py)
python -m playwright install
if errorlevel 1 (
  echo ❌ Playwright browser install failed.
  exit /b 1
)

REM Quick sanity check
python - <<PY
import astrapy, requests, fastapi
from sentence_transformers import SentenceTransformer
print("✅ Setup complete, all imports working")
PY

echo.
echo To start using:
echo   call .venv\Scripts\activate
echo   uvicorn server:app --port 8080 --reload
echo.

endlocal