import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = 'password'  # Set your MySQL password here
    MYSQL_DB = 'project_management_system'
    MYSQL_PORT = 3306