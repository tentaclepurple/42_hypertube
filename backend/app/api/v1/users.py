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
    """
    Update user profile
    """
    try:
        # Use user_id from the authenticated user
        user_id = current_user["id"]

        # Verify that favorite_movie_id and worst_movie_id exist in the movies table
        movie_ids = [
            profile_data.favorite_movie_id,
            profile_data.worst_movie_id
        ]
        
        # Filter out None values
        valid_movie_ids = [id for id in movie_ids if id is not None]
        
        if valid_movie_ids:
            async with get_db_connection() as conn:
                # Verify that all referenced movies exist
                for movie_id in valid_movie_ids:
                    movie_exists = await conn.fetchval(
                        "SELECT EXISTS(SELECT 1 FROM movies WHERE id = $1)",
                        movie_id
                    )
                    if not movie_exists:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Movie with ID {movie_id} does not exist"
                        )

        # Use existing profile picture
        profile_picture_url = current_user.get("profile_picture", "")

        # If no profile picture, assign a default one
        if not profile_picture_url:
            profile_picture_url = "https://ujbctboiqjsoskaflslz.supabase.co/storage/v1/object/public/profile_images//burp.png"
        
        # Verify if email is already in use (if provided)
        if profile_data.email and profile_data.email != current_user["email"]:
            async with get_db_connection() as conn:
                email_exists = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM users WHERE email = $1 AND id != $2)",
                    profile_data.email, user_id
                )
                
                if email_exists:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email is already in use by another account"
                    )
        
        # Update the user profile in the database
        async with get_db_connection() as conn:
            # Verify if this is the first time the profile is being completed
            is_profile_completed = await conn.fetchval(
                "SELECT profile_completed FROM users WHERE id = $1",
                user_id
            )
            
            # Preparare data for update
            update_data = {
                "birth_year": profile_data.birth_year,
                "gender": profile_data.gender,
                "favorite_movie_id": profile_data.favorite_movie_id,
                "worst_movie_id": profile_data.worst_movie_id,
                "profile_picture": profile_picture_url,
                "updated_at": datetime.now()
            }
            
            # Add optional fields if provided
            if profile_data.email:
                update_data["email"] = profile_data.email
            
            if profile_data.first_name:
                update_data["first_name"] = profile_data.first_name
                
            if profile_data.last_name:
                update_data["last_name"] = profile_data.last_name
            
            # Verify if profile is now complete
            profile_is_complete = all([
                profile_data.birth_year,
                profile_data.gender,
                profile_data.favorite_movie_id,
                profile_data.worst_movie_id
            ])
            
            if profile_is_complete:
                update_data["profile_completed"] = True
            
            # Build the SET clause dynamically
            set_clauses = ", ".join([f"{key} = ${i+1}" for i, key in enumerate(update_data.keys())])
            values = list(update_data.values())

            # Add user_id as last parameter
            query = f"UPDATE users SET {set_clauses} WHERE id = ${len(values)+1} RETURNING *"
            values.append(user_id)

            # Execute the update
            updated_user = await conn.fetchrow(query, *values)
            
            if not updated_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # Verify if all required fields are completed
            if not profile_is_complete:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Profile update successful but some required fields are missing"
                )

            # Convert the updated user record to a dictionary and return
            return {
                "id": str(updated_user["id"]),
                "username": updated_user["username"],
                "email": updated_user["email"],
                "first_name": updated_user["first_name"],
                "last_name": updated_user["last_name"],
                "profile_picture": updated_user["profile_picture"],
                "birth_year": updated_user["birth_year"],
                "gender": updated_user["gender"],
                "favorite_movie_id": str(updated_user["favorite_movie_id"]) if updated_user["favorite_movie_id"] else None,
                "worst_movie_id": str(updated_user["worst_movie_id"]) if updated_user["worst_movie_id"] else None,
                "profile_completed": updated_user["profile_completed"],
                "message": "Profile updated successfully"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating profile: {str(e)}"
        )


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