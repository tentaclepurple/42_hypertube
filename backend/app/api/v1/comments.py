# backend/app/api/v1/comments.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List
import uuid
from datetime import datetime

from app.api.deps import get_current_user
from app.db.session import get_db_connection
from app.models.comment import (
    CommentCreate, 
    CommentUpdate, 
    CommentListResponse, 
    CommentDetailResponse,
    CommentResponse
)
from app.services.comment_queries import (
    GET_LATEST_COMMENTS,
    GET_COMMENT_BY_ID,
    GET_COMMENT_FOR_OWNER,
    CREATE_COMMENT,
    UPDATE_COMMENT,
    DELETE_COMMENT,
    CHECK_MOVIE_EXISTS,
    GET_MOVIE_COMMENTS,
    CHECK_USER_CAN_COMMENT
)

router = APIRouter()


@router.get("/", response_model=List[CommentListResponse])
async def get_latest_comments(
    limit: int = Query(20, ge=1, le=100, description="Number of comments to return"),
    offset: int = Query(0, ge=0, description="Number of comments to skip"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get latest comments with author username, date, content, and id
    """
    try:
        async with get_db_connection() as conn:
            comments = await conn.fetch(GET_LATEST_COMMENTS, limit, offset)
            
            return [
                CommentListResponse(
                    id=str(comment["id"]),
                    comment=comment["comment"],
                    rating=comment["rating"],
                    username=comment["username"],
                    created_at=comment["created_at"]
                )
                for comment in comments
            ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving comments: {str(e)}"
        )


@router.get("/{comment_id}", response_model=CommentDetailResponse)
async def get_comment_by_id(
    comment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get specific comment by ID with author's username, comment id, and date posted
    """
    try:
        comment_uuid = uuid.UUID(comment_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid comment ID format"
        )
    
    try:
        async with get_db_connection() as conn:
            comment = await conn.fetchrow(GET_COMMENT_BY_ID, comment_uuid)
            
            if not comment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Comment not found"
                )
            
            return CommentDetailResponse(
                id=str(comment["id"]),
                comment=comment["comment"],
                rating=comment["rating"],
                username=comment["username"],
                created_at=comment["created_at"]
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving comment: {str(e)}"
        )


@router.patch("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: str,
    comment_data: CommentUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update comment - only the owner can update their comment
    """
    try:
        comment_uuid = uuid.UUID(comment_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid comment ID format"
        )
    
    try:
        user_id = current_user["id"]
        
        async with get_db_connection() as conn:
            # Check if comment exists and belongs to the user
            existing_comment = await conn.fetchrow(GET_COMMENT_FOR_OWNER, comment_uuid)
            
            if not existing_comment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Comment not found"
                )
            
            if str(existing_comment["user_id"]) != str(user_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only update your own comments"
                )
            
            # Update the comment - use existing rating if not provided
            rating_to_update = comment_data.rating if comment_data.rating is not None else existing_comment["rating"]
            
            updated_comment = await conn.fetchrow(
                UPDATE_COMMENT,
                comment_uuid,
                comment_data.comment,
                rating_to_update,
                datetime.now(),
                user_id
            )
            
            if not updated_comment:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update comment"
                )
            
            return CommentResponse(
                id=str(updated_comment["id"]),
                user_id=str(updated_comment["user_id"]),
                movie_id=str(updated_comment["movie_id"]),
                comment=updated_comment["comment"],
                rating=updated_comment["rating"],
                username=existing_comment["username"],
                created_at=updated_comment["created_at"],
                updated_at=updated_comment["updated_at"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating comment: {str(e)}"
        )


@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete comment - only the owner can delete their comment
    """
    try:
        comment_uuid = uuid.UUID(comment_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid comment ID format"
        )
    
    try:
        user_id = current_user["id"]
        
        async with get_db_connection() as conn:
            # Check if comment exists and belongs to the user
            existing_comment = await conn.fetchrow(GET_COMMENT_FOR_OWNER, comment_uuid)
            
            if not existing_comment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Comment not found"
                )
            
            if str(existing_comment["user_id"]) != str(user_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only delete your own comments"
                )
            
            # Delete the comment
            deleted_comment = await conn.fetchrow(DELETE_COMMENT, comment_uuid, user_id)
            
            if not deleted_comment:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete comment"
                )
            
            return {"message": "Comment deleted successfully"}
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting comment: {str(e)}"
        )


@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment_data: CommentCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create new comment - only users who have watched the movie can comment
    """
    try:
        user_id = current_user["id"]
        
        async with get_db_connection() as conn:
            # Check if movie exists
            movie_exists = await conn.fetchval(CHECK_MOVIE_EXISTS, comment_data.movie_id)
            
            if not movie_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Movie not found"
                )
            
            # Check if user has watched enough of the movie to comment (10% minimum)
            can_comment = await conn.fetchval(CHECK_USER_CAN_COMMENT, user_id, comment_data.movie_id)
            
            if not can_comment:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You need to watch at least 10% of the movie to comment on it"
                )
            
            # Create the comment
            comment_id = uuid.uuid4()
            now = datetime.now()
            
            new_comment = await conn.fetchrow(
                CREATE_COMMENT,
                comment_id,
                user_id,
                comment_data.movie_id,
                comment_data.comment,
                comment_data.rating,
                now
            )
            
            if not new_comment:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create comment"
                )
            
            return CommentResponse(
                id=str(new_comment["id"]),
                user_id=str(new_comment["user_id"]),
                movie_id=str(new_comment["movie_id"]),
                comment=new_comment["comment"],
                rating=new_comment["rating"],
                username=current_user["username"],
                created_at=new_comment["created_at"],
                updated_at=new_comment["updated_at"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating comment: {str(e)}"
        )


# Alternative endpoint for creating comments under movies
@router.post("/movies/{movie_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_movie_comment(
    movie_id: str,
    comment_data: CommentCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create new comment for a specific movie
    """
    try:
        movie_uuid = uuid.UUID(movie_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid movie ID format"
        )
    
    # Override the movie_id from the URL
    comment_data.movie_id = movie_uuid
    
    # Use the same logic as create_comment
    return await create_comment(comment_data, current_user)


@router.get("/movies/{movie_id}/comments", response_model=List[CommentListResponse])
async def get_movie_comments(
    movie_id: str,
    limit: int = Query(20, ge=1, le=100, description="Number of comments to return"),
    offset: int = Query(0, ge=0, description="Number of comments to skip"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get comments for a specific movie
    """
    try:
        movie_uuid = uuid.UUID(movie_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid movie ID format"
        )
    
    try:
        async with get_db_connection() as conn:
            # Check if movie exists
            movie_exists = await conn.fetchval(CHECK_MOVIE_EXISTS, movie_uuid)
            if not movie_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Movie not found"
                )
            
            comments = await conn.fetch(GET_MOVIE_COMMENTS, movie_uuid, limit, offset)
            
            return [
                CommentListResponse(
                    id=str(comment["id"]),
                    comment=comment["comment"],
                    rating=comment["rating"],
                    username=comment["username"],
                    created_at=comment["created_at"]
                )
                for comment in comments
            ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving movie comments: {str(e)}"
        )