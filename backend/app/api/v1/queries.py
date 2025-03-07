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