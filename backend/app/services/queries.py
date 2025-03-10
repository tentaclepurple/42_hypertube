insert_user = """
                INSERT INTO users 
                (id, email, username, password, first_name, last_name, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $7)
                RETURNING id, email, username, first_name, last_name, created_at
                """

get_popular = """
                SELECT 
                    id, imdb_id, title, year, imdb_rating, genres, summary,
                    cover_image, director, casting, torrents
                FROM movies
                WHERE imdb_rating IS NOT NULL
                ORDER BY imdb_rating DESC
                LIMIT $1 OFFSET $2
                """

insert_movie = """
                INSERT INTO movies 
                (id, imdb_id, title, title_lower, year, imdb_rating, genres, 
                summary, cover_image, director, casting, 
                torrents, added_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                ON CONFLICT (imdb_id) DO NOTHING
                """

