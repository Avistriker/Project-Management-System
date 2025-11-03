import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DatabaseSetup:
    def __init__(self):
        self.host = os.getenv('MYSQL_HOST', 'localhost')
        self.user = os.getenv('MYSQL_USER', 'root')
        self.password = os.getenv('MYSQL_PASSWORD', '')
        self.database = os.getenv('MYSQL_DB', 'project_management_system')
    
    def create_connection(self):
        """Create a database connection"""
        try:
            connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password
            )
            if connection.is_connected():
                print("Connected to MySQL server")
                return connection
        except Error as e:
            print(f"Error: {e}")
            return None
    
    def create_database(self, connection):
        """Create the database"""
        try:
            cursor = connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            print(f"Database '{self.database}' created successfully")
        except Error as e:
            print(f"Error creating database: {e}")
    
    def use_database(self, connection):
        """Use the specific database"""
        try:
            cursor = connection.cursor()
            cursor.execute(f"USE {self.database}")
            print(f"Using database: {self.database}")
        except Error as e:
            print(f"Error using database: {e}")
    
    def create_tables(self, connection):
        """Create all tables"""
        try:
            cursor = connection.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    role ENUM('student', 'supervisor', 'fic') NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("Table 'user' created successfully")
            
            # Student groups table (created first due to foreign key constraints)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS student_group (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(20) UNIQUE NOT NULL,
                    supervisor_id INT,
                    project_title VARCHAR(255),
                    project_description TEXT,
                    document_link VARCHAR(500),
                    branch ENUM(
                        'CS', 'ECS', 'IT', 'ETC', 
                        'Civil', 'Mech', 'Aerospace', 'EE'
                    ) NOT NULL,
                    year ENUM('Third', 'Fourth') NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("Table 'student_group' created successfully")
            
            # Students table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS student (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    roll_number VARCHAR(20) UNIQUE NOT NULL,
                    year ENUM('Third', 'Fourth') NOT NULL,
                    school ENUM(
                        'School of Electronics',
                        'School of Computer Science',
                        'School of Electrical',
                        'School of Civil',
                        'School of Mechanical',
                        'School of IT'
                    ) NOT NULL,
                    branch ENUM(
                        'CS', 'ECS', 'IT', 'ETC',
                        'Civil', 'Mech', 'Aerospace', 'EE'
                    ) NOT NULL,
                    group_id INT,
                    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
                    FOREIGN KEY (group_id) REFERENCES student_group(id) ON DELETE SET NULL
                )
            """)
            print("Table 'student' created successfully")
            
            # Supervisors table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS supervisor (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    domain ENUM('ML', 'IOT', 'ML & IOT', 'VLSI', 'Signals') NOT NULL,
                    school ENUM(
                        'School of Electronics',
                        'School of Computer Science',
                        'School of Electrical',
                        'School of Civil',
                        'School of Mechanical',
                        'School of IT'
                    ) NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
                )
            """)
            print("Table 'supervisor' created successfully")
            
            # FIC table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fic (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    school ENUM(
                        'School of Electronics',
                        'School of Computer Science',
                        'School of Electrical',
                        'School of Civil',
                        'School of Mechanical',
                        'School of IT'
                    ) NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
                )
            """)
            print("Table 'fic' created successfully")
            
            # Add foreign key constraint for student_group supervisor_id
            cursor.execute("""
                ALTER TABLE student_group 
                ADD CONSTRAINT fk_group_supervisor 
                FOREIGN KEY (supervisor_id) REFERENCES supervisor(id) ON DELETE SET NULL
            """)
            print("Foreign key constraint added to student_group")
            
            # Group invites table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS group_invite (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    sender_id INT NOT NULL,
                    receiver_id INT NOT NULL,
                    status ENUM('pending', 'accepted', 'rejected') DEFAULT 'pending',
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sender_id) REFERENCES student(id) ON DELETE CASCADE,
                    FOREIGN KEY (receiver_id) REFERENCES student(id) ON DELETE CASCADE
                )
            """)
            print("Table 'group_invite' created successfully")
            
            # Supervisor requests table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS supervisor_request (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    group_id INT NOT NULL,
                    supervisor_id INT NOT NULL,
                    status ENUM('pending', 'accepted', 'rejected') DEFAULT 'pending',
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (group_id) REFERENCES student_group(id) ON DELETE CASCADE,
                    FOREIGN KEY (supervisor_id) REFERENCES supervisor(id) ON DELETE CASCADE
                )
            """)
            print("Table 'supervisor_request' created successfully")
            
            # Supervisor change requests table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS supervisor_change_request (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    group_id INT NOT NULL,
                    current_supervisor_id INT NOT NULL,
                    new_supervisor_id INT NOT NULL,
                    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
                    reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP NULL,
                    FOREIGN KEY (group_id) REFERENCES student_group(id) ON DELETE CASCADE,
                    FOREIGN KEY (current_supervisor_id) REFERENCES supervisor(id) ON DELETE CASCADE,
                    FOREIGN KEY (new_supervisor_id) REFERENCES supervisor(id) ON DELETE CASCADE
                )
            """)
            print("Table 'supervisor_change_request' created successfully")
            
            # Panels table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS panel (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    group_id INT NOT NULL,
                    created_by INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (group_id) REFERENCES student_group(id) ON DELETE CASCADE,
                    FOREIGN KEY (created_by) REFERENCES fic(id) ON DELETE CASCADE
                )
            """)
            print("Table 'panel' created successfully")
            
            # Panel members table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS panel_member (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    panel_id INT NOT NULL,
                    supervisor_id INT NOT NULL,
                    FOREIGN KEY (panel_id) REFERENCES panel(id) ON DELETE CASCADE,
                    FOREIGN KEY (supervisor_id) REFERENCES supervisor(id) ON DELETE CASCADE
                )
            """)
            print("Table 'panel_member' created successfully")
            
            # Marks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS marks (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    student_id INT NOT NULL,
                    presentation DECIMAL(4,2) DEFAULT 0,
                    documents DECIMAL(4,2) DEFAULT 0,
                    collaboration DECIMAL(4,2) DEFAULT 0,
                    total DECIMAL(5,2) DEFAULT 0,
                    given_by INT NOT NULL,
                    given_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE,
                    FOREIGN KEY (given_by) REFERENCES supervisor(id) ON DELETE CASCADE
                )
            """)
            print("Table 'marks' created successfully")
            
            # OTP table (updated with purpose field)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS otp (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(120) NOT NULL,
                    otp VARCHAR(6) NOT NULL,
                    purpose ENUM('registration', 'password_reset') DEFAULT 'registration',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    used BOOLEAN DEFAULT FALSE
                )
            """)
            print("Table 'otp' created successfully")
            
            # Notifications table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notification (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    message TEXT NOT NULL,
                    target_type ENUM('all', 'students', 'supervisors', 'specific_branch') NOT NULL,
                    target_branch VARCHAR(50),
                    created_by INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES fic(id) ON DELETE CASCADE
                )
            """)
            print("Table 'notification' created successfully")
            
            # Remove password_reset_token table since we're using OTP method
            
            connection.commit()
            print("All tables created successfully!")
            
        except Error as e:
            print(f"Error creating tables: {e}")
            connection.rollback()
    
    def setup_database(self):
        """Complete database setup"""
        connection = self.create_connection()
        if connection:
            self.create_database(connection)
            self.use_database(connection)
            self.create_tables(connection)
            connection.close()
            print("Database setup completed successfully!")

if __name__ == "__main__":
    db_setup = DatabaseSetup()
    db_setup.setup_database()