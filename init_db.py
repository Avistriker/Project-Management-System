import os
import sys
sys.path.append('.')

from app import app, db

def init_database():
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # You can add initial data here if needed
            print("✅ Database initialization completed!")
            
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            sys.exit(1)

if __name__ == '__main__':
    init_database()
