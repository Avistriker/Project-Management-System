import os
import psycopg2
from urllib.parse import urlparse

def setup_railway_database():
    # Get database URL from Railway environment
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("No DATABASE_URL found in environment variables")
        return
    
    # Parse the database URL
    result = urlparse(database_url)
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )
        
        print("Connected to Railway PostgreSQL database successfully!")
        
        # Your existing database setup logic here
        # You'll need to adapt your MySQL schema to PostgreSQL
        
        conn.close()
        
    except Exception as e:
        print(f"Error setting up database: {e}")

if __name__ == "__main__":
    setup_railway_database()
