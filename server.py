import os
import sys
import time
import asyncio
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from astrapy import DataAPIClient

# Load env (only for IBM Watson and optional settings)
load_dotenv()

# IBM Watson configuration (required for chat functionality)
IBM_API_KEY = os.getenv("IBM_API_KEY")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID")
WATSONX_URL = os.getenv("WATSONX_URL")
MODEL_ID = os.getenv("WATSONX_MODEL_ID")

# Optional settings
API_KEY = os.getenv("API_KEY", "")  # optional auth key

# Astra DB configuration will be set dynamically per pipeline
# No hardcoded values loaded at startup

# ─────────────────────────────────────────────
# Astra + embeddings (will be initialized dynamically)
# ─────────────────────────────────────────────
client = None
db = None
collection = None

def get_astra_connection():
    """Get or create Astra DB connection using current environment variables."""
    global client, db, collection
    
    # Check if Astra DB is configured
    astra_token = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
    astra_endpoint = os.getenv("ASTRA_DB_API_ENDPOINT")
    
    if not astra_token or not astra_endpoint:
        raise HTTPException(
            status_code=400, 
            detail="Astra DB not configured. Please run a pipeline first to set up the database connection."
        )
    
    if not client or not db or not collection:
        client = DataAPIClient(astra_token)
        db = client.get_database_by_api_endpoint(astra_endpoint)
        collection = db.get_collection(os.getenv("ASTRA_COLLECTION_NAME", "chatbot_chunks"))
    return client, db, collection

# ─────────────────────────────────────────────
# FastAPI app
# ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Website Chatbot API...")
    load_pipeline_history()
    yield
    # Shutdown
    print("💾 Saving pipeline history...")
    save_pipeline_history()
    print("👋 Shutting down Website Chatbot API...")

app = FastAPI(title="Website Chatbot API", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,  # Set to False when using allow_origins=["*"]
    allow_methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
    allow_headers=["*"]
)

# ─────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────

class AnswerRequest(BaseModel):
    query: str
    run_id: Optional[str] = None

class PipelineRequest(BaseModel):
    start_url: str
    max_depth: int = 2
    max_pages: int = 50

class PipelineStatus(BaseModel):
    run_id: str
    status: str  # "running", "completed", "failed"
    progress: Dict[str, Any]
    logs: list[str]
    start_time: Optional[str] = None
    end_time: Optional[str] = None

# Global pipeline status tracking
pipeline_status: Dict[str, PipelineStatus] = {}

# Pipeline history file path
PIPELINE_HISTORY_FILE = "pipeline_history.json"

def save_pipeline_history():
    """Save pipeline status to disk."""
    try:
        # Convert PipelineStatus objects to dictionaries
        history_data = {}
        for run_id, status in pipeline_status.items():
            history_data[run_id] = {
                "run_id": status.run_id,
                "status": status.status,
                "progress": status.progress,
                "logs": status.logs,
                "start_time": status.start_time,
                "end_time": status.end_time
            }
        
        with open(PIPELINE_HISTORY_FILE, 'w') as f:
            json.dump(history_data, f, indent=2)
        print(f"✅ Pipeline history saved to {PIPELINE_HISTORY_FILE}")
    except Exception as e:
        print(f"❌ Error saving pipeline history: {e}")

def load_pipeline_history():
    """Load pipeline status from disk."""
    global pipeline_status
    try:
        if os.path.exists(PIPELINE_HISTORY_FILE):
            with open(PIPELINE_HISTORY_FILE, 'r') as f:
                history_data = json.load(f)
            
            # Convert dictionaries back to PipelineStatus objects
            for run_id, data in history_data.items():
                pipeline_status[run_id] = PipelineStatus(
                    run_id=data["run_id"],
                    status=data["status"],
                    progress=data["progress"],
                    logs=data["logs"],
                    start_time=data.get("start_time"),
                    end_time=data.get("end_time")
                )
            print(f"✅ Pipeline history loaded from {PIPELINE_HISTORY_FILE} ({len(pipeline_status)} runs)")
        else:
            print(f"📝 No existing pipeline history found at {PIPELINE_HISTORY_FILE}")
    except Exception as e:
        print(f"❌ Error loading pipeline history: {e}")
        pipeline_status = {}

# ─────────────────────────────────────────────
# Pipeline Management
# ─────────────────────────────────────────────

async def run_pipeline_background(run_id: str, start_url: str, max_depth: int, max_pages: int):
    """Run the pipeline in the background and update status."""
    try:
        pipeline_status[run_id] = PipelineStatus(
            run_id=run_id,
            status="running",
            progress={"step": "starting", "current_step": 0, "total_steps": 3},
            logs=["Pipeline started"],
            start_time=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        save_pipeline_history()  # Save initial status
        
        # Add initial setup information (like run_all.py does)
        from urllib.parse import urlparse
        parsed_url = urlparse(start_url)
        site_name = parsed_url.netloc or start_url
        os.environ["SITE_NAME"] = site_name
        
        pipeline_status[run_id].logs.append(f"🚀 Starting pipeline | run_id: {run_id}")
        pipeline_status[run_id].logs.append(f"📂 Output dir: data/{run_id}")
        pipeline_status[run_id].logs.append(f"🌐 SITE_NAME set to: {site_name}")
        pipeline_status[run_id].logs.append(f"🔗 START_URL: {start_url}")
        pipeline_status[run_id].logs.append(f"🧭 MAX_DEPTH:  {max_depth}")
        pipeline_status[run_id].logs.append(f"📄 MAX_PAGES:  {max_pages}")
        
        # Ensure Astra DB is set up for this URL
        pipeline_status[run_id].logs.append("Setting up Astra DB...")
        pipeline_status[run_id].progress = {
            "step": "Setting up Astra DB",
            "current_step": 1,
            "total_steps": 3
        }
        
        # Import and run ensure_db with output capture
        from astra_db_manager import ensure_db
        import io
        import contextlib
        
        # Capture print output from ensure_db
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            ensure_db(start_url)
        
        # Add captured output to logs
        captured_output = f.getvalue().strip()
        if captured_output:
            for line in captured_output.split('\n'):
                if line.strip():
                    pipeline_status[run_id].logs.append(line.strip())
        
        pipeline_status[run_id].logs.append("Astra DB setup completed")
        pipeline_status[run_id].logs.append(f"Environment variables set: ASTRA_DB_API_ENDPOINT={os.getenv('ASTRA_DB_API_ENDPOINT', 'NOT_SET')[:50]}...")
        
        # Refresh the global Astra connection with new environment variables
        global client, db, collection
        client = None
        db = None
        collection = None
        get_astra_connection()  # Initialize with new environment variables
        
        # Run run_all.py directly with the parameters (exactly like terminal)
        pipeline_status[run_id].progress = {
            "step": "Running Pipeline",
            "current_step": 2,
            "total_steps": 3
        }
        
        # Run run_all.py with the exact same command as terminal
        cmd = [sys.executable, "run_all.py", start_url, str(max_depth), str(max_pages)]
        pipeline_status[run_id].logs.append(f"=== Running: {' '.join(cmd)} ===")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=Path.cwd(),
            env=os.environ.copy()  # Pass current environment variables
        )
        
        # Stream output in real-time
        output_lines = []
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            
            # Decode and add to logs
            line_text = line.decode().strip()
            if line_text:  # Only add non-empty lines
                pipeline_status[run_id].logs.append(line_text)
                output_lines.append(line_text)
        
        # Wait for process to complete
        await process.wait()
        
        if process.returncode != 0:
            error_msg = f"Error in run_all.py (exit code: {process.returncode})"
            pipeline_status[run_id].logs.append(error_msg)
            pipeline_status[run_id].status = "failed"
            pipeline_status[run_id].end_time = time.strftime("%Y-%m-%d %H:%M:%S")
            return
        
        pipeline_status[run_id].logs.append("✅ Pipeline completed successfully")
        
        pipeline_status[run_id].status = "completed"
        pipeline_status[run_id].progress = {
            "step": "completed",
            "current_step": 3,
            "total_steps": 3
        }
        pipeline_status[run_id].logs.append(f"\n✅ Done | run_id: {run_id} | Stored in: data/{run_id}")
        pipeline_status[run_id].end_time = time.strftime("%Y-%m-%d %H:%M:%S")
        save_pipeline_history()  # Save final status
        
    except Exception as e:
        pipeline_status[run_id].status = "failed"
        pipeline_status[run_id].logs.append(f"Pipeline failed with error: {str(e)}")
        pipeline_status[run_id].end_time = time.strftime("%Y-%m-%d %H:%M:%S")
        save_pipeline_history()  # Save error status

# ─────────────────────────────────────────────
# API Endpoints
# ─────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "Website Chatbot API", "status": "running"}

@app.get("/status")
def get_status():
    """Get server and Astra DB status."""
    try:
        # Check if Astra DB is configured
        astra_token = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
        astra_endpoint = os.getenv("ASTRA_DB_API_ENDPOINT")
        astra_configured = bool(astra_token and astra_endpoint)
        
        # Check Watson configuration
        watson_configured = bool(IBM_API_KEY and WATSONX_PROJECT_ID and WATSONX_URL and MODEL_ID)
        
        # Try to get Astra connection status
        astra_connection = "not_configured"
        collections = []
        collection_name = os.getenv("ASTRA_COLLECTION_NAME", "chatbot_chunks")
        
        if astra_configured:
            try:
                client, db, collection = get_astra_connection()
                astra_connection = "active"
                collections = [c["name"] for c in db.list_collections()]
            except Exception as e:
                astra_connection = f"error: {str(e)}"
        
        return {
            "server": "running",
            "astra_db_configured": astra_configured,
            "watson_configured": watson_configured,
            "astra_endpoint": astra_endpoint or "not_set",
            "collection_name": collection_name,
            "astra_connection": astra_connection,
            "collections": collections
        }
    except Exception as e:
        return {
            "server": "running",
            "astra_db_configured": False,
            "watson_configured": False,
            "astra_endpoint": "error",
            "collection_name": "error",
            "astra_connection": f"error: {str(e)}",
            "collections": []
        }

@app.post("/pipeline/start")
async def start_pipeline(req: PipelineRequest, background_tasks: BackgroundTasks, x_api_key: Optional[str] = Header(default=None)):
    """Start a new pipeline run."""
    # optional auth
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Generate run_id
    run_id = time.strftime("%Y%m%d_%H%M%S")
    
    # Start pipeline in background
    background_tasks.add_task(run_pipeline_background, run_id, req.start_url, req.max_depth, req.max_pages)
    
    return {
        "run_id": run_id,
        "message": f"Pipeline started with run_id: {run_id}",
        "status": "started"
    }

@app.get("/pipeline/status/{run_id}")
def get_pipeline_status(run_id: str, x_api_key: Optional[str] = Header(default=None)):
    """Get the status of a specific pipeline run."""
    # optional auth
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if run_id not in pipeline_status:
        return PipelineStatus(
            run_id=run_id,
            status="not_found",
            progress={"step": "not_found", "current_step": 0, "total_steps": 0},
            logs=["Pipeline not found"]
        )
    
    return pipeline_status[run_id]

@app.get("/pipeline/list")
def list_pipelines(x_api_key: Optional[str] = Header(default=None)):
    """List all pipeline runs."""
    # optional auth
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Get run_ids from both pipeline_status and from logs (in case some are missing)
    run_ids = set(pipeline_status.keys())
    
    # Also extract run_ids from logs
    for status in pipeline_status.values():
        for log in status.logs:
            if "run_id=" in log:
                # Extract run_id from log entries like "run_id=20250923_194738"
                parts = log.split("run_id=")
                if len(parts) > 1:
                    extracted_run_id = parts[1].split()[0]  # Get the first word after run_id=
                    run_ids.add(extracted_run_id)
    
    return {"pipelines": sorted(list(run_ids), reverse=True)}

@app.delete("/pipeline/{run_id}")
def delete_pipeline(run_id: str, x_api_key: Optional[str] = Header(default=None)):
    """Delete a pipeline run and its associated data."""
    # optional auth
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if run_id in pipeline_status:
        del pipeline_status[run_id]
        save_pipeline_history()  # Save after deletion
    
    # Also try to delete the data directory
    data_dir = Path(f"data/{run_id}")
    if data_dir.exists():
        import shutil
        shutil.rmtree(data_dir)
    
    return {"message": f"Pipeline {run_id} deleted"}

@app.post("/answer")
def answer(req: AnswerRequest, x_api_key: Optional[str] = Header(default=None)):
    # optional auth
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Use the same logic as query_astra_llm.py
    try:
        # Set environment variables for the specific run_id if provided
        if req.run_id:
            os.environ["RUN_ID"] = req.run_id
            # Set up the Astra DB environment variables for this run
            # Use the current server's Astra DB configuration
            if os.getenv("ASTRA_DB_API_ENDPOINT"):
                os.environ["ASTRA_DB_API_ENDPOINT"] = os.getenv("ASTRA_DB_API_ENDPOINT")
            if os.getenv("ASTRA_DB_APPLICATION_TOKEN"):
                os.environ["ASTRA_DB_APPLICATION_TOKEN"] = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
            # Set SITE_NAME based on run_id (extract from run_id or use default)
            if not os.getenv("SITE_NAME"):
                os.environ["SITE_NAME"] = "hprc.in"  # Default for now
        
        # Import the retrieve_and_answer function from query_astra_llm
        import sys
        sys.path.append('.')
        from query_astra_llm import retrieve_and_answer
        
        # Call the same function that the terminal uses
        result = retrieve_and_answer(req.query)
        
        # Format sources for frontend
        sources = []
        for doc in result.get("sources", []):
            sources.append({
                "url": doc.get("url"),
                "title": doc.get("title"),
                "score": doc.get("$similarity", 0)
            })
        
        return {"answer": result.get("answer", "No answer available"), "sources": sources}
        
    except Exception as e:
        return {"answer": f"Error processing query: {str(e)}", "sources": []}

@app.post("/chat/test")
def test_chatbot(req: AnswerRequest, x_api_key: Optional[str] = Header(default=None)):
    """Test the chatbot with a sample query (like the terminal 'Ask:' prompt)."""
    # optional auth
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Use the same logic as query_astra_llm.py
    try:
        # Set environment variables for the specific run_id if provided
        if req.run_id:
            os.environ["RUN_ID"] = req.run_id
            # Set up the Astra DB environment variables for this run
            # Use the current server's Astra DB configuration
            if os.getenv("ASTRA_DB_API_ENDPOINT"):
                os.environ["ASTRA_DB_API_ENDPOINT"] = os.getenv("ASTRA_DB_API_ENDPOINT")
            if os.getenv("ASTRA_DB_APPLICATION_TOKEN"):
                os.environ["ASTRA_DB_APPLICATION_TOKEN"] = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
            # Set SITE_NAME based on run_id (extract from run_id or use default)
            if not os.getenv("SITE_NAME"):
                os.environ["SITE_NAME"] = "hprc.in"  # Default for now
        
        # Import the retrieve_and_answer function from query_astra_llm
        import sys
        sys.path.append('.')
        from query_astra_llm import retrieve_and_answer
        
        # Call the same function that the terminal uses
        result = retrieve_and_answer(req.query)
        
        # Format sources for frontend
        sources = []
        for doc in result.get("sources", []):
            sources.append({
                "url": doc.get("url"),
                "title": doc.get("title"),
                "score": doc.get("$similarity", 0)
            })
        
        return {"answer": result.get("answer", "No answer available"), "sources": sources}
        
    except Exception as e:
        return {"answer": f"Error processing query: {str(e)}", "sources": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
