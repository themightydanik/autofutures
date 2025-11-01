# backend/services/oauth_service.py
from google.oauth2 import id_token
from google.auth.transport import requests
from typing import Dict
import logging

logger = logging.getLogger(__name__)

# Google OAuth Client ID (нужно получить в Google Cloud Console)
GOOGLE_CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com"

class OAuthService:
    """Google OAuth authentication service"""
    
    @staticmethod
    async def verify_google_token(token: str) -> Dict:
        """Verify Google ID token and return user info"""
        try:
            # Verify the token
            idinfo = id_token.verify_oauth2_token(
                token, 
                requests.Request(), 
                GOOGLE_CLIENT_ID
            )
            
            # Check issuer
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer')
            
            # Extract user info
            user_info = {
                'google_id': idinfo['sub'],
                'email': idinfo['email'],
                'name': idinfo.get('name', ''),
                'picture': idinfo.get('picture', ''),
                'email_verified': idinfo.get('email_verified', False)
            }
            
            logger.info(f"Google token verified for: {user_info['email']}")
            return user_info
            
        except ValueError as e:
            logger.error(f"Invalid Google token: {str(e)}")
            raise ValueError("Invalid Google token")
        except Exception as e:
            logger.error(f"Google token verification error: {str(e)}")
            raise
