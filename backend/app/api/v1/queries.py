update_existing_user = """
                    UPDATE users 
                    SET first_name = $1, last_name = $2, profile_picture = $3, updated_at = $4
                    WHERE oauth_provider = $5 AND oauth_id = $6
                    """

update_existing_email = """
                        UPDATE users 
                        SET oauth_provider = $1, oauth_id = $2, 
                            first_name = $3, last_name = $4, 
                            profile_picture = $5, updated_at = $6
                        WHERE email = $7
                        """

insert_new_user = """
					INSERT INTO users 
					(id, email, username, first_name, last_name, profile_picture, 
						oauth_provider, oauth_id, created_at, updated_at)
					VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $9)
					RETURNING id, email, username, first_name, last_name, 
								profile_picture, created_at
					"""

get_movie_comments = """
                SELECT 
                    mc.id, 
                    mc.movie_id, 
                    m.title as movie_title, 
                    mc.comment, 
                    mc.rating, 
                    mc.created_at,
                    mc.updated_at
                FROM 
                    movie_comments mc
                JOIN 
                    movies m ON mc.movie_id = m.id
                WHERE 
                    mc.user_id = $1
                ORDER BY 
                    mc.created_at DESC
            """


get_user_profile = """  
                SELECT 
                    id, email, username, first_name, last_name, profile_picture,
                    birth_year, gender, favorite_movie_id, worst_movie_id,
                    created_at, updated_at
                FROM 
                    users
                WHERE 
                    id = $1
            """

movies_query = """
                    SELECT 
                        m.id, 
                        m.title, 
                        m.year, 
                        m.cover_image, 
                        m.imdb_rating
                    FROM 
                        movies m
                    WHERE 
                        m.id = ANY($1)
                """


comments_query = """
                SELECT 
                    mc.id, 
                    mc.movie_id, 
                    m.title as movie_title, 
                    mc.comment, 
                    mc.rating, 
                    mc.created_at,
                    mc.updated_at
                FROM 
                    movie_comments mc
                JOIN 
                    movies m ON mc.movie_id = m.id
                WHERE 
                    mc.user_id = $1
                ORDER BY 
                    mc.created_at DESC
            """

user_query = """
                SELECT 
                    u.id, u.username, u.first_name, u.last_name, 
                    u.profile_picture, u.birth_year, u.gender,
                    u.favorite_movie_id, u.worst_movie_id, 
                    u.profile_completed, u.created_at, u.updated_at
                FROM 
                    users u
                WHERE 
                    u.username = $1
            """