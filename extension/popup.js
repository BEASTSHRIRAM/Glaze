// Main popup script for Glaze extension
import { initiateAuth, getAccessToken, logout, isAuthenticated } from './src/auth.js';
import { searchDriveFiles, triggerIndexing } from './src/api.js';

const API_BASE_URL = 'http://localhost:8000';

// State
let currentUser = null;
let searchResults = [];
let isLoading = false;

// Initialize app
document.addEventListener('DOMContentLoaded', async () => {
  await checkAuth();
  render();
});

async function checkAuth() {
  const tokenData = await getAccessToken();
  if (tokenData.authenticated) {
    currentUser = {
      userId: tokenData.user_id,
      accessToken: tokenData.access_token
    };
  } else {
    currentUser = null;
  }
}

function render() {
  const root = document.getElementById('root');
  
  if (!currentUser) {
    root.innerHTML = renderAuthScreen();
    attachAuthListeners();
  } else {
    root.innerHTML = renderSearchScreen();
    attachSearchListeners();
  }
}

function renderAuthScreen() {
  return `
    <div class="flex flex-col items-center justify-center h-screen p-6 bg-gradient-to-br from-blue-50 to-indigo-100">
      <div class="text-center">
        <h1 class="text-3xl font-bold text-gray-800 mb-2">Glaze</h1>
        <p class="text-gray-600 mb-8">Semantic search for your Google Drive</p>
        <button id="signInBtn" class="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg shadow-md transition duration-200">
          Sign in with Google
        </button>
      </div>
    </div>
  `;
}

function renderSearchScreen() {
  return `
    <div class="flex flex-col h-full">
      <!-- Header -->
      <div class="bg-white border-b border-gray-200 p-4">
        <div class="flex items-center justify-between mb-3">
          <h1 class="text-xl font-bold text-gray-800">Glaze</h1>
          <div class="flex items-center space-x-3">
            <button id="syncBtn" class="text-sm bg-blue-100 text-blue-700 hover:bg-blue-200 px-2 py-1 rounded transition duration-200">
              Sync Drive
            </button>
            <button id="logoutBtn" class="text-sm text-gray-600 hover:text-gray-800">
              Logout
            </button>
          </div>
        </div>
        
        <!-- Search Box -->
        <div class="relative">
          <input
            type="text"
            id="searchInput"
            placeholder="Search your Drive files..."
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button id="searchBtn" class="absolute right-2 top-2 text-blue-600 hover:text-blue-700">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
            </svg>
          </button>
        </div>
      </div>
      
      <!-- Results Area -->
      <div id="resultsContainer" class="flex-1 overflow-y-auto p-4">
        ${renderResults()}
      </div>
    </div>
  `;
}

function renderResults() {
  if (isLoading) {
    return renderLoading();
  }
  
  if (searchResults.length === 0) {
    return renderEmptyState();
  }
  
  return `
    <div class="space-y-3">
      ${searchResults.map(result => renderResultItem(result)).join('')}
    </div>
  `;
}

function renderLoading() {
  return `
    <div class="flex items-center justify-center h-full">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>
  `;
}

function renderEmptyState() {
  return `
    <div class="flex flex-col items-center justify-center h-full text-center p-6">
      <svg class="w-16 h-16 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
      </svg>
      <p class="text-gray-600">Search your Drive files using natural language</p>
      <p class="text-sm text-gray-500 mt-2">Try: "machine learning papers" or "budget spreadsheets"</p>
    </div>
  `;
}

function renderResultItem(result) {
  const icon = getFileIcon(result.mime_type);
  const snippet = result.chunk_text.substring(0, 150) + (result.chunk_text.length > 150 ? '...' : '');
  
  return `
    <div class="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition duration-200">
      <div class="flex items-start">
        <div class="flex-shrink-0 mr-3">
          ${icon}
        </div>
        <div class="flex-1 min-w-0">
          <h3 class="text-sm font-semibold text-gray-800 truncate">${escapeHtml(result.file_name)}</h3>
          <p class="text-xs text-gray-600 mt-1 line-clamp-2">${escapeHtml(snippet)}</p>
          <div class="flex items-center mt-2">
            <span class="text-xs text-gray-500 mr-3">Score: ${(result.score * 100).toFixed(1)}%</span>
            <a href="${result.link}" target="_blank" class="text-xs text-blue-600 hover:text-blue-700 font-medium">
              Open in Drive →
            </a>
          </div>
        </div>
      </div>
    </div>
  `;
}

function getFileIcon(mimeType) {
  if (mimeType.includes('pdf')) {
    return '<svg class="w-8 h-8 text-red-500" fill="currentColor" viewBox="0 0 20 20"><path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"></path></svg>';
  } else if (mimeType.includes('document') || mimeType.includes('word')) {
    return '<svg class="w-8 h-8 text-blue-500" fill="currentColor" viewBox="0 0 20 20"><path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"></path></svg>';
  } else if (mimeType.includes('presentation') || mimeType.includes('powerpoint')) {
    return '<svg class="w-8 h-8 text-orange-500" fill="currentColor" viewBox="0 0 20 20"><path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"></path></svg>';
  } else {
    return '<svg class="w-8 h-8 text-gray-500" fill="currentColor" viewBox="0 0 20 20"><path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"></path></svg>';
  }
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Event listeners
function attachAuthListeners() {
  document.getElementById('signInBtn').addEventListener('click', async () => {
    await initiateAuth();
  });
}

function attachSearchListeners() {
  const searchInput = document.getElementById('searchInput');
  const searchBtn = document.getElementById('searchBtn');
  const logoutBtn = document.getElementById('logoutBtn');
  const syncBtn = document.getElementById('syncBtn');
  
  searchBtn.addEventListener('click', handleSearch);
  syncBtn.addEventListener('click', handleSync);
  searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  });
  
  logoutBtn.addEventListener('click', async () => {
    await logout();
    currentUser = null;
    searchResults = [];
    render();
  });
}

async function handleSync() {
  const syncBtn = document.getElementById('syncBtn');
  if (!syncBtn || isLoading) return;
  
  const originalText = syncBtn.innerText;
  syncBtn.innerText = 'Syncing...';
  syncBtn.disabled = true;
  syncBtn.classList.add('opacity-50', 'cursor-not-allowed');
  
  try {
    const result = await triggerIndexing(currentUser.userId);
    console.log('Indexing result:', result);
    alert(`Sync started! Processing ${result.file_count} files in the background. Check back in a few minutes.`);
  } catch (error) {
    console.error('Sync failed:', error);
    alert('Sync failed: ' + error.message);
  } finally {
    syncBtn.innerText = originalText;
    syncBtn.disabled = false;
    syncBtn.classList.remove('opacity-50', 'cursor-not-allowed');
  }
}

async function handleSearch() {
  const searchInput = document.getElementById('searchInput');
  const query = searchInput.value.trim();
  
  if (!query) return;
  
  isLoading = true;
  updateResults();
  
  try {
    const results = await searchDriveFiles(query, currentUser.userId);
    searchResults = results.results || [];
  } catch (error) {
    console.error('Search failed:', error);
    searchResults = [];
    alert('Search failed. Please try again.');
  } finally {
    isLoading = false;
    updateResults();
  }
}

function updateResults() {
  const container = document.getElementById('resultsContainer');
  if (container) {
    container.innerHTML = renderResults();
  }
}

// Listen for auth completion from background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'authComplete') {
    console.log('Auth complete message received, refreshing UI');
    checkAuth();
    render();
  }
});

// Listen for auth completion
chrome.storage.onChanged.addListener(async (changes, namespace) => {
  if (namespace === 'local' && changes.access_token) {
    console.log('Access token changed, refreshing auth state');
    await checkAuth();
    render();
  }
});
