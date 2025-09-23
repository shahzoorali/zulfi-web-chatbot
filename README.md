# 🤖 AI-Powered Web Chatbot with Knowledge Base Pipeline

A full-stack chatbot application that crawls websites, builds a knowledge base, and provides AI-powered responses using IBM watsonx and Astra DB. Features session-based chat that binds to specific pipeline runs for isolated knowledge bases.

## 🌟 Features

### Chat Interface
- **Session-Based Chat**: Each pipeline run has its own isolated chat context
- **Run Selection**: Choose which pipeline's data to chat with via dropdown
- **Real-time Chat**: Interactive chat interface with streaming responses
- **Source Attribution**: Shows sources for each answer with similarity scores
- **Vector Search**: Uses sentence transformers for semantic search
- **AI Responses**: Powered by IBM watsonx (Meta Llama 3.3 70B)

### Knowledge Base Pipeline
- **Direct Script Execution**: Frontend runs `run_all.py` exactly like terminal
- **Web Crawling**: Automated website crawling with Playwright
- **Content Processing**: Intelligent content extraction and chunking
- **Real-time Monitoring**: Live progress tracking with exact terminal output
- **Pipeline Management**: Start, monitor, and manage crawling jobs from the UI
- **Dynamic DB Setup**: Automatically configures Astra DB per URL
- **Test Chatbot**: Built-in testing interface after pipeline completion

## 🏗️ Architecture

```
Frontend (React + Vite)
    ↓
Backend (FastAPI)
    ↓
┌─────────────────┬─────────────────┐
│   Chat System   │   Pipeline      │
│                 │                 │
│ • Vector Search │ • Web Crawling  │
│ • AI Responses  │ • Content Proc. │
│ • Source Attr.  │ • Progress Mon. │
└─────────────────┴─────────────────┘
    ↓                    ↓
Astra DB            IBM watsonx
(Vector Store)      (LLM Service)
```

## 🚀 Quick Start

### Local Development

1. **Clone and setup environment:**
   ```bash
   git clone https://github.com/shahzoorali/zulfi-web-chatbot.git
   cd zulfi-web-chatbot
   
   # Create .env file with your credentials (see Configuration section)
   ```

2. **Install dependencies:**
   ```bash
   # Backend dependencies
   pip install -r requirements.txt
   
   # Install Playwright browsers
   playwright install chromium
   
   # Frontend dependencies
   cd frontend && npm install
   ```

3. **Start the application:**
   ```bash
   # Terminal 1: Backend (with auto-reload)
   python3 -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
   
   # Terminal 2: Frontend (with hot reload)
   cd frontend && npm run dev
   ```

4. **Access the application:**
   - **Frontend**: http://localhost:5173
   - **Backend API**: http://localhost:8000/docs
   - **API Status**: http://localhost:8000/status

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# IBM watsonx Configuration
IBM_API_KEY=your_ibm_api_key
WATSONX_PROJECT_ID=your_project_id
WATSONX_URL=https://ca-tor.ml.cloud.ibm.com
WATSONX_MODEL_ID=meta-llama/llama-3-3-70b-instruct

# Astra DB Configuration
ASTRA_DB_API_ENDPOINT=your_astra_endpoint
ASTRA_DB_APPLICATION_TOKEN=your_app_token
ASTRA_DEVOPS_TOKEN=your_devops_token
ASTRA_ORG_ID=your_org_id
ASTRA_COLLECTION_NAME=chatbot_chunks
ASTRA_KEYSPACE=default_keyspace

# Optional
API_KEY=your_optional_api_key
```

### Frontend Environment Variables

Create `frontend/.env`:

```env
VITE_API_BASE=http://localhost:8000
VITE_API_KEY=
VITE_DEFAULT_RUN_ID=
VITE_TOP_K=3
```

## 📊 Using the Application

### 1. Knowledge Base Pipeline
- Open the application at http://localhost:5173
- Click on the "Knowledge Base" tab
- Configure crawling parameters:
  - **Website URL**: Enter the starting URL to crawl (e.g., `https://hprc.in`)
  - **Max Depth**: How deep to follow links (0-5)
  - **Max Pages**: Maximum number of pages to crawl (1-1000)
- Click "Start Pipeline" to begin crawling
- Monitor real-time progress and logs (exactly like terminal output)
- View completed pipelines in the history

### 2. Chat Interface
- Click on the "Chat" tab
- Select a pipeline run from the dropdown (e.g., `20250923_192312`)
- Ask questions about the crawled data:
  - "What is HPRC?"
  - "What services does HPRC offer?"
  - "Tell me about polo at HPRC"
- Each pipeline run has its own isolated chat context

### 3. Test Chatbot (After Pipeline Completion)
- After a pipeline completes, use the "Test Chatbot" section
- Enter test queries to verify your knowledge base
- See answers with source attribution and similarity scores

### 4. Pipeline Steps (Automated)
1. **Initialization**: Set up pipeline environment and parameters
2. **Astra DB Setup**: Configure and connect to Astra database
3. **Pipeline Execution**: Run `run_all.py` with your parameters
   - Web crawling with Playwright
   - Content extraction and processing
   - Vector embedding generation
   - Database storage

## 🌐 AWS Deployment

### Prerequisites
- AWS CLI configured with appropriate permissions
- Docker installed
- Environment variables set (see Configuration section)

### Quick Deployment
```bash
# Make deployment script executable
chmod +x deploy.sh

# Set required environment variables
export IBM_API_KEY="your_ibm_api_key"
export WATSONX_PROJECT_ID="your_project_id"
export ASTRA_DEVOPS_TOKEN="your_devops_token"
export ASTRA_DB_APPLICATION_TOKEN="your_app_token"

# Run automated deployment
./deploy.sh
```

### Manual Deployment

#### Backend (AWS App Runner)
1. Push code to Git repository
2. Go to AWS App Runner console
3. Create service using `apprunner.yaml`
4. Set environment variables in App Runner service
5. Service will automatically build and deploy

#### Frontend (AWS Amplify)
1. Go to AWS Amplify console
2. Connect your Git repository
3. Amplify detects `amplify.yml` automatically
4. Update `VITE_API_BASE` with your App Runner URL
5. Deploy and get your frontend URL

### Deployment Files
- `apprunner.yaml` - AWS App Runner configuration
- `amplify.yml` - AWS Amplify build configuration
- `Dockerfile` - Container configuration for backend
- `deploy.sh` - Automated deployment script

## 🔍 API Endpoints

### Chat Endpoints
- `POST /answer` - Ask a question (with run_id for session binding)
- `POST /chat/test` - Test chatbot with sample query
- `GET /docs` - Interactive API documentation (Swagger UI)

### Pipeline Endpoints
- `POST /pipeline/start` - Start a new crawling pipeline
- `GET /pipeline/status/{run_id}` - Get real-time pipeline status
- `GET /pipeline/list` - List all pipeline runs
- `DELETE /pipeline/{run_id}` - Delete a pipeline run and its data

### System Endpoints
- `GET /status` - Get server and database configuration status

## 🛠️ Development

### Project Structure
```
├── server.py                    # FastAPI backend with pipeline management
├── frontend/                    # React + TypeScript frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat.tsx         # Session-based chat interface
│   │   │   └── Pipeline.tsx     # Pipeline management with real-time logs
│   │   ├── lib/
│   │   │   └── api.ts           # API client with all endpoints
│   │   └── App.tsx              # Main app with tab navigation
│   ├── amplify.yml              # AWS Amplify configuration
│   └── package.json             # Frontend dependencies
├── crawl.py                     # Web crawling logic
├── astra_db_manager.py          # Dynamic database management
├── query_astra_llm.py           # RAG chatbot logic
├── run_all.py                   # Main pipeline script
├── apprunner.yaml               # AWS App Runner configuration
├── deploy.sh                    # Automated deployment script
├── Dockerfile                   # Container configuration
├── requirements.txt             # Python dependencies
└── .gitignore                   # Git ignore rules
```

### Key Technologies
- **Frontend**: React, TypeScript, Vite
- **Backend**: FastAPI, Python 3.11
- **Database**: Astra DB (Cassandra)
- **AI/ML**: IBM watsonx, sentence-transformers
- **Web Crawling**: Playwright, BeautifulSoup
- **Deployment**: AWS App Runner, AWS Amplify

## 📈 Monitoring

### Application Logs
- **App Runner**: CloudWatch logs
- **Amplify**: Build logs in console
- **Pipeline**: Real-time logs in UI

### Performance Metrics
- **Response Times**: API endpoint performance
- **Crawling Stats**: Pages processed, errors, duration
- **Vector Search**: Similarity scores, retrieval accuracy

## 🔐 Security

- **Environment Variables**: Stored securely in AWS
- **CORS**: Configured for production domains
- **API Authentication**: Optional API key support
- **Input Validation**: Request validation with Pydantic

## 🆘 Troubleshooting

### Common Issues

1. **NumPy Compatibility Error**
   ```bash
   pip install "numpy<2.0" --force-reinstall
   pip install "sentence-transformers==2.2.2" --force-reinstall
   pip install "huggingface-hub==0.16.4" --force-reinstall
   ```

2. **Playwright Browser Missing**
   ```bash
   playwright install chromium
   ```

3. **CORS Issues**
   - Update CORS origins in `server.py`
   - Check frontend API base URL in `frontend/.env`

4. **Pipeline Failures**
   - Check pipeline logs in the UI (real-time output)
   - Verify website accessibility
   - Check Astra DB connectivity and status
   - Ensure environment variables are set correctly

5. **Chat Not Working**
   - Make sure you've run a pipeline first
   - Select the correct pipeline run from dropdown
   - Check that Astra DB is configured for that run

6. **"No results in Astra DB" Error**
   - Verify the pipeline completed successfully
   - Check that the selected run_id matches your pipeline
   - Ensure Astra DB is not hibernated

## 🆕 Latest Features

### Session-Based Chat System
- **Isolated Contexts**: Each pipeline run has its own chat session
- **Run Selection**: Dropdown to choose which pipeline's data to chat with
- **Dynamic Binding**: Chat automatically binds to the selected pipeline's data
- **No Cross-Contamination**: Chat for run A won't see data from run B

### Real-Time Pipeline Execution
- **Direct Script Execution**: Frontend runs `run_all.py` exactly like terminal
- **Live Output Streaming**: See exact terminal output in the UI
- **Progress Tracking**: Real-time status updates and step progression
- **Verbose Mode**: Detailed logs with timestamps and step descriptions

### Enhanced User Experience
- **Tab Navigation**: Switch between Chat and Knowledge Base tabs
- **Server Status**: Monitor Astra DB and Watson AI configuration
- **Test Chatbot**: Built-in testing interface after pipeline completion
- **Pipeline History**: View and manage all past pipeline runs

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the troubleshooting section
- Review API documentation at `/docs`
- Check pipeline logs for crawling issues
- Verify environment variables are set correctly
