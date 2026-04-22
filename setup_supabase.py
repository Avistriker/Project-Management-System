"""
Database setup script for Supabase PostgreSQL
Run this once after creating your Supabase project
"""

import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import urllib.parse

load_dotenv()

def get_connection():
    """Create database connection to Supabase"""
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'postgres')
    
    # URL encode password for special characters
    encoded_password = urllib.parse.quote_plus(db_password)
    
    print(f"Connecting to Supabase at {db_host}:{db_port}")
    
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
            sslmode='require'
        )
        conn.autocommit = True
        print("✅ Connected to Supabase successfully!")
        return conn
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

def create_tables(conn):
    """Create all tables in Supabase"""
    cursor = conn.cursor()
    
    tables = [
        # User table
        """
        CREATE TABLE IF NOT EXISTS "user" (
            id SERIAL PRIMARY KEY,
            email VARCHAR(120) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # Student group table
        """
        CREATE TABLE IF NOT EXISTS student_group (
            id SERIAL PRIMARY KEY,
            name VARCHAR(20) UNIQUE NOT NULL,
            supervisor_id INTEGER,
            project_title VARCHAR(255),
            project_description TEXT,
            document_link VARCHAR(500),
            whatsapp_link VARCHAR(500),
            branch VARCHAR(50) NOT NULL,
            year VARCHAR(10) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # Student table
        """
        CREATE TABLE IF NOT EXISTS student (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
            name VARCHAR(100) NOT NULL,
            roll_number VARCHAR(20) UNIQUE NOT NULL,
            year VARCHAR(10) NOT NULL,
            school VARCHAR(100) NOT NULL,
            branch VARCHAR(50) NOT NULL,
            phone_number VARCHAR(15),
            mentor_name VARCHAR(100),
            mentor_phone VARCHAR(15),
            mentor_email VARCHAR(120),
            group_id INTEGER REFERENCES student_group(id) ON DELETE SET NULL
        )
        """,
        
        # Supervisor table
        """
        CREATE TABLE IF NOT EXISTS supervisor (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
            name VARCHAR(100) NOT NULL,
            domain VARCHAR(100) NOT NULL,
            school VARCHAR(100) NOT NULL,
            phone_number VARCHAR(15),
            max_groups INTEGER DEFAULT 3,
            priority INTEGER DEFAULT 1
        )
        """,
        
        # FIC table
        """
        CREATE TABLE IF NOT EXISTS fic (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
            name VARCHAR(100) NOT NULL,
            school VARCHAR(100) NOT NULL,
            phone_number VARCHAR(15)
        )
        """,
        
        # Group invite table
        """
        CREATE TABLE IF NOT EXISTS group_invite (
            id SERIAL PRIMARY KEY,
            sender_id INTEGER NOT NULL REFERENCES student(id) ON DELETE CASCADE,
            receiver_id INTEGER NOT NULL REFERENCES student(id) ON DELETE CASCADE,
            status VARCHAR(20) DEFAULT 'pending',
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # Supervisor request table
        """
        CREATE TABLE IF NOT EXISTS supervisor_request (
            id SERIAL PRIMARY KEY,
            group_id INTEGER NOT NULL REFERENCES student_group(id) ON DELETE CASCADE,
            supervisor_id INTEGER NOT NULL REFERENCES supervisor(id) ON DELETE CASCADE,
            status VARCHAR(20) DEFAULT 'pending',
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # Supervisor change request table
        """
        CREATE TABLE IF NOT EXISTS supervisor_change_request (
            id SERIAL PRIMARY KEY,
            group_id INTEGER NOT NULL REFERENCES student_group(id) ON DELETE CASCADE,
            current_supervisor_id INTEGER NOT NULL REFERENCES supervisor(id) ON DELETE CASCADE,
            new_supervisor_id INTEGER NOT NULL REFERENCES supervisor(id) ON DELETE CASCADE,
            status VARCHAR(20) DEFAULT 'pending',
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP
        )
        """,
        
        # Panel table
        """
        CREATE TABLE IF NOT EXISTS panel (
            id SERIAL PRIMARY KEY,
            panel_number VARCHAR(20) UNIQUE NOT NULL,
            group_id INTEGER NOT NULL REFERENCES student_group(id) ON DELETE CASCADE,
            created_by INTEGER NOT NULL REFERENCES fic(id) ON DELETE CASCADE,
            phase VARCHAR(20) DEFAULT 'Phase 1',
            evaluation_date DATE,
            evaluation_time TIME,
            venue VARCHAR(200),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # Panel member table
        """
        CREATE TABLE IF NOT EXISTS panel_member (
            id SERIAL PRIMARY KEY,
            panel_id INTEGER NOT NULL REFERENCES panel(id) ON DELETE CASCADE,
            supervisor_id INTEGER NOT NULL REFERENCES supervisor(id) ON DELETE CASCADE
        )
        """,
        
        # Evaluation table
        """
        CREATE TABLE IF NOT EXISTS evaluation (
            id SERIAL PRIMARY KEY,
            panel_id INTEGER NOT NULL REFERENCES panel(id) ON DELETE CASCADE,
            group_id INTEGER NOT NULL REFERENCES student_group(id) ON DELETE CASCADE,
            evaluator_id INTEGER NOT NULL REFERENCES supervisor(id) ON DELETE CASCADE,
            presentation_marks DECIMAL(5,2) DEFAULT 0,
            documentation_marks DECIMAL(5,2) DEFAULT 0,
            collaboration_marks DECIMAL(5,2) DEFAULT 0,
            innovation_marks DECIMAL(5,2) DEFAULT 0,
            total_marks DECIMAL(6,2) DEFAULT 0,
            feedback_to_students TEXT,
            feedback_to_supervisor TEXT,
            evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # Marks table
        """
        CREATE TABLE IF NOT EXISTS marks (
            id SERIAL PRIMARY KEY,
            student_id INTEGER NOT NULL REFERENCES student(id) ON DELETE CASCADE,
            presentation DECIMAL(4,2) DEFAULT 0,
            documents DECIMAL(4,2) DEFAULT 0,
            collaboration DECIMAL(4,2) DEFAULT 0,
            total DECIMAL(5,2) DEFAULT 0,
            given_by INTEGER NOT NULL REFERENCES supervisor(id) ON DELETE CASCADE,
            given_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # OTP table
        """
        CREATE TABLE IF NOT EXISTS otp (
            id SERIAL PRIMARY KEY,
            email VARCHAR(120) NOT NULL,
            otp VARCHAR(6) NOT NULL,
            purpose VARCHAR(20) DEFAULT 'registration',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            used BOOLEAN DEFAULT FALSE
        )
        """,
        
        # Notification table
        """
        CREATE TABLE IF NOT EXISTS notification (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            message TEXT NOT NULL,
            target_type VARCHAR(20) NOT NULL,
            target_branch VARCHAR(50),
            created_by INTEGER NOT NULL REFERENCES fic(id) ON DELETE CASCADE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    ]
    
    print("\n📝 Creating tables...")
    
    for table_sql in tables:
        try:
            cursor.execute(table_sql)
        except Exception as e:
            print(f"  ⚠️ Table may already exist or error: {e}")
    
    # Add foreign key constraints
    try:
        cursor.execute("""
            ALTER TABLE student_group 
            ADD CONSTRAINT IF NOT EXISTS fk_group_supervisor 
            FOREIGN KEY (supervisor_id) REFERENCES supervisor(id) ON DELETE SET NULL
        """)
    except Exception as e:
        print(f"  ⚠️ Foreign key constraint may already exist: {e}")
    
    cursor.close()
    print("✅ All tables created/verified successfully!")

def main():
    print("=" * 60)
    print("SUPABASE DATABASE SETUP")
    print("=" * 60)
    
    conn = get_connection()
    if not conn:
        print("\n❌ Failed to connect. Please check your environment variables.")
        print("\nMake sure you have set:")
        print("  DB_USER=postgres.YOUR_PROJECT_ID")
        print("  DB_PASSWORD=your_password")
        print("  DB_HOST=aws-0-ap-south-1.pooler.supabase.com")
        print("  DB_PORT=5432")
        print("  DB_NAME=postgres")
        return
    
    create_tables(conn)
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ DATABASE SETUP COMPLETED!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Deploy to Render")
    print("2. Set environment variables in Render")
    print("3. Your app should be ready to use!")

if __name__ == "__main__":
    main()
