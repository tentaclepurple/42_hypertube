# backend/app/services/supabase_services.py

import os
import requests
import uuid
from supabase import create_client
from io import BytesIO

class SupabaseService:
    """Service for interacting with Supabase"""
    
    def __init__(self):
        self.supabase_url = os.environ.get("SUPABASE_URL")
        self.supabase_key = os.environ.get("SUPABASE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL and key must be provided in environment variables")
        
        self.client = create_client(self.supabase_url, self.supabase_key)
    
    async def update_profile_picture(self, image_data, user_id):
        """
        Upload profile picture to Supabase storage
        
        Args:
            image_data (bytes): Binary image data
            user_id (str): ID of the user
            
        Returns:
            str: Public URL of the uploaded image
        """
        try:
            if not image_data:
                return ""
                
            # Generate unique filename
            file_ext = "jpg"  # Default extension
            filename = f"{user_id}_{uuid.uuid4().hex}.{file_ext}"
            
            print(f"Uploading profile picture: {filename}")
            
            # Upload to Supabase Storage
            result = self.client.storage.from_('profile_images').upload(
                filename,
                image_data,
                {"content-type": f"image/{file_ext}"}
            )
            
            # Get public URL
            public_url = self.client.storage.from_('profile_pictures').get_public_url(filename)
            
            return public_url
            
        except Exception as e:
            print(f"Error uploading profile picture: {str(e)}")
            raise e
    
    async def upload_profile_picture(self, image_url, user_id):
        """
        Download image from URL and upload to Supabase storage
        
        Args:
            image_url (str): URL of the profile picture
            user_id (str): ID of the user
            
        Returns:
            str: Public URL of the uploaded image
        """
        try:
            if not image_url:
                return ""
            # Download image from URL
            response = requests.get(image_url)
            if response.status_code != 200:
                print(f"Error downloading image from {image_url}: {response.status_code}")
                return ""
                
            image_data = BytesIO(response.content)
            
            # Generate unique filename
            file_ext = image_url.split('.')[-1] if '.' in image_url else 'jpg'
            if '?' in file_ext:  # Remove query parameters
                file_ext = file_ext.split('?')[0]
            
            # Ensure extension is valid
            valid_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
            if file_ext.lower() not in valid_extensions:
                file_ext = 'jpg'
                
            filename = f"{user_id}_{uuid.uuid4().hex}.{file_ext}"
            
            # Upload to Supabase Storage
            result = self.client.storage.from_('profile_images').upload(
                filename,
                image_data.getvalue(),
                {"content-type": f"image/{file_ext}"}
            )
            
            # Get public URL
            public_url = self.client.storage.from_('profile_pictures').get_public_url(filename)
            
            return public_url
            
        except Exception as e:
            print(f"Error uploading profile picture: {str(e)}")
            return ""


# Singleton instance
supabase_service = SupabaseService()