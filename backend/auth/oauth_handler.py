"""OAuth 2.0 authentication handler for Google."""
import logging
import secrets
import json
from typing import Dict, Optional, Any
from urllib.parse import urlencode
import httpx
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from config import get_settings
from database import store_oauth_token, get_oauth_token

logger = logging.getLogger(__name__)

# Google OAuth 2.0 endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/userinfo.email"
]


class OAuthHandler:
    """Handles Google OAuth 2.0 authentication flow."""
    
    def __init__(self):
        self.settings = get_settings()
        self.tokens: Dict[str, Dict[str, Any]] = {}  # In-memory token storage
    
    def get_auth_url(self, state: Optional[str] = None) -> Dict[str, str]:
        """
        Generate Google OAuth 2.0 authorization URL.
        
        Returns:
            Dict with 'auth_url' and 'state' for CSRF protection
        """
        if state is None:
            state = secrets.token_urlsafe(32)
        
        params = {
            "client_id": self.settings.google_client_id,
            "redirect_uri": self.settings.google_redirect_uri,
            "response_type": "code",
            "scope": " ".join(GOOGLE_SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "state": state
        }
        
        auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
        
        logger.info(f"Generated OAuth URL with state: {state[:10]}...")
        return {
            "auth_url": auth_url,
            "state": state
        }
    
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token and refresh token.
        
        Args:
            code: Authorization code from Google OAuth callback
            
        Returns:
            Dict containing access_token, refresh_token, expires_in, token_type
            
        Raises:
            Exception: If token exchange fails
        """
        try:
            data = {
                "code": code,
                "client_id": self.settings.google_client_id,
                "client_secret": self.settings.google_client_secret,
                "redirect_uri": self.settings.google_redirect_uri,
                "grant_type": "authorization_code"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(GOOGLE_TOKEN_URL, data=data)
                response.raise_for_status()
                token_data = response.json()
            
            logger.info("Successfully exchanged code for tokens")
            return token_data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Token exchange failed: {e.response.text}")
            raise Exception(f"Failed to exchange authorization code: {e.response.text}")
        except Exception as e:
            logger.error(f"Token exchange error: {str(e)}")
            raise Exception(f"Authentication failed: {str(e)}")
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an expired access token using refresh token.
        
        Args:
            refresh_token: The refresh token
            
        Returns:
            Dict containing new access_token and expires_in
            
        Raises:
            Exception: If token refresh fails
        """
        try:
            data = {
                "client_id": self.settings.google_client_id,
                "client_secret": self.settings.google_client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(GOOGLE_TOKEN_URL, data=data)
                response.raise_for_status()
                token_data = response.json()
            
            logger.info("Successfully refreshed access token")
            return token_data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Token refresh failed: {e.response.text}")
            raise Exception(f"Failed to refresh token: {e.response.text}")
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            raise Exception(f"Token refresh failed: {str(e)}")
    
    def store_token(self, user_id: str, token_data: Dict[str, Any]) -> None:
        """
        Store access token and refresh token securely.
        
        Args:
            user_id: Unique identifier for the user
            token_data: Token data from Google OAuth
        """
        store_oauth_token(user_id, token_data)
        logger.info(f"Stored tokens for user: {user_id}")
    
    def get_stored_token(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve stored tokens for a user.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            Token data dict or None if not found
        """
        token_data = get_oauth_token(user_id)
        if token_data:
            logger.info(f"Retrieved tokens for user: {user_id}")
        else:
            logger.warning(f"No tokens found for user: {user_id}")
        return token_data
    
    def get_credentials(self, user_id: str) -> Optional[Credentials]:
        """
        Get Google API credentials for a user.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            Google Credentials object or None
        """
        token_data = self.get_stored_token(user_id)
        if not token_data:
            return None
        
        return Credentials(
            token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            token_uri=GOOGLE_TOKEN_URL,
            client_id=self.settings.google_client_id,
            client_secret=self.settings.google_client_secret,
            scopes=GOOGLE_SCOPES
        )


# Global OAuth handler instance
oauth_handler = OAuthHandler()
