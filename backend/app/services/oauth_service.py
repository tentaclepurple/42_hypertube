# backend/app/services/oauth_service.py
import os
import requests
from urllib.parse import urlencode
import json
from app.models.users import UserCreate
from .auth_service import AuthService

class OAuthService:
    """OAuth service"""
    
    # provider info
    PROVIDERS_CONFIG = {
        "google": {
            "auth_url": "https://accounts.google.com/o/oauth2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "userinfo_url": "https://www.googleapis.com/oauth2/v3/userinfo",
            "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
            "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
            "scope": "email profile"
        },
        "github": {
            "auth_url": "https://github.com/login/oauth/authorize",
            "token_url": "https://github.com/login/oauth/access_token",
            "userinfo_url": "https://api.github.com/user",
            "email_url": "https://api.github.com/user/emails",
            "client_id": os.environ.get("GITHUB_CLIENT_ID"),
            "client_secret": os.environ.get("GITHUB_CLIENT_SECRET"),
            "scope": "read:user user:email"
        },
        "42": {
            "auth_url": "https://api.intra.42.fr/oauth/authorize",
            "token_url": "https://api.intra.42.fr/oauth/token",
            "userinfo_url": "https://api.intra.42.fr/v2/me",
            "client_id": os.environ.get("FORTYTWO_CLIENT_ID"),
            "client_secret": os.environ.get("FORTYTWO_CLIENT_SECRET"),
            "scope": "public"
        }
    }
    
    @staticmethod
    def get_authorization_url(provider, redirect_uri, state=None):
        """Generate URL"""
        if provider not in OAuthService.PROVIDERS_CONFIG:
            raise ValueError(f"Provider {provider} not supported")
        
        config = OAuthService.PROVIDERS_CONFIG[provider]
        
        if not config.get("client_id") or not config.get("client_secret"):
            raise ValueError(f"Missing client credentials for {provider}")
        
        params = {
            "client_id": config["client_id"],
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": config["scope"]
        }
        
        # Agregar state si se proporciona (para seguridad CSRF) ######
        if state:
            params["state"] = state
            
        auth_url = f"{config['auth_url']}?{urlencode(params)}"
        return auth_url
    
    @staticmethod
    async def process_callback(provider, code, redirect_uri):
        """Procesar callback de OAuth y obtener información del usuario"""
        if provider not in OAuthService.PROVIDERS_CONFIG:
            raise ValueError(f"Provider {provider} not supported")
        
        config = OAuthService.PROVIDERS_CONFIG[provider]
        

        token_params = {
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }
        
        headers = {"Accept": "application/json"}
        if provider == "github":
            headers["Accept"] = "application/json"
        
        token_response = requests.post(
            config["token_url"], 
            data=token_params if provider != "github" else None,
            params=token_params if provider == "github" else None,
            headers=headers
        )
        
        if token_response.status_code != 200:
            raise ValueError(f"Error obtaining access token: {token_response.text}")
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise ValueError("No access token received")
        
        # Obtener información del usuario
        user_info = await OAuthService._get_user_info(provider, access_token)
        
        # Transformar información del usuario según el proveedor
        standardized_user = OAuthService._standardize_user_info(provider, user_info)
        
        # Aquí podrías crear o actualizar el usuario en tu base de datos
        # Usando AuthService o directamente
        return standardized_user
    
    @staticmethod
    async def _get_user_info(provider, access_token):
        """Get user info from OAuth provider"""
        config = OAuthService.PROVIDERS_CONFIG[provider]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        if provider == "github":
            headers["Accept"] = "application/json"
        
        user_response = requests.get(
            config["userinfo_url"],
            headers=headers
        )
        
        if user_response.status_code != 200:
            raise ValueError(f"Error obtaining user info: {user_response.text}")
        
        user_info = user_response.json()
        
        # Another request is necessary for github
        if provider == "github" and not user_info.get("email"):
            email_response = requests.get(
                config["email_url"],
                headers=headers
            )
            
            if email_response.status_code == 200:
                emails = email_response.json()
                primary_email = next((e for e in emails if e.get("primary")), emails[0] if emails else None)
                if primary_email:
                    user_info["email"] = primary_email.get("email")
        
        return user_info
    
    @staticmethod
    def _standardize_user_info(provider, user_info):
        """Standarize data"""

        if provider == "google":
            return {
                "email": user_info.get("email"),
                "username": user_info.get("email").split("@")[0],
                "first_name": user_info.get("given_name", ""),
                "last_name": user_info.get("family_name", ""),
                "profile_picture": user_info.get("picture", ""),
                "oauth_provider": provider,
                "oauth_id": user_info.get("sub")
            }
        elif provider == "github":
            name_parts = (user_info.get("name") or "").split(" ")
            return {
                "email": user_info.get("email"),
                "username": user_info.get("login"),
                "first_name": name_parts[0] if name_parts else "",
                "last_name": " ".join(name_parts[1:]) if len(name_parts) > 1 else "",
                "profile_picture": user_info.get("avatar_url", ""),
                "oauth_provider": provider,
                "oauth_id": str(user_info.get("id"))
            }
        elif provider == "42":
            avatar = user_info.get('image', {})
            avatar_url = avatar.get('versions', {}).get('small', "")

            return {
                "email": user_info.get("email"),
                "username": user_info.get("login"),
                "first_name": user_info.get("first_name", ""),
                "last_name": user_info.get("last_name", ""),
                "profile_picture": avatar_url,
                "oauth_provider": provider,
                "oauth_id": str(user_info.get("id"))
            }
        else:
            raise ValueError(f"Provider {provider} not supported for standardization")