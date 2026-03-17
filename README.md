# Glaze - Semantic Search for Google Drive

Glaze is a full-stack application that enables semantic search over Google Drive files using AI-powered embeddings. Search your Drive files using natural language queries instead of keyword matching.

## Features

- Google OAuth 2.0 authentication
- Automatic indexing of Google Drive files (PDF, DOCX, TXT, PPT)
- AI-powered embeddings using Google Gemini
- Semantic search with natural language queries
- Fast vector similarity search with Qdrant
- Clean Chrome Extension UI
- Incremental indexing (only processes new/modified files)

## Architecture

- **Backend**: FastAPI (Python)
- **Vector Database**: Qdrant (Docker)
- **Metadata Database**: SQLite
- **AI Model**: Google Gemini Embedding (multimodal-embedding-002)
- **Frontend**: Chrome Extension (Vanilla JS + Tailwind CSS)

## Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Google Cloud Project with Drive API enabled
- Google Gemini API key
- Chrome browser

## Setup Instructions

### 1. Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Drive API
4. Create OAuth 2.0 credentials:
   - Application type: Web application
   - Authorized redirect URIs: `http://localhost:8000/auth/callback`
5. Note down Client ID and Client Secret
6. Get a Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env and add your credentials:
# GOOGLE_CLIENT_ID=your_client_id
# GOOGLE_CLIENT_SECRET=your_client_secret
# GEMINI_API_KEY=your_gemini_api_key
# SECRET_KEY=your_random_secret_key
```

### 3. Start Qdrant with Docker

```bash
# From project root
docker-compose up -d qdrant

# Verify Qdrant is running
curl http://localhost:6333/health
```

### 4. Run Backend Server

```bash
# From backend directory
python main.py

# Or with uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at `http://localhost:8000`

### 5. Chrome Extension Setup

```bash
# Navigate to extension directory
cd extension

# The extension is ready to load (no build step needed for basic version)
```

**Load Extension in Chrome:**

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select the `extension` directory
5. The Glaze icon should appear in your extensions

### 6. Usage

1. Click the Glaze extension icon
2. Click "Sign in with Google"
3. Authorize the application
4. Wait for initial indexing (happens automatically)
5. Start searching with natural language queries!

**Example queries:**
- "machine learning papers"
- "budget spreadsheets from last quarter"
- "presentation about product roadmap"
- "meeting notes with John"

## API Endpoints

### Authentication
- `POST /auth/google` - Initiate OAuth flow
- `GET /auth/callback` - Handle OAuth callback

### Drive Operations
- `GET /drive/files` - List Drive files
- `POST /index` - Index files
- `POST /search` - Semantic search

### Health
- `GET /health` - Health check

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID | Yes | - |
| `GOOGLE_CLIENT_SECRET` | Google OAuth Client Secret | Yes | - |
| `GEMINI_API_KEY` | Google Gemini API Key | Yes | - |
| `SECRET_KEY` | Secret key for sessions | Yes | - |
| `QDRANT_HOST` | Qdrant host | No | localhost |
| `QDRANT_PORT` | Qdrant port | No | 6333 |
| `BACKEND_HOST` | Backend host | No | 0.0.0.0 |
| `BACKEND_PORT` | Backend port | No | 8000 |

## Development

### Run with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Project Structure

```
glaze/
├── backend/
│   ├── auth/              # OAuth authentication
│   ├── services/          # Core services
│   │   ├── drive_service.py
│   │   ├── file_processor.py
│   │   ├── embedding_service.py
│   │   ├── qdrant_service.py
│   │   ├── indexing_service.py
│   │   └── search_engine.py
│   ├── config.py          # Configuration
│   ├── database.py        # SQLite operations
│   ├── errors.py          # Custom exceptions
│   ├── logging_config.py  # Logging setup
│   └── main.py            # FastAPI app
├── extension/
│   ├── src/
│   │   ├── auth.js        # Auth utilities
│   │   └── api.js         # API client
│   ├── styles/
│   │   └── tailwind.css   # Styles
│   ├── manifest.json      # Extension manifest
│   ├── popup.html         # Popup UI
│   ├── popup.js           # Popup logic
│   └── background.js      # Background worker
├── docker-compose.yml     # Docker services
└── README.md
```

## Troubleshooting

### Qdrant Connection Error
- Ensure Qdrant is running: `docker ps`
- Check Qdrant health: `curl http://localhost:6333/health`
- Restart Qdrant: `docker-compose restart qdrant`

### Authentication Issues
- Verify OAuth credentials in `.env`
- Check redirect URI matches Google Cloud Console
- Clear browser cache and extension storage

### Indexing Failures
- Check file permissions in Google Drive
- Verify Gemini API key is valid
- Check API quota limits

### Search Returns No Results
- Ensure files have been indexed
- Check Qdrant collection: `curl http://localhost:6333/collections/drive_files`
- Try re-indexing with force flag

## Performance

- **Search latency**: < 2 seconds (p95)
- **Indexing throughput**: ~10 files/minute
- **Supported file size**: Up to 50MB per file
- **Chunk size**: 500-1000 tokens per chunk

## Limitations

- Requires active internet connection
- Gemini API free tier: 15 requests/minute
- Google Drive API: 1000 requests/100 seconds per user
- Only supports text-based files (PDF, DOCX, TXT, PPT)

## Future Enhancements

- [ ] Image search support
- [ ] RAG-based Q&A over documents
- [ ] File summarization
- [ ] "Find similar files" feature
- [ ] Real-time incremental indexing
- [ ] Multi-user support with proper auth
- [ ] Cloud deployment guide

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## Support

For issues and questions, please open a GitHub issue.
