# 🤖 AI-Powered Web Chatbot with Knowledge Base Pipeline

A full-stack chatbot application that crawls websites, builds a knowledge base, and provides AI-powered responses using IBM watsonx and Astra DB.

## 🌟 Features

### Chat Interface
- **Real-time Chat**: Interactive chat interface with streaming responses
- **Source Attribution**: Shows sources for each answer
- **Vector Search**: Uses sentence transformers for semantic search
- **AI Responses**: Powered by IBM watsonx (Meta Llama 3.3 70B)

### Knowledge Base Pipeline (NEW!)
- **Web Crawling**: Automated website crawling with Playwright
- **Content Processing**: Intelligent content extraction and chunking
- **Real-time Monitoring**: Live progress tracking and logs
- **Pipeline Management**: Start, monitor, and manage crawling jobs from the UI

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
   git clone <your-repo>
   cd zulfi-web-chatbot
   
   # Create .env file with your credentials (see .env.example)
   ```

2. **Install dependencies:**
   ```bash
   # Backend
   pip install -r requirements.txt
   
   # Frontend
   cd frontend && npm install
   ```

3. **Start the application:**
   ```bash
   # Terminal 1: Backend
   python3 -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
   
   # Terminal 2: Frontend
   cd frontend && npm run dev
   ```

4. **Access the application:**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000/docs

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

## 📊 Using the Pipeline

### 1. Access the Knowledge Base Tab
- Open the application in your browser
- Click on the "Knowledge Base" tab

### 2. Configure Crawling Parameters
- **Website URL**: Enter the starting URL to crawl
- **Max Depth**: How deep to follow links (0-5)
- **Max Pages**: Maximum number of pages to crawl (1-1000)

### 3. Start the Pipeline
- Click "Start Pipeline"
- Monitor real-time progress and logs
- View completed pipelines in the history

### 4. Pipeline Steps
1. **Web Crawling**: Extract content from web pages
2. **Page Type Detection**: Classify content types
3. **Chunking Strategy**: Determine optimal text chunking
4. **Collection Creation**: Set up Astra DB collection
5. **Vector Upload**: Generate embeddings and store in database

## 🌐 AWS Deployment

### Quick Deployment
```bash
# Automated deployment script
./deploy.sh
```

### Manual Deployment

#### Backend (AWS App Runner)
1. Push code to Git repository
2. Go to AWS App Runner console
3. Create service using `apprunner.yaml`
4. All environment variables are pre-configured

#### Frontend (AWS Amplify)
1. Go to AWS Amplify console
2. Connect your Git repository
3. Amplify detects `amplify.yml` automatically
4. Update `VITE_API_BASE` with your App Runner URL

## 🔍 API Endpoints

### Chat Endpoints
- `POST /answer` - Ask a question
- `GET /docs` - API documentation

### Pipeline Endpoints (NEW!)
- `POST /pipeline/start` - Start a new crawling pipeline
- `GET /pipeline/status/{run_id}` - Get pipeline status
- `GET /pipeline/list` - List all pipeline runs
- `DELETE /pipeline/{run_id}` - Delete a pipeline run

## 🛠️ Development

### Project Structure
```
├── server.py              # FastAPI backend
├── frontend/              # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat.tsx   # Chat interface
│   │   │   └── Pipeline.tsx # Pipeline management
│   │   └── lib/
│   │       └── api.ts     # API client
├── crawl.py              # Web crawling logic
├── astra_db_manager.py   # Database management
├── run_all.py            # Original pipeline script
└── requirements.txt      # Python dependencies
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
   ```

2. **Playwright Browser Missing**
   ```bash
   playwright install chromium
   ```

3. **CORS Issues**
   - Update CORS origins in `server.py`
   - Check frontend API base URL

4. **Pipeline Failures**
   - Check pipeline logs in the UI
   - Verify website accessibility
   - Check Astra DB connectivity

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
