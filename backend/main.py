"""FastAPI backend for Glaze semantic search."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
from typing import List, Optional

from config import get_settings
from database import initialize_database
from auth.oauth_handler import oauth_handler
from services.drive_service import DriveService
from services.file_processor import file_processor
from services.embedding_service import embedding_service
from services.qdrant_service import qdrant_service
from services.indexing_service import IndexingService
from services.search_engine import initialize_search_engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Request/Response models
class AuthResponse(BaseModel):
    auth_url: str
    state: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str]
    expires_in: int
    token_type: str


class IndexRequest(BaseModel):
    file_ids: Optional[List[str]] = None
    force_reindex: bool = False


class IndexResponse(BaseModel):
    status: str
    indexed_count: int
    skipped_count: int
    failed_count: int
    errors: List[dict]


class SearchRequest(BaseModel):
    query: str
    limit: int = 10


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("Starting Glaze backend...")
    initialize_database()
    qdrant_service.initialize_collection()
    initialize_search_engine(embedding_service, qdrant_service)
    logger.info("Glaze backend started successfully")
    yield
    # Shutdown
    logger.info("Shutting down Glaze backend...")


# Create FastAPI app
app = FastAPI(
    title="Glaze Semantic Search API",
    description="Backend API for semantic search over Google Drive files",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify Chrome extension origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware for request logging
@app.middleware("http")
async def log_requests(request, call_next):
    """Log all API requests."""
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"{request.method} {request.url.path} - {response.status_code}")
    return response


# Authentication endpoints
@app.post("/auth/google", response_model=AuthResponse)
async def initiate_google_auth():
    """Initiate Google OAuth 2.0 flow."""
    try:
        auth_data = oauth_handler.get_auth_url()
        return AuthResponse(**auth_data)
    except Exception as e:
        logger.error(f"Auth initiation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/auth/callback")
async def handle_auth_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query(..., description="CSRF state token")
):
    """Handle OAuth callback and exchange code for tokens."""
    try:
        token_data = await oauth_handler.exchange_code_for_token(code)
        
        # Store tokens (using state as user_id for demo)
        oauth_handler.store_token(state, token_data)
        
        # Return HTML page that notifies the extension
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Successful</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }}
                .container {{
                    text-align: center;
                    background: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                }}
                h1 {{
                    color: #4CAF50;
                    margin-bottom: 20px;
                }}
                p {{
                    color: #666;
                    font-size: 16px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>✓ Authentication Successful!</h1>
                <p>You can close this window and return to the extension.</p>
            </div>
            <script>
                // Send message to extension with token data
                const authData = {{
                    type: 'GLAZE_AUTH_SUCCESS',
                    access_token: '{token_data.get("access_token")}',
                    refresh_token: '{token_data.get("refresh_token", "")}',
                    expires_in: {token_data.get("expires_in", 3600)},
                    user_id: '{state}'
                }};
                
                console.log('Sending auth data:', authData);
                window.postMessage(authData, '*');
                
                // Also try sending via chrome.runtime if available
                if (typeof chrome !== 'undefined' && chrome.runtime) {{
                    chrome.runtime.sendMessage(authData, function(response) {{
                        console.log('Direct message response:', response);
                    }});
                }}
                
                // Close window after 2 seconds
                setTimeout(function() {{
                    window.close();
                }}, 2000);
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"Auth callback failed: {str(e)}")
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Failed</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                }}
                .container {{
                    text-align: center;
                    background: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                }}
                h1 {{
                    color: #f44336;
                    margin-bottom: 20px;
                }}
                p {{
                    color: #666;
                    font-size: 16px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>✗ Authentication Failed</h1>
                <p>{str(e)}</p>
                <p>Please close this window and try again.</p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=error_html, status_code=400)


# Drive endpoints
@app.get("/drive/files")
async def list_drive_files(
    user_id: str = Query(..., description="User identifier"),
    page_token: Optional[str] = Query(None, description="Pagination token")
):
    """List files from Google Drive."""
    try:
        # Get credentials
        credentials = oauth_handler.get_credentials(user_id)
        if not credentials:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Create Drive service and list files
        drive_service = DriveService(credentials)
        result = drive_service.list_files(page_token)
        
        return JSONResponse(content=result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Indexing endpoints
@app.post("/index")
async def index_files(
    request: IndexRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Query(..., description="User identifier")
):
    """Index files from Google Drive in the background."""
    try:
        # Get credentials
        credentials = oauth_handler.get_credentials(user_id)
        if not credentials:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Create services
        drive_service = DriveService(credentials)
        indexing_service = IndexingService(
            drive_service,
            file_processor,
            embedding_service,
            qdrant_service
        )
        
        # Get files to index
        if request.file_ids:
            files = [{'id': f_id, 'name': 'Unknown', 'mimeType': 'application/pdf'} for f_id in request.file_ids]
        else:
            files = drive_service.list_all_files()
        
        # Run indexing in background
        background_tasks.add_task(
            indexing_service.index_files, 
            files, 
            request.force_reindex
        )
        
        return {
            "status": "started",
            "message": f"Indexing started for {len(files)} files in the background.",
            "file_count": len(files)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Indexing initiation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Search endpoints
@app.post("/search")
async def search_files(
    request: SearchRequest,
    user_id: str = Query(..., description="User identifier")
):
    """Perform semantic search over indexed files."""
    try:
        # Verify authentication
        credentials = oauth_handler.get_credentials(user_id)
        if not credentials:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Import search engine
        from services.search_engine import search_engine
        
        if not search_engine:
            raise HTTPException(status_code=500, detail="Search engine not initialized")
        
        # Perform search
        results = search_engine.search_dict(request.query, request.limit)
        
        return JSONResponse(content=results)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check Qdrant connection
        info = qdrant_service.get_collection_info()
        return {
            "status": "healthy",
            "qdrant": info
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
