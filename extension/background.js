// Background service worker for Glaze extension

const API_BASE_URL = 'http://localhost:8000';

// Handle messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'initiateAuth') {
    initiateAuth().then(sendResponse);
    return true;
  }
  
  if (request.action === 'getAccessToken') {
    getAccessToken().then(sendResponse);
    return true;
  }
  
  if (request.action === 'logout') {
    logout().then(sendResponse);
    return true;
  }
});

async function initiateAuth() {
  try {
    // Call backend to get auth URL
    const response = await fetch(`${API_BASE_URL}/auth/google`, {
      method: 'POST'
    });
    
    if (!response.ok) {
      throw new Error('Failed to initiate authentication');
    }
    
    const data = await response.json();
    const authUrl = data.auth_url;
    const state = data.state;
    
    // Store state for verification
    await chrome.storage.local.set({ auth_state: state });
    
    // Open auth URL in new tab
    chrome.tabs.create({ url: authUrl });
    
    return { success: true };
  } catch (error) {
    console.error('Auth initiation failed:', error);
    return { success: false, error: error.message };
  }
}

async function getAccessToken() {
  try {
    const data = await chrome.storage.local.get(['access_token', 'token_expiry', 'user_id']);
    
    if (!data.access_token) {
      return { authenticated: false };
    }
    
    // Check if token is expired
    const now = Date.now();
    if (data.token_expiry && now >= data.token_expiry) {
      // Token expired, need to re-authenticate
      return { authenticated: false, expired: true };
    }
    
    return {
      authenticated: true,
      access_token: data.access_token,
      user_id: data.user_id
    };
  } catch (error) {
    console.error('Failed to get access token:', error);
    return { authenticated: false, error: error.message };
  }
}

async function logout() {
  try {
    await chrome.storage.local.remove(['access_token', 'refresh_token', 'token_expiry', 'user_id', 'user_email']);
    return { success: true };
  } catch (error) {
    console.error('Logout failed:', error);
    return { success: false, error: error.message };
  }
}

// Listen for OAuth callback and poll for token storage
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (changeInfo.url && changeInfo.url.includes('/auth/callback')) {
    console.log('Auth callback detected on tab:', tabId);
    
    // Get the stored state to verify later
    const stored = await chrome.storage.local.get(['auth_state']);
    const expectedState = stored.auth_state;
    
    // Poll the backend to check if tokens were stored
    let pollCount = 0;
    const pollInterval = setInterval(async () => {
      pollCount++;
      console.log(`Polling for auth completion (attempt ${pollCount})...`);
      
      try {
        // Try to get tokens from backend by checking if we can access drive files
        const response = await fetch(`${API_BASE_URL}/drive/files?user_id=${expectedState}`);
        
        if (response.ok) {
          console.log('Auth successful! Tokens are stored on backend');
          clearInterval(pollInterval);
          
          // Store tokens locally - use a marker token since real tokens are on backend
          const expiryTime = Date.now() + (3600 * 1000); // 1 hour default
          await chrome.storage.local.set({
            access_token: expectedState, // Store the user_id/state as the token identifier
            refresh_token: '',
            token_expiry: expiryTime,
            user_id: expectedState
          });
          
          console.log('Auth marker stored locally, closing auth tab');
          chrome.tabs.remove(tabId);
          
          // Notify popup that auth is complete
          chrome.runtime.sendMessage({
            action: 'authComplete'
          }).catch(() => {
            // Popup might not be open, that's ok
          });
        }
      } catch (error) {
        console.log('Auth check failed (expected during polling):', error.message);
      }
      
      // Stop polling after 30 seconds
      if (pollCount > 30) {
        console.log('Auth polling timeout');
        clearInterval(pollInterval);
      }
    }, 1000);
  }
});
