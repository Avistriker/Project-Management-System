from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets
import os
import json
import sqlite3
from contextlib import contextmanager
import tempfile

# Initialize Flask app
app = Flask(__name__, 
    template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates'),
    static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static')
)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-12345')
app.config['DATABASE_PATH'] = os.path.join(tempfile.gettempdir(), 'project_management.db')

# Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database setup
def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect(app.config['DATABASE_PATH'])
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Students table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            roll_number TEXT UNIQUE NOT NULL,
            year TEXT NOT NULL,
            school TEXT NOT NULL,
            branch TEXT NOT NULL,
            group_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Supervisors table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS supervisors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            domain TEXT NOT NULL,
            school TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # FIC table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fic (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            school TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Student groups table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            supervisor_id INTEGER,
            project_title TEXT,
            document_link TEXT,
            branch TEXT NOT NULL,
            year TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

@contextmanager
def get_db_connection():
    """Database connection context manager"""
    conn = sqlite3.connect(app.config['DATABASE_PATH'])
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

class User(UserMixin):
    def __init__(self, id, email, password, role, created_at):
        self.id = id
        self.email = email
        self.password = password
        self.role = role
        self.created_at = created_at

@login_manager.user_loader
def load_user(user_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user_data = cursor.fetchone()
        
        if user_data:
            return User(
                id=user_data['id'],
                email=user_data['email'],
                password=user_data['password'],
                role=user_data['role'],
                created_at=user_data['created_at']
            )
        return None

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            user_data = cursor.fetchone()
            
            if user_data and check_password_hash(user_data['password'], password):
                user = User(
                    id=user_data['id'],
                    email=user_data['email'],
                    password=user_data['password'],
                    role=user_data['role'],
                    created_at=user_data['created_at']
                )
                login_user(user)
                
                if user.role == 'student':
                    return redirect('/student/dashboard')
                elif user.role == 'supervisor':
                    return redirect('/supervisor/dashboard')
                elif user.role == 'fic':
                    return redirect('/fic/dashboard')
        
        flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form.get('role')
        
        if role == 'student':
            return redirect('/register/student')
        elif role == 'supervisor':
            return redirect('/register/supervisor')
        elif role == 'fic':
            return redirect('/register/fic')
    
    return render_template('register.html')

@app.route('/register/student', methods=['GET', 'POST'])
def student_registration():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        roll_number = request.form.get('roll_number')
        year = request.form.get('year')
        school = request.form.get('school')
        branch = request.form.get('branch')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('student_registration.html')
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if email exists
            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            if cursor.fetchone():
                flash('Email already registered', 'error')
                return render_template('student_registration.html')
            
            # Check if roll number exists
            cursor.execute('SELECT id FROM students WHERE roll_number = ?', (roll_number,))
            if cursor.fetchone():
                flash('Roll number already registered', 'error')
                return render_template('student_registration.html')
            
            # Create user
            hashed_password = generate_password_hash(password)
            cursor.execute(
                'INSERT INTO users (email, password, role) VALUES (?, ?, ?)',
                (email, hashed_password, 'student')
            )
            user_id = cursor.lastrowid
            
            # Create student
            cursor.execute(
                '''INSERT INTO students 
                (user_id, name, roll_number, year, school, branch) 
                VALUES (?, ?, ?, ?, ?, ?)''',
                (user_id, name, roll_number, year, school, branch)
            )
            
            conn.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect('/login')
    
    return render_template('student_registration.html')

@app.route('/register/supervisor', methods=['GET', 'POST'])
def supervisor_registration():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        domain = request.form.get('domain')
        school = request.form.get('school')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('supervisor_registration.html')
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            if cursor.fetchone():
                flash('Email already registered', 'error')
                return render_template('supervisor_registration.html')
            
            hashed_password = generate_password_hash(password)
            cursor.execute(
                'INSERT INTO users (email, password, role) VALUES (?, ?, ?)',
                (email, hashed_password, 'supervisor')
            )
            user_id = cursor.lastrowid
            
            cursor.execute(
                'INSERT INTO supervisors (user_id, name, domain, school) VALUES (?, ?, ?, ?)',
                (user_id, name, domain, school)
            )
            
            conn.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect('/login')
    
    return render_template('supervisor_registration.html')

@app.route('/register/fic', methods=['GET', 'POST'])
def fic_registration():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        school = request.form.get('school')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('fic_registration.html')
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            if cursor.fetchone():
                flash('Email already registered', 'error')
                return render_template('fic_registration.html')
            
            # Check FIC limit per school
            cursor.execute('SELECT COUNT(*) FROM fic WHERE school = ?', (school,))
            fic_count = cursor.fetchone()[0]
            if fic_count >= 6:
                flash('Maximum FIC limit reached for this school', 'error')
                return render_template('fic_registration.html')
            
            hashed_password = generate_password_hash(password)
            cursor.execute(
                'INSERT INTO users (email, password, role) VALUES (?, ?, ?)',
                (email, hashed_password, 'fic')
            )
            user_id = cursor.lastrowid
            
            cursor.execute(
                'INSERT INTO fic (user_id, name, school) VALUES (?, ?, ?)',
                (user_id, name, school)
            )
            
            conn.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect('/login')
    
    return render_template('fic_registration.html')

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        return redirect('/')
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.*, sg.name as group_name, sg.project_title, sg.document_link
            FROM students s 
            LEFT JOIN student_groups sg ON s.group_id = sg.id
            WHERE s.user_id = ?
        ''', (current_user.id,))
        student_data = cursor.fetchone()
        
        if not student_data:
            flash('Student profile not found', 'error')
            return redirect('/logout')
        
        # Get available students for inviting
        cursor.execute('''
            SELECT s.* FROM students s
            WHERE s.year = ? AND s.branch = ? AND s.group_id IS NULL AND s.user_id != ?
        ''', (student_data['year'], student_data['branch'], current_user.id))
        available_students = cursor.fetchall()
        
        # Get available supervisors
        cursor.execute('SELECT * FROM supervisors WHERE school = ?', (student_data['school'],))
        available_supervisors = cursor.fetchall()
    
    student = {
        'id': student_data['id'],
        'name': student_data['name'],
        'roll_number': student_data['roll_number'],
        'year': student_data['year'],
        'school': student_data['school'],
        'branch': student_data['branch'],
        'group_id': student_data['group_id'],
        'group_name': student_data['group_name'],
        'project_title': student_data['project_title'],
        'document_link': student_data['document_link']
    }
    
    return render_template('student_dashboard.html',
                         student=student,
                         available_students=available_students,
                         available_supervisors=available_supervisors)

@app.route('/supervisor/dashboard')
@login_required
def supervisor_dashboard():
    if current_user.role != 'supervisor':
        return redirect('/')
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM supervisors WHERE user_id = ?', (current_user.id,))
        supervisor_data = cursor.fetchone()
        
        if not supervisor_data:
            flash('Supervisor profile not found', 'error')
            return redirect('/logout')
        
        # Get supervised groups
        cursor.execute('''
            SELECT sg.*, COUNT(s.id) as member_count
            FROM student_groups sg
            LEFT JOIN students s ON sg.id = s.group_id
            WHERE sg.supervisor_id = ?
            GROUP BY sg.id
        ''', (supervisor_data['id'],))
        supervised_groups = cursor.fetchall()
    
    supervisor = {
        'id': supervisor_data['id'],
        'name': supervisor_data['name'],
        'domain': supervisor_data['domain'],
        'school': supervisor_data['school']
    }
    
    return render_template('supervisor_dashboard.html',
                         supervisor=supervisor,
                         supervised_groups=supervised_groups)

@app.route('/fic/dashboard')
@login_required
def fic_dashboard():
    if current_user.role != 'fic':
        return redirect('/')
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM fic WHERE user_id = ?', (current_user.id,))
        fic_data = cursor.fetchone()
        
        if not fic_data:
            flash('FIC profile not found', 'error')
            return redirect('/logout')
        
        # Get school groups
        cursor.execute('''
            SELECT sg.*, COUNT(s.id) as member_count
            FROM student_groups sg
            LEFT JOIN students s ON sg.id = s.group_id
            WHERE sg.branch IN (SELECT DISTINCT branch FROM students WHERE school = ?)
            GROUP BY sg.id
        ''', (fic_data['school'],))
        school_groups = cursor.fetchall()
        
        # Get school supervisors
        cursor.execute('SELECT * FROM supervisors WHERE school = ?', (fic_data['school'],))
        school_supervisors = cursor.fetchall()
    
    fic = {
        'id': fic_data['id'],
        'name': fic_data['name'],
        'school': fic_data['school']
    }
    
    return render_template('fic_dashboard.html',
                         fic=fic,
                         school_groups=school_groups,
                         school_supervisors=school_supervisors)

# API Routes
@app.route('/api/send_invite', methods=['POST'])
@login_required
def send_invite():
    if current_user.role != 'student':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.get_json()
    receiver_id = data.get('receiver_id')
    
    # Implementation for group invites
    return jsonify({'success': True, 'message': 'Invite sent successfully'})

@app.route('/api/send_otp', methods=['POST'])
def send_otp():
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'success': False, 'message': 'Email is required'})
    
    # Simulate OTP sending for Vercel
    otp_code = ''.join(secrets.choice('0123456789') for _ in range(6))
    
    return jsonify({
        'success': True, 
        'message': f'OTP {otp_code} sent successfully (simulated)'
    })

@app.route('/forgot_password')
def forgot_password():
    return render_template('forgot_password.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

# Health check
@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy', 
        'service': 'Project Management System',
        'timestamp': datetime.utcnow().isoformat()
    })

# Vercel serverless handler
def handler(request):
    """Vercel serverless function handler"""
    with app.test_request_context(
        path=request['path'],
        method=request['method'],
        headers=request.get('headers', {}),
        data=json.dumps(request.get('body')) if request.get('body') else None
    ):
        try:
            response = app.full_dispatch_request()
        except Exception as e:
            response = app.handle_exception(e)
        
        return {
            'statusCode': response.status_code,
            'headers': dict(response.headers),
            'body': response.get_data(as_text=True)
        }

# For local development
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=True)
