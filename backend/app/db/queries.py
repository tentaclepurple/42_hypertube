create_users_table= '''
                CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255),  -- can be NULL for OAuth users
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                profile_picture VARCHAR(255),
                oauth_provider VARCHAR(20),    -- 'google', 'github', '42' or NULL
                oauth_id VARCHAR(100),         -- Unique ID OAuth
                profile_completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                
                CONSTRAINT unique_oauth UNIQUE (oauth_provider, oauth_id)
            );
            '''

create_users_idx = '''
                CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
                CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);
            '''

create_movies_table = '''
				CREATE TABLE IF NOT EXISTS movies (
				id UUID PRIMARY KEY,
				imdb_id VARCHAR(20) UNIQUE NOT NULL,
				title VARCHAR(255) NOT NULL,
				year INTEGER,
				rating REAL,
				runtime INTEGER,
				genres VARCHAR(255)[],
				summary TEXT,
				poster VARCHAR(255),
				trailer VARCHAR(255),
				torrents JSONB,
				created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
				updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
			);
			'''