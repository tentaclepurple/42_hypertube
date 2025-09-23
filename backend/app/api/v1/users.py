# backend/app/api/v1/users.py


from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, status, Request
from app.api.deps import get_current_user
from app.db.session import get_db_connection
from app.services.supabase_services import supabase_service
from app.models.users import ProfileUpdate, UserProfile, PublicUserProfile
from datetime import datetime
from .queries import get_movie_comments, get_user_profile, movies_query, comments_query, user_query
from pprint import pprint


router = APIRouter()


@router.put("/profile")
@router.patch("/profile")
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = current_user["id"]

        if not profile_data.first_name.strip():
            raise HTTPException(400, "First name is required")
        
        if not profile_data.last_name.strip():
            raise HTTPException(400, "Last name is required")
        
        if not profile_data.email.strip():
            raise HTTPException(400, "Email is required")
            
        if profile_data.email != profile_data.email_confirm:
            raise HTTPException(400, "Email addresses do not match")

        if profile_data.email != current_user["email"]:
            async with get_db_connection() as conn:
                email_exists = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM users WHERE email = $1 AND id != $2)",
                    profile_data.email, user_id
                )
                if email_exists:
                    raise HTTPException(400, "Email is already in use by another account")

        profile_picture_url = current_user.get("profile_picture", "")
        if not profile_picture_url:
            profile_picture_url = "https://ujbctboiqjsoskaflslz.supabase.co/storage/v1/object/public/profile_images//burp.png"

        async with get_db_connection() as conn:
            update_data = {
                "first_name": profile_data.first_name.strip(),
                "last_name": profile_data.last_name.strip(), 
                "email": profile_data.email.strip(),
                "birth_year": profile_data.birth_year,
                "gender": profile_data.gender,
                "profile_picture": profile_picture_url,
                "profile_completed": True,
                "updated_at": datetime.now()
            }

            set_clauses = ", ".join([f"{key} = ${i+1}" for i, key in enumerate(update_data.keys())])
            values = list(update_data.values())
            values.append(user_id)

            query = f"UPDATE users SET {set_clauses} WHERE id = ${len(values)} RETURNING *"
            updated_user = await conn.fetchrow(query, *values)
            
            if not updated_user:
                raise HTTPException(404, "User not found")

            return {
                "id": str(updated_user["id"]),
                "username": updated_user["username"],
                "email": updated_user["email"],
                "first_name": updated_user["first_name"],
                "last_name": updated_user["last_name"],
                "profile_picture": updated_user["profile_picture"],
                "birth_year": updated_user["birth_year"],
                "gender": updated_user["gender"],
                "profile_completed": updated_user["profile_completed"],
                "comments": [],
                "message": "Profile updated successfully"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error updating profile: {str(e)}")


@router.put("/profile/image")
async def update_profile_image(
    profile_picture: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
    ):
    """
    Update user profile picture
    """
    try:
        user_id = current_user["id"]
        
        try:
            file_content = await profile_picture.read()
            print(f"Read file content, size: {len(file_content)} bytes", flush=True)
        except Exception as e:
            print(f"Error reading file: {e}", flush=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error reading uploaded file: {str(e)}"
            )
        
        try:
            profile_picture_url = await supabase_service.update_profile_picture(
                file_content,
                str(user_id)
            )
            
            if not profile_picture_url:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to upload profile picture"
                )
        except Exception as e:
            print(f"Error uploading to Supabase: {e}", flush=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error uploading profile picture: {str(e)}"
            )
        
        try:
            async with get_db_connection() as conn:
                updated_user = await conn.fetchrow(
                    "UPDATE users SET profile_picture = $1, updated_at = $2 WHERE id = $3 RETURNING id, profile_picture",
                    profile_picture_url, datetime.now(), user_id
                )
                
                if not updated_user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="User not found"
                    )
                
                print(f"Updated user record with new profile picture", flush=True)
        except Exception as e:
            print(f"Database error: {e}", flush=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating user record: {str(e)}"
            )
        
        return {
            "profile_picture": profile_picture_url,
            "message": "Profile picture updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error: {e}", flush=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating profile picture: {str(e)}"
        )



@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """
    Gets the current user's profile information along with their comments and favorite movies
    """
    try:
        user_id = current_user["id"]
        
        async with get_db_connection() as conn:
            user = await conn.fetchrow(get_user_profile, user_id)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            comments = await conn.fetch(get_movie_comments, user_id)
            
            favorite_movies = {}
            movie_ids = []
            
            if user['favorite_movie_id']:
                movie_ids.append(user['favorite_movie_id'])
            if user['worst_movie_id']:
                movie_ids.append(user['worst_movie_id'])
            
            if movie_ids:
                movies_data = await conn.fetch("""
                    SELECT id, title, year, cover_image, imdb_rating
                    FROM movies
                    WHERE id = ANY($1)
                """, movie_ids)
                
                for movie in movies_data:
                    favorite_movies[str(movie['id'])] = {
                        'id': str(movie['id']),
                        'title': movie['title'],
                        'year': movie['year'],
                        'cover_image': movie['cover_image'],
                        'imdb_rating': movie['imdb_rating']
                    }
            
            user_dict = dict(user)
            comments_list = [dict(comment) for comment in comments]
            
            user_dict["id"] = str(user_dict["id"])
            
            for comment in comments_list:
                comment["id"] = str(comment["id"])
                comment["movie_id"] = str(comment["movie_id"])
            
            user_dict["comments"] = comments_list
            
            if user_dict.get('favorite_movie_id') and str(user_dict['favorite_movie_id']) in favorite_movies:
                user_dict['favorite_movie'] = favorite_movies[str(user_dict['favorite_movie_id'])]
            else:
                user_dict['favorite_movie'] = None
                
            if user_dict.get('worst_movie_id') and str(user_dict['worst_movie_id']) in favorite_movies:
                user_dict['worst_movie'] = favorite_movies[str(user_dict['worst_movie_id'])]
            else:
                user_dict['worst_movie'] = None
            
            user_dict.pop('favorite_movie_id', None)
            user_dict.pop('worst_movie_id', None)
            
            return user_dict
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error retrieving user profile: {str(e)}", flush=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user profile: {str(e)}")
    

@router.get("/{username}", response_model=PublicUserProfile)
async def get_user_profile_by_username(username: str):
    """
    Gets a user's public profile information by username along with their comments and favorite movies
    """
    try:
        async with get_db_connection() as conn:

            user = await conn.fetchrow(user_query, username)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            comments = await conn.fetch(comments_query, user['id'])
            
            favorite_movies = {}
            movie_ids = []
            
            if user['favorite_movie_id']:
                movie_ids.append(user['favorite_movie_id'])
            if user['worst_movie_id']:
                movie_ids.append(user['worst_movie_id'])
            
            if movie_ids:

                movies_data = await conn.fetch(movies_query, movie_ids)
                
                for movie in movies_data:
                    favorite_movies[str(movie['id'])] = {
                        'id': str(movie['id']),
                        'title': movie['title'],
                        'year': movie['year'],
                        'cover_image': movie['cover_image'],
                        'imdb_rating': movie['imdb_rating']
                    }
            
            user_dict = dict(user)
            comments_list = [dict(comment) for comment in comments]
            
            user_dict["id"] = str(user_dict["id"])
            
            for comment in comments_list:
                comment["id"] = str(comment["id"])
                comment["movie_id"] = str(comment["movie_id"])
            
            user_dict["comments"] = comments_list
            
            if user_dict.get('favorite_movie_id') and str(user_dict['favorite_movie_id']) in favorite_movies:
                user_dict['favorite_movie'] = favorite_movies[str(user_dict['favorite_movie_id'])]
            else:
                user_dict['favorite_movie'] = None
                
            if user_dict.get('worst_movie_id') and str(user_dict['worst_movie_id']) in favorite_movies:
                user_dict['worst_movie'] = favorite_movies[str(user_dict['worst_movie_id'])]
            else:
                user_dict['worst_movie'] = None
            
            user_dict.pop('favorite_movie_id', None)
            user_dict.pop('worst_movie_id', None)
            
            return user_dict
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error retrieving user profile: {str(e)}", flush=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user profile: {str(e)}"
        )