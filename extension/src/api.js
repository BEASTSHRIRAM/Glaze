// API client for Glaze backend

const API_BASE_URL = 'http://localhost:8000';
const REQUEST_TIMEOUT = 10000; // 10 seconds

async function fetchWithTimeout(url, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);
  
  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    clearTimeout(timeout);
    return response;
  } catch (error) {
    clearTimeout(timeout);
    if (error.name === 'AbortError') {
      throw new Error('Request timeout');
    }
    throw error;
  }
}

export async function searchDriveFiles(query, userId, limit = 10) {
  try {
    const response = await fetchWithTimeout(`${API_BASE_URL}/search?user_id=${userId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ query, limit })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Search failed');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Search API error:', error);
    throw error;
  }
}

export async function triggerIndexing(userId, fileIds = null, forceReindex = false) {
  try {
    const response = await fetchWithTimeout(`${API_BASE_URL}/index?user_id=${userId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        file_ids: fileIds,
        force_reindex: forceReindex
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Indexing failed');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Indexing API error:', error);
    throw error;
  }
}

export async function getDriveFiles(userId, pageToken = null) {
  try {
    let url = `${API_BASE_URL}/drive/files?user_id=${userId}`;
    if (pageToken) {
      url += `&page_token=${pageToken}`;
    }
    
    const response = await fetchWithTimeout(url, {
      method: 'GET'
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch files');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Drive files API error:', error);
    throw error;
  }
}

export async function checkHealth() {
  try {
    const response = await fetchWithTimeout(`${API_BASE_URL}/health`, {
      method: 'GET'
    });
    
    if (!response.ok) {
      throw new Error('Health check failed');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Health check error:', error);
    throw error;
  }
}
