# Implementation Plan: Glaze Semantic Search

## Overview

This implementation plan breaks down the Glaze semantic search system into discrete coding tasks. The system consists of a FastAPI backend (Python), a Chrome Extension frontend (JavaScript/React), and supporting infrastructure (Docker, Qdrant, SQLite). Tasks are organized to build incrementally, with early validation through testing and checkpoints.

## Tasks

- [x] 1. Set up project structure and configuration
  - Create directory structure: `backend/`, `extension/`, `docker/`, `tests/`
  - Create `backend/requirements.txt` with dependencies: fastapi, uvicorn, google-auth, google-api-python-client, qdrant-client, google-generativeai, PyPDF2, python-docx, python-pptx, tenacity, hypothesis
  - Create `backend/.env.example` with required environment variables: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GEMINI_API_KEY, QDRANT_HOST, QDRANT_PORT
  - Create `backend/config.py` to load environment variables with validation
  - _Requirements: 14.1, 14.2, 14.3, 14.4_

- [ ]* 1.1 Write unit tests for configuration loading
  - Test missing required environment variables raise errors
  - Test optional configuration uses default values
  - Test sensitive values are not logged
  - _Requirements: 14.4, 14.5_

- [x] 2. Set up Docker infrastructure for Qdrant
  - Create `docker-compose.yml` with Qdrant service configuration
  - Configure Qdrant to run on port 6333
  - Configure persistent volume storage at `./qdrant_data`
  - Add health check for Qdrant service
  - _Requirements: 11.1, 11.2, 11.3, 11.4_

- [ ]* 2.1 Write unit tests for Docker configuration
  - Verify docker-compose.yml has correct port mapping
  - Verify volume configuration is present
  - _Requirements: 11.2, 11.3_

- [x] 3. Implement SQLite database initialization
  - Create `backend/database.py` with SQLite connection management
  - Implement `create_tables()` function to create `files` table with schema: id, file_id (UNIQUE), file_name, mime_type, link, indexed_at, modified_time
  - Implement `create_tables()` to create `indexing_status` table with schema: file_id (PRIMARY KEY), status, chunk_count, error_message, last_attempt
  - Create indexes: idx_file_id on files(file_id), idx_modified_time on files(modified_time)
  - _Requirements: 6.1, 6.2_

- [ ]* 3.1 Write unit tests for database initialization
  - Test tables are created on first run
  - Test indexes are created correctly
  - Test idempotency (running create_tables twice doesn't fail)
  - _Requirements: 6.1_

- [ ]* 3.2 Write property test for metadata serialization round-trip
  - **Property 38: Metadata Serialization Round-Trip**
  - **Validates: Requirements 15.5**
  - Generate random FileMetadata objects, store in SQLite, retrieve, and verify all fields match
  - _Requirements: 15.5_

- [x] 4. Implement OAuth authentication handler
  - Create `backend/auth/oauth_handler.py` with OAuthHandler class
  - Implement `get_auth_url()` method to generate Google OAuth 2.0 authorization URL with PKCE
  - Implement `exchange_code_for_token(code)` method to exchange authorization code for access token and refresh token
  - Implement `refresh_access_token(refresh_token)` method to refresh expired tokens
  - Implement `store_token(token_data)` method to securely store tokens
  - Implement `get_stored_token()` method to retrieve stored tokens
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ]* 4.1 Write unit tests for OAuth handler
  - Test auth URL contains required parameters (client_id, redirect_uri, scope, response_type, state)
  - Test token exchange with mock Google API response
  - Test token refresh logic
  - Test error handling for invalid authorization codes
  - _Requirements: 1.1, 1.2, 1.4, 1.5_

- [ ]* 4.2 Write property test for token storage and retrieval
  - **Property 2: Token Storage and Retrieval**
  - **Validates: Requirements 1.3**
  - Generate random token strings, store them, retrieve them, and verify they match
  - _Requirements: 1.3_

- [ ]* 4.3 Write property test for authentication error handling
  - **Property 3: Authentication Error Handling**
  - **Validates: Requirements 1.5**
  - Simulate various authentication failures and verify descriptive error messages are returned
  - _Requirements: 1.5_

- [x] 5. Implement Google Drive service
  - Create `backend/services/drive_service.py` with DriveService class
  - Implement `list_files(access_token, page_token=None)` method to fetch files from Google Drive API
  - Implement pagination handling to follow nextPageToken until all files retrieved
  - Implement MIME type filtering for supported types: application/pdf, application/vnd.google-apps.document, text/plain, application/vnd.ms-powerpoint, application/vnd.openxmlformats-officedocument.presentationml.presentation
  - Implement `download_file(file_id, access_token)` method to download file content
  - Implement error handling and logging for Drive API errors
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ]* 5.1 Write unit tests for Drive service
  - Test file list retrieval with mock Drive API
  - Test pagination with multiple pages
  - Test MIME type filtering
  - Test error propagation from Drive API
  - _Requirements: 2.1, 2.3, 2.4, 2.5_

- [ ]* 5.2 Write property test for MIME type filtering
  - **Property 6: MIME Type Filtering**
  - **Validates: Requirements 2.3**
  - Generate random file lists with various MIME types, filter them, and verify only supported types remain
  - _Requirements: 2.3_

- [ ]* 5.3 Write property test for pagination handling
  - **Property 8: Pagination Handling**
  - **Validates: Requirements 2.5**
  - Simulate users with >100 files and verify all files are retrieved through pagination
  - _Requirements: 2.5_

- [x] 6. Implement file content extraction
  - Create `backend/services/file_processor.py` with FileProcessor class
  - Implement `extract_text(file_content, mime_type)` method with format-specific extraction:
    - PDF: Use PyPDF2 to extract text from all pages
    - DOCX: Use python-docx to extract text from paragraphs
    - TXT: Read text content directly
    - PPT/PPTX: Use python-pptx to extract text from slides
  - Implement error handling to log and skip files that fail extraction
  - Implement `chunk_text(text, chunk_size=750)` method to split text into 500-1000 token chunks with 100 token overlap
  - Use sentence boundaries for chunk splits when possible
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [ ]* 6.1 Write unit tests for file extraction
  - Test PDF extraction with sample PDF file
  - Test DOCX extraction with sample DOCX file
  - Test TXT extraction with sample TXT file
  - Test PPT/PPTX extraction with sample presentation files
  - Test error handling for corrupted files
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ]* 6.2 Write property test for text chunking bounds
  - **Property 11: Text Chunking Bounds**
  - **Validates: Requirements 3.6**
  - Generate random text content of various lengths, chunk it, and verify all chunks are 500-1000 tokens
  - _Requirements: 3.6_

- [ ]* 6.3 Write property test for file processing error handling
  - **Property 10: File Processing Error Handling**
  - **Validates: Requirements 3.5**
  - Simulate various file processing failures and verify errors are logged and indexing continues
  - _Requirements: 3.5_

- [x] 7. Checkpoint - Verify file processing pipeline
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement embedding service with Gemini API
  - Create `backend/services/embedding_service.py` with EmbeddingService class
  - Implement `generate_embedding(text)` method using Google Gemini multimodal-embedding-002 model
  - Implement `generate_embeddings_batch(texts)` method to process up to 10 texts per batch
  - Implement rate limiting logic (15 requests/minute for free tier)
  - Implement exponential backoff retry logic with tenacity: max 3 retries, initial delay 1s, multiplier 2
  - Implement error handling to log failures and continue with remaining chunks
  - Return embeddings as list of floats (768 dimensions)
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ]* 8.1 Write unit tests for embedding service
  - Test single embedding generation with mock Gemini API
  - Test batch processing
  - Test rate limit handling
  - Test retry logic with transient failures
  - Test error resilience (one chunk fails, others continue)
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ]* 8.2 Write property test for embedding format compatibility
  - **Property 15: Embedding Format Compatibility**
  - **Validates: Requirements 4.5**
  - Generate embeddings and verify they are lists of floats with 768 dimensions
  - _Requirements: 4.5_

- [ ]* 8.3 Write property test for embedding vector serialization round-trip
  - **Property 37: Embedding Vector Serialization Round-Trip**
  - **Validates: Requirements 15.3**
  - Generate random embedding vectors, serialize to Qdrant format, deserialize, and verify equivalence within floating-point tolerance
  - _Requirements: 15.3_

- [x] 9. Implement Qdrant vector database integration
  - Create `backend/services/qdrant_service.py` with QdrantService class
  - Implement `initialize_collection()` method to create "drive_files" collection if not exists
  - Configure collection with 768-dimensional vectors and Cosine distance metric
  - Configure HNSW index with ef_construct=100, m=16
  - Implement `store_embedding(chunk_id, vector, payload)` method to store vector with metadata
  - Implement `search_similar(query_vector, limit=10)` method for vector similarity search
  - Implement `delete_file_embeddings(file_id)` method to remove all chunks for a file
  - Implement error handling for Qdrant connection failures
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ]* 9.1 Write unit tests for Qdrant service
  - Test collection initialization
  - Test vector storage with payload
  - Test similarity search
  - Test deletion of file embeddings
  - Test error handling for connection failures
  - _Requirements: 5.1, 5.2, 5.5_

- [ ]* 9.2 Write property test for embedding storage completeness
  - **Property 16: Embedding Storage Completeness**
  - **Validates: Requirements 5.2, 5.3, 5.4**
  - Store embeddings with various payloads and verify all required fields are present after retrieval
  - _Requirements: 5.2, 5.3, 5.4_

- [x] 10. Implement indexing service orchestration
  - Create `backend/services/indexing_service.py` with IndexingService class
  - Implement `is_indexed(file_id)` method to check if file exists in metadata database
  - Implement `should_reindex(file_id, modified_time)` method to compare modification times
  - Implement `index_file(file_metadata, access_token, force_reindex=False)` method that:
    - Checks if file should be indexed (incremental logic)
    - Downloads file content via DriveService
    - Extracts text via FileProcessor
    - Chunks text via FileProcessor
    - Generates embeddings via EmbeddingService (in batches)
    - Stores embeddings in Qdrant via QdrantService
    - Stores metadata in SQLite
    - Updates indexing_status table
  - Implement parallel processing for up to 5 files concurrently
  - Implement error handling to continue with remaining files if one fails
  - Return IndexResult with status, chunk_count, and errors
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ]* 10.1 Write unit tests for indexing service
  - Test incremental indexing skip behavior
  - Test force reindex override
  - Test modified file re-indexing
  - Test parallel processing
  - Test error handling (one file fails, others continue)
  - _Requirements: 7.2, 7.3, 7.4, 7.5_

- [ ]* 10.2 Write property test for incremental indexing skip behavior
  - **Property 20: Incremental Indexing Skip Behavior**
  - **Validates: Requirements 7.2, 7.3**
  - Index files, then re-run indexing and verify unchanged files are skipped
  - _Requirements: 7.2, 7.3_

- [ ]* 10.3 Write property test for modified file re-indexing
  - **Property 21: Modified File Re-indexing**
  - **Validates: Requirements 7.4**
  - Index files, modify them, re-run indexing, and verify modified files are re-processed
  - _Requirements: 7.4_

- [ ]* 10.4 Write property test for force re-index override
  - **Property 22: Force Re-index Override**
  - **Validates: Requirements 7.5**
  - Index files, then force re-index and verify all files are re-processed
  - _Requirements: 7.5_

- [x] 11. Checkpoint - Verify indexing pipeline
  - Ensure all tests pass, ask the user if questions arise.

- [x] 12. Implement search engine
  - Create `backend/services/search_engine.py` with SearchEngine class
  - Implement `search(query, access_token, limit=10)` method that:
    - Generates query embedding via EmbeddingService
    - Performs vector similarity search via QdrantService
    - Extracts file_ids from search results
    - Fetches complete metadata from SQLite for each file_id
    - Combines results with file metadata
    - Returns list of SearchResult objects with file_name, mime_type, link, chunk_text, score
  - Implement query result caching with 5-minute TTL
  - Ensure search completes within 2 seconds for typical queries
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

- [ ]* 12.1 Write unit tests for search engine
  - Test query embedding generation
  - Test vector similarity search execution
  - Test metadata retrieval and joining
  - Test default result limit of 10
  - Test result completeness (all required fields present)
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ]* 12.2 Write property test for query embedding generation
  - **Property 23: Query Embedding Generation**
  - **Validates: Requirements 8.1**
  - Submit various search queries and verify embeddings are generated
  - _Requirements: 8.1_

- [ ]* 12.3 Write property test for default result limit
  - **Property 25: Default Result Limit**
  - **Validates: Requirements 8.3**
  - Perform searches without explicit limit and verify at most 10 results returned
  - _Requirements: 8.3_

- [ ]* 12.4 Write property test for search result completeness
  - **Property 26: Search Result Completeness**
  - **Validates: Requirements 8.4, 8.5**
  - Perform searches and verify all results include file_name, mime_type, link, chunk_text, and score
  - _Requirements: 8.4, 8.5_

- [x] 13. Implement FastAPI backend endpoints
  - Create `backend/main.py` with FastAPI application
  - Configure CORS middleware to allow Chrome Extension origin
  - Implement POST `/auth/google` endpoint that returns OAuth authorization URL
  - Implement GET `/auth/callback` endpoint that handles OAuth callback and exchanges code for tokens
  - Implement GET `/drive/files` endpoint that returns list of user's Drive files with pagination
  - Implement POST `/index` endpoint that triggers file indexing with optional file_ids and force_reindex parameters
  - Implement POST `/search` endpoint that accepts query and limit parameters and returns search results
  - Return all responses in JSON format with appropriate HTTP status codes
  - Implement request logging middleware (method, endpoint, status)
  - Implement error handling middleware to return structured error responses
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 13.5_

- [ ]* 13.1 Write unit tests for API endpoints
  - Test POST /auth/google returns auth URL
  - Test GET /auth/callback exchanges code for tokens
  - Test GET /drive/files returns file list with pagination
  - Test POST /index triggers indexing
  - Test POST /search returns search results
  - Test CORS headers are present
  - Test error responses have correct format
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7_

- [ ]* 13.2 Write property test for API response format
  - **Property 31: API Response Format**
  - **Validates: Requirements 12.6, 12.7**
  - Call various API endpoints and verify responses are valid JSON with appropriate status codes and CORS headers
  - _Requirements: 12.6, 12.7_

- [x] 14. Implement comprehensive error handling and logging
  - Create `backend/errors.py` with custom exception classes: AuthenticationError, TokenExpiredError, FileProcessingError, UnsupportedFileTypeError, FileSizeExceededError, EmbeddingError, RateLimitError, QuotaExceededError, StorageError, QdrantConnectionError, DatabaseError
  - Create `backend/logging_config.py` with structured logging configuration (JSON format with timestamp, level, component, message, context)
  - Implement error message mapping for user-friendly messages
  - Ensure sensitive data (tokens, API keys) are never logged
  - Implement logging in all components with appropriate levels (ERROR, WARNING, INFO, DEBUG)
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 14.5_

- [ ]* 14.1 Write unit tests for error handling
  - Test custom exception classes are raised correctly
  - Test error messages are user-friendly
  - Test sensitive data is not logged
  - Test structured log format
  - _Requirements: 13.1, 13.2, 14.5_

- [ ]* 14.2 Write property test for error logging and response format
  - **Property 32: Error Logging and Response Format**
  - **Validates: Requirements 13.1, 13.2**
  - Trigger various errors and verify they are logged with required fields and return structured responses
  - _Requirements: 13.1, 13.2_

- [ ]* 14.3 Write property test for sensitive data protection in logs
  - **Property 36: Sensitive Data Protection in Logs**
  - **Validates: Requirements 14.5**
  - Generate logs with various data and verify sensitive values are not present
  - _Requirements: 14.5_

- [x] 15. Checkpoint - Verify backend API
  - Ensure all tests pass, ask the user if questions arise.

- [x] 16. Implement Chrome Extension manifest and structure
  - Create `extension/manifest.json` with Manifest V3 configuration
  - Set manifest_version to 3
  - Configure permissions: ["storage", "identity"]
  - Configure host_permissions: ["http://localhost:8000/*"]
  - Configure action with default_popup: "popup.html"
  - Configure background service_worker: "background.js"
  - Configure content_security_policy: "script-src 'self'; object-src 'self'"
  - Create directory structure: `extension/src/`, `extension/assets/`, `extension/styles/`
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ]* 16.1 Write unit tests for manifest configuration
  - Test manifest version is 3
  - Test required permissions are present
  - Test CSP is configured correctly
  - _Requirements: 10.1, 10.5_

- [x] 17. Implement Chrome Extension authentication UI and logic
  - Create `extension/src/background.js` with OAuth flow handling
  - Implement `initiateAuth()` function to call backend /auth/google endpoint
  - Implement `handleAuthCallback()` function to process OAuth callback
  - Implement token storage in chrome.storage.local
  - Implement token refresh logic before expiration
  - Create `extension/src/auth.js` with authentication state management
  - Implement `getAccessToken()` function to retrieve valid token (refresh if needed)
  - Implement `logout()` function to clear stored tokens
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ]* 17.1 Write unit tests for extension authentication
  - Test OAuth flow initiation
  - Test token storage and retrieval
  - Test token refresh logic
  - Test logout clears tokens
  - _Requirements: 1.2, 1.3, 1.4_

- [x] 18. Implement Chrome Extension search UI with React and Tailwind
  - Create `extension/popup.html` with React root element
  - Create `extension/src/components/SearchBox.jsx` with search input and submit button
  - Create `extension/src/components/ResultList.jsx` to display search results
  - Create `extension/src/components/ResultItem.jsx` to display individual result with:
    - File name
    - File type icon (based on mime_type)
    - Content snippet (chunk_text)
    - "Open in Drive" button that opens webViewLink
  - Create `extension/src/components/LoadingSpinner.jsx` for loading state
  - Create `extension/src/components/ErrorMessage.jsx` for error display
  - Create `extension/src/components/EmptyState.jsx` for "No results found" message
  - Set up Tailwind CSS for styling
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8_

- [ ]* 18.1 Write unit tests for extension UI components
  - Test SearchBox renders and handles input
  - Test ResultList displays results correctly
  - Test ResultItem shows all required fields
  - Test LoadingSpinner displays during search
  - Test ErrorMessage displays on errors
  - Test EmptyState displays when no results
  - _Requirements: 9.1, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8_

- [x] 19. Implement Chrome Extension API communication
  - Create `extension/src/api.js` with API client functions
  - Implement `searchDriveFiles(query, limit)` function to call POST /search endpoint
  - Implement `triggerIndexing(fileIds, forceReindex)` function to call POST /index endpoint
  - Implement `getDriveFiles(pageToken)` function to call GET /drive/files endpoint
  - Implement error handling for network failures and API errors
  - Implement request timeout handling (10 seconds)
  - _Requirements: 9.2, 12.4, 12.5_

- [ ]* 19.1 Write unit tests for API communication
  - Test search API call with mock backend
  - Test indexing API call
  - Test file list API call
  - Test error handling for network failures
  - Test timeout handling
  - _Requirements: 9.2_

- [ ]* 19.2 Write property test for Chrome Extension API communication
  - **Property 27: Chrome Extension API Communication**
  - **Validates: Requirements 9.2**
  - Submit various queries and verify HTTP requests are sent to backend
  - _Requirements: 9.2_

- [x] 20. Wire Chrome Extension components together
  - Create `extension/src/popup.js` as main entry point
  - Implement search flow: user input → API call → display results
  - Implement loading state management during API calls
  - Implement error state management and display
  - Implement authentication check on popup open
  - Implement "Sign In" button if not authenticated
  - Connect all UI components with state management
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.8_

- [ ]* 20.1 Write integration tests for extension
  - Test complete search flow (input → API → results)
  - Test authentication flow (sign in → token storage → API calls)
  - Test error handling flow (API error → error message display)
  - Test empty results flow (no results → empty state display)
  - _Requirements: 9.2, 9.3, 9.4, 9.7, 9.8_

- [x] 21. Checkpoint - Verify Chrome Extension
  - Ensure all tests pass, ask the user if questions arise.

- [x] 22. Create build and deployment scripts
  - Create `backend/Dockerfile` for FastAPI application
  - Create `docker-compose.yml` to orchestrate backend and Qdrant services
  - Create `extension/build.sh` script to bundle extension for Chrome Web Store
  - Create `README.md` with setup instructions, environment variable configuration, and usage guide
  - Create `.gitignore` to exclude sensitive files (.env, node_modules, __pycache__, qdrant_data)
  - _Requirements: 11.1, 11.5_

- [ ] 23. Create end-to-end integration tests
  - Create `tests/integration/test_full_flow.py` for complete workflow testing
  - Test authentication flow: OAuth redirect → callback → token storage
  - Test indexing pipeline: Drive fetch → extraction → embedding → storage
  - Test search flow: query → embedding → search → metadata join → results
  - Test incremental indexing: index → modify file → re-index
  - Test error recovery: API failure → retry → success
  - Use Docker Compose to spin up Qdrant for tests
  - Mock Google OAuth and Drive API
  - Mock Gemini API with pre-generated embeddings
  - _Requirements: All requirements_

- [ ]* 23.1 Write property-based integration tests
  - Test various file types and sizes through full pipeline
  - Test various query types and verify results
  - Test concurrent operations (multiple users, multiple searches)
  - _Requirements: All requirements_

- [ ] 24. Final checkpoint - Complete system verification
  - Ensure all tests pass (unit, property-based, integration)
  - Verify test coverage meets requirements (backend 85-90%, extension 80-90%)
  - Run manual end-to-end test with real Google Drive account
  - Verify Docker Compose starts all services correctly
  - Verify Chrome Extension loads and functions correctly
  - Ask the user if questions arise or if ready for deployment

## Notes

- Tasks marked with `*` are optional testing tasks and can be skipped for faster MVP delivery
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties across all inputs
- Unit tests validate specific examples, edge cases, and integration points
- Backend uses Python with FastAPI, frontend uses JavaScript/React with Tailwind CSS
- All property tests should run minimum 100 iterations and include property reference comments
- Use `hypothesis` for Python property tests and `fast-check` for JavaScript property tests
