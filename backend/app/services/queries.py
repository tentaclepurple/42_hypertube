insert_user = """
                INSERT INTO users 
                (id, email, username, password, first_name, last_name, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $7)
                RETURNING id, email, username, first_name, last_name, created_at
                """