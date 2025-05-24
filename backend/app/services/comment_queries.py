# backend/app/services/comment_queries.py

# Get latest comments with user info
GET_LATEST_COMMENTS = """
    SELECT 
        mc.id,
        mc.comment,
        mc.rating,
        mc.created_at,
        u.username
    FROM movie_comments mc
    JOIN users u ON mc.user_id = u.id
    ORDER BY mc.created_at DESC
    LIMIT $1 OFFSET $2
"""

# Get specific comment by ID with user info
GET_COMMENT_BY_ID = """
    SELECT 
        mc.id,
        mc.comment,
        mc.rating,
        mc.created_at,
        u.username
    FROM movie_comments mc
    JOIN users u ON mc.user_id = u.id
    WHERE mc.id = $1
"""

# Get comment by ID for the owner (includes user_id for verification)
GET_COMMENT_FOR_OWNER = """
    SELECT 
        mc.id,
        mc.user_id,
        mc.movie_id,
        mc.comment,
        mc.rating,
        mc.created_at,
        mc.updated_at,
        u.username
    FROM movie_comments mc
    JOIN users u ON mc.user_id = u.id
    WHERE mc.id = $1
"""

# Create new comment
CREATE_COMMENT = """
    INSERT INTO movie_comments (id, user_id, movie_id, comment, rating, created_at, updated_at)
    VALUES ($1, $2, $3, $4, $5, $6, $6)
    RETURNING id, user_id, movie_id, comment, rating, created_at, updated_at
"""

# Update comment
UPDATE_COMMENT = """
    UPDATE movie_comments 
    SET comment = $2, rating = $3, updated_at = $4
    WHERE id = $1 AND user_id = $5
    RETURNING id, user_id, movie_id, comment, rating, created_at, updated_at
"""

# Delete comment
DELETE_COMMENT = """
    DELETE FROM movie_comments 
    WHERE id = $1 AND user_id = $2
    RETURNING id
"""

# Check if user has watched enough of the movie to comment (10% minimum)
CHECK_USER_CAN_COMMENT = """
    SELECT EXISTS(
        SELECT 1 FROM user_movie_views 
        WHERE user_id = $1 AND movie_id = $2 AND view_percentage >= 10.0
    )
"""

# Alternative check if you don't have a viewing history table yet
# This assumes any interaction with the movie (like downloading) counts as "watching"
CHECK_MOVIE_EXISTS = """
    SELECT EXISTS(SELECT 1 FROM movies WHERE id = $1)
"""

# Get comments for a specific movie
GET_MOVIE_COMMENTS = """
    SELECT 
        mc.id,
        mc.comment,
        mc.rating,
        mc.created_at,
        u.username
    FROM movie_comments mc
    JOIN users u ON mc.user_id = u.id
    WHERE mc.movie_id = $1
    ORDER BY mc.created_at DESC
    LIMIT $2 OFFSET $3
"""