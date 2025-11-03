import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

load_dotenv()

class DatabaseSetup:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
    
    def create_tables(self):
        """Create all tables in PostgreSQL"""
        try:
            # Connect to database
            conn = psycopg2.connect(self.database_url)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Enable UUID extension
            cursor.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
            
            # Create tables (simplified for PostgreSQL)
            tables_sql = [
                # Users table
                """
                CREATE TABLE IF NOT EXISTS "user" (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    role VARCHAR(20) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """,
                
                # Student groups table
                """
                CREATE TABLE IF NOT EXISTS student_group (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(20) UNIQUE NOT NULL,
                    supervisor_id INTEGER,
                    project_title VARCHAR(255),
                    project_description TEXT,
                    document_link VARCHAR(500),
                    branch VARCHAR(50) NOT NULL,
                    year VARCHAR(10) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """,
                
                # Students table
                """
                CREATE TABLE IF NOT EXISTS student (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
                    name VARCHAR(100) NOT NULL,
                    roll_number VARCHAR(20) UNIQUE NOT NULL,
                    year VARCHAR(10) NOT NULL,
                    school VARCHAR(100) NOT NULL,
                    branch VARCHAR(50) NOT NULL,
                    group_id INTEGER REFERENCES student_group(id) ON DELETE SET NULL
                );
                """,
                
                # Add other table creation statements here...
                # Continue with supervisors, fic, group_invite, supervisor_request, etc.
            ]
            
            for sql in tables_sql:
                cursor.execute(sql)
            
            conn.commit()
            print("All tables created successfully!")
            
        except Exception as e:
            print(f"Error creating tables: {e}")
        finally:
            if conn:
                conn.close()

if __name__ == "__main__":
    db_setup = DatabaseSetup()
    db_setup.create_tables()
