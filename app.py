from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, timezone
import secrets
import os
from dotenv import load_dotenv
import csv
import io
from io import StringIO
import urllib.parse
import socket
import time

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', '08d8440116c5b8b558bd90d064310f2aeb9846ae028c3c89b66d4e289baa5fbe')

# Database configuration - Support both MySQL (local) and PostgreSQL (Supabase)
db_type = os.getenv('DATABASE_TYPE', 'postgresql')

if db_type == 'mysql':
    # MySQL configuration for local development
    db_user = os.getenv('MYSQL_USER', 'root')
    db_password = os.getenv('MYSQL_PASSWORD', '12345')
    db_host = os.getenv('MYSQL_HOST', 'localhost')
    db_port = os.getenv('MYSQL_PORT', '3306')
    db_name = os.getenv('MYSQL_DB', 'project_management_system')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+mysqlconnector://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 5,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }
else:
    # PostgreSQL configuration for Supabase
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'postgres')
    
    # URL encode password to handle special characters
    encoded_password = urllib.parse.quote_plus(db_password)
    
    # Use transaction pooler or direct connection
    use_pooler = os.getenv('USE_POOLER', 'true').lower() == 'true'
    use_transaction_pooler = os.getenv('USE_TRANSACTION_POOLER', 'false').lower() == 'true'
    
    if use_transaction_pooler:
        # Transaction pooler (port 6543)
        app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql+psycopg2://{db_user}:{encoded_password}@{db_host}:6543/{db_name}?sslmode=require&connect_timeout=15"
    elif use_pooler:
        # Session pooler (port 5432)
        app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql+psycopg2://{db_user}:{encoded_password}@{db_host}:{db_port}/{db_name}?sslmode=require&connect_timeout=15&keepalives=1&keepalives_idle=5&keepalives_interval=2"
    else:
        # Direct connection
        app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql+psycopg2://{db_user}:{encoded_password}@{db_host}:{db_port}/{db_name}?sslmode=require&connect_timeout=15"
    
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 1,
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'pool_use_lifo': True,
        'max_overflow': 0,
        'pool_timeout': 30
    }

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']
app.config['MAIL_SUPPRESS_SEND'] = False
app.config['TESTING'] = False

db = SQLAlchemy(app)
mail = Mail(app)

# Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Teardown request to close database connections
@app.teardown_appcontext
def shutdown_session(exception=None):
    """Close database session after each request"""
    db.session.remove()

# Health check endpoint for Render
@app.route('/health')
def health_check():
    """Health check endpoint for Render"""
    try:
        db.session.execute('SELECT 1')
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

def get_utc_now():
    """Get current UTC time as timezone-aware datetime"""
    return datetime.now(timezone.utc)

def make_timezone_aware(dt):
    """Make a datetime timezone-aware if it's naive"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

# Models
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=get_utc_now)
    
    def is_authenticated(self):
        return True
    
    def is_active(self):
        return True
    
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.id)

class Student(db.Model):
    __tablename__ = 'student'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(20), unique=True, nullable=False)
    year = db.Column(db.String(10), nullable=False)
    school = db.Column(db.String(100), nullable=False)
    branch = db.Column(db.String(50), nullable=False)
    phone_number = db.Column(db.String(15))
    mentor_name = db.Column(db.String(100))
    mentor_phone = db.Column(db.String(15))
    mentor_email = db.Column(db.String(120))
    group_id = db.Column(db.Integer, db.ForeignKey('student_group.id'))
    
    user = db.relationship('User', backref=db.backref('student', uselist=False))
    group = db.relationship('StudentGroup', backref=db.backref('students', lazy=True))

class Supervisor(db.Model):
    __tablename__ = 'supervisor'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    domain = db.Column(db.String(100), nullable=False)
    school = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(15))
    max_groups = db.Column(db.Integer, default=3)
    priority = db.Column(db.Integer, default=1)
    
    user = db.relationship('User', backref=db.backref('supervisor', uselist=False))
    supervised_groups = db.relationship('StudentGroup', backref='supervisor', lazy=True)

class FIC(db.Model):
    __tablename__ = 'fic'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    school = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(15))
    
    user = db.relationship('User', backref=db.backref('fic', uselist=False))

class StudentGroup(db.Model):
    __tablename__ = 'student_group'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('supervisor.id'))
    project_title = db.Column(db.String(255))
    project_description = db.Column(db.Text)
    document_link = db.Column(db.String(500))
    whatsapp_link = db.Column(db.String(500))
    branch = db.Column(db.String(50), nullable=False)
    year = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=get_utc_now)

class GroupInvite(db.Model):
    __tablename__ = 'group_invite'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    sent_at = db.Column(db.DateTime, default=get_utc_now)
    
    sender = db.relationship('Student', foreign_keys=[sender_id], backref='sent_invites')
    receiver = db.relationship('Student', foreign_keys=[receiver_id], backref='received_invites')

class SupervisorRequest(db.Model):
    __tablename__ = 'supervisor_request'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('student_group.id'), nullable=False)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('supervisor.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    sent_at = db.Column(db.DateTime, default=get_utc_now)
    
    group = db.relationship('StudentGroup', backref='supervisor_requests')
    supervisor = db.relationship('Supervisor', backref='received_requests')

class SupervisorChangeRequest(db.Model):
    __tablename__ = 'supervisor_change_request'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('student_group.id'), nullable=False)
    current_supervisor_id = db.Column(db.Integer, db.ForeignKey('supervisor.id'), nullable=False)
    new_supervisor_id = db.Column(db.Integer, db.ForeignKey('supervisor.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=get_utc_now)
    processed_at = db.Column(db.DateTime, nullable=True)
    
    group = db.relationship('StudentGroup', backref='supervisor_change_requests')
    current_supervisor = db.relationship('Supervisor', foreign_keys=[current_supervisor_id])
    new_supervisor = db.relationship('Supervisor', foreign_keys=[new_supervisor_id])

class Panel(db.Model):
    __tablename__ = 'panel'
    id = db.Column(db.Integer, primary_key=True)
    panel_number = db.Column(db.String(20), unique=True, nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('student_group.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('fic.id'), nullable=False)
    phase = db.Column(db.String(20), default='Phase 1')
    evaluation_date = db.Column(db.Date)
    evaluation_time = db.Column(db.Time)
    venue = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=get_utc_now)
    
    group = db.relationship('StudentGroup', backref='panels')
    fic = db.relationship('FIC', backref='created_panels')

class PanelMember(db.Model):
    __tablename__ = 'panel_member'
    id = db.Column(db.Integer, primary_key=True)
    panel_id = db.Column(db.Integer, db.ForeignKey('panel.id'), nullable=False)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('supervisor.id'), nullable=False)
    
    panel = db.relationship('Panel', backref='members')
    supervisor = db.relationship('Supervisor', backref='panel_memberships')

class Evaluation(db.Model):
    __tablename__ = 'evaluation'
    id = db.Column(db.Integer, primary_key=True)
    panel_id = db.Column(db.Integer, db.ForeignKey('panel.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('student_group.id'), nullable=False)
    evaluator_id = db.Column(db.Integer, db.ForeignKey('supervisor.id'), nullable=False)
    presentation_marks = db.Column(db.Float, default=0)
    documentation_marks = db.Column(db.Float, default=0)
    collaboration_marks = db.Column(db.Float, default=0)
    innovation_marks = db.Column(db.Float, default=0)
    total_marks = db.Column(db.Float, default=0)
    feedback_to_students = db.Column(db.Text)
    feedback_to_supervisor = db.Column(db.Text)
    evaluated_at = db.Column(db.DateTime, default=get_utc_now)
    
    panel = db.relationship('Panel', backref='evaluations')
    group = db.relationship('StudentGroup', backref='evaluations')
    evaluator = db.relationship('Supervisor', backref='given_evaluations')

class Marks(db.Model):
    __tablename__ = 'marks'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    presentation = db.Column(db.Float, default=0)
    documents = db.Column(db.Float, default=0)
    collaboration = db.Column(db.Float, default=0)
    total = db.Column(db.Float, default=0)
    given_by = db.Column(db.Integer, db.ForeignKey('supervisor.id'), nullable=False)
    given_at = db.Column(db.DateTime, default=get_utc_now)
    
    student = db.relationship('Student', backref='marks')
    supervisor_given = db.relationship('Supervisor', backref='given_marks')

class OTP(db.Model):
    __tablename__ = 'otp'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    otp = db.Column(db.String(6), nullable=False)
    purpose = db.Column(db.String(20), default='registration')
    created_at = db.Column(db.DateTime, default=get_utc_now)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)

class Notification(db.Model):
    __tablename__ = 'notification'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    target_type = db.Column(db.String(20), nullable=False)
    target_branch = db.Column(db.String(50))
    created_by = db.Column(db.Integer, db.ForeignKey('fic.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=get_utc_now)
    
    fic = db.relationship('FIC', backref='sent_notifications')

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            
            if user.role == 'student':
                return redirect(url_for('student_dashboard'))
            elif user.role == 'supervisor':
                return redirect(url_for('supervisor_dashboard'))
            elif user.role == 'fic':
                return redirect(url_for('fic_dashboard'))
        
        flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('If this email exists, a password reset OTP has been sent.', 'info')
            return render_template('forgot_password.html')
        
        otp_code = ''.join(secrets.choice('0123456789') for _ in range(6))
        expires_at = get_utc_now() + timedelta(minutes=10)
        
        otp = OTP(
            email=email, 
            otp=otp_code, 
            purpose='password_reset',
            expires_at=expires_at
        )
        db.session.add(otp)
        db.session.commit()
        
        try:
            msg = Message('Password Reset OTP - Project Management System', 
                         sender=app.config['MAIL_USERNAME'], 
                         recipients=[email])
            msg.body = f'''You have requested to reset your password.

Your OTP for password reset is: {otp_code}

This OTP will expire in 10 minutes.

If you did not request a password reset, please ignore this email.
'''
            mail.send(msg)
            flash('Password reset OTP has been sent to your email.', 'success')
            return redirect(url_for('reset_password_with_otp', email=email))
        except Exception as e:
            print(f"Email error: {e}")
            flash('Failed to send OTP email. Please try again.', 'error')
        
        return render_template('forgot_password.html')
    
    return render_template('forgot_password.html')

@app.route('/reset_password/<email>', methods=['GET', 'POST'])
def reset_password_with_otp(email):
    if request.method == 'POST':
        otp = request.form.get('otp')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('reset_password_otp.html', email=email)
        
        otp_record = OTP.query.filter_by(
            email=email, 
            purpose='password_reset', 
            used=False
        ).order_by(OTP.created_at.desc()).first()
        
        current_time = get_utc_now()
        expires_at = make_timezone_aware(otp_record.expires_at) if otp_record else None
        
        if not otp_record or otp_record.otp != otp or (expires_at and expires_at < current_time):
            flash('Invalid or expired OTP', 'error')
            return render_template('reset_password_otp.html', email=email)
        
        user = User.query.filter_by(email=email).first()
        if user:
            user.password = generate_password_hash(password)
            otp_record.used = True
            db.session.commit()
            flash('Password has been reset successfully. Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('User not found.', 'error')
    
    return render_template('reset_password_otp.html', email=email)

@app.route('/send_password_reset_otp', methods=['POST'])
def send_password_reset_otp():
    email = request.json.get('email')
    
    if not email:
        return jsonify({'success': False, 'message': 'Email is required'})
    
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'success': True, 'message': 'If this email exists, a password reset OTP has been sent.'})
    
    otp_code = ''.join(secrets.choice('0123456789') for _ in range(6))
    expires_at = get_utc_now() + timedelta(minutes=10)
    
    otp = OTP(
        email=email, 
        otp=otp_code, 
        purpose='password_reset',
        expires_at=expires_at
    )
    db.session.add(otp)
    db.session.commit()
    
    try:
        msg = Message('Password Reset OTP - Project Management System', 
                     sender=app.config['MAIL_USERNAME'], 
                     recipients=[email])
        msg.body = f'Your OTP for password reset is: {otp_code}\n\nThis OTP will expire in 10 minutes.'
        mail.send(msg)
        return jsonify({'success': True, 'message': 'Password reset OTP sent successfully'})
    except Exception as e:
        print(f"Email error: {e}")
        return jsonify({'success': False, 'message': 'Failed to send OTP'})

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form.get('role')
        
        if role == 'student':
            return redirect(url_for('student_registration'))
        elif role == 'supervisor':
            return redirect(url_for('supervisor_registration'))
        elif role == 'fic':
            return redirect(url_for('fic_registration'))
    
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
        phone_number = request.form.get('phone_number')
        mentor_name = request.form.get('mentor_name')
        mentor_phone = request.form.get('mentor_phone')
        mentor_email = request.form.get('mentor_email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        otp = request.form.get('otp')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('student_registration.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('student_registration.html')
        
        if Student.query.filter_by(roll_number=roll_number).first():
            flash('Roll number already registered', 'error')
            return render_template('student_registration.html')
        
        otp_record = OTP.query.filter_by(
            email=email, 
            purpose='registration', 
            used=False
        ).order_by(OTP.created_at.desc()).first()
        
        current_time = get_utc_now()
        expires_at = make_timezone_aware(otp_record.expires_at) if otp_record else None
        
        if not otp_record or otp_record.otp != otp or (expires_at and expires_at < current_time):
            flash('Invalid or expired OTP', 'error')
            return render_template('student_registration.html')
        
        try:
            hashed_password = generate_password_hash(password)
            user = User(email=email, password=hashed_password, role='student')
            db.session.add(user)
            db.session.flush()
            
            student = Student(
                user_id=user.id,
                name=name,
                roll_number=roll_number,
                year=year,
                school=school,
                branch=branch,
                phone_number=phone_number,
                mentor_name=mentor_name,
                mentor_phone=mentor_phone,
                mentor_email=mentor_email
            )
            db.session.add(student)
            
            otp_record.used = True
            db.session.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Registration error: {e}")
            flash('Registration failed. Please try again.', 'error')
            return render_template('student_registration.html')
    
    return render_template('student_registration.html')

@app.route('/register/supervisor', methods=['GET', 'POST'])
def supervisor_registration():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        domain = request.form.get('domain')
        school = request.form.get('school')
        phone_number = request.form.get('phone_number')
        priority = request.form.get('priority', 1)
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        otp = request.form.get('otp')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('supervisor_registration.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('supervisor_registration.html')
        
        otp_record = OTP.query.filter_by(
            email=email, 
            purpose='registration', 
            used=False
        ).order_by(OTP.created_at.desc()).first()
        
        current_time = get_utc_now()
        expires_at = make_timezone_aware(otp_record.expires_at) if otp_record else None
        
        if not otp_record or otp_record.otp != otp or (expires_at and expires_at < current_time):
            flash('Invalid or expired OTP', 'error')
            return render_template('supervisor_registration.html')
        
        try:
            hashed_password = generate_password_hash(password)
            user = User(email=email, password=hashed_password, role='supervisor')
            db.session.add(user)
            db.session.flush()
            
            if len(domain) > 100:
                domain = domain[:100]
            
            supervisor = Supervisor(
                user_id=user.id,
                name=name,
                domain=domain,
                school=school,
                phone_number=phone_number,
                priority=int(priority) if priority else 1
            )
            db.session.add(supervisor)
            
            otp_record.used = True
            db.session.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Registration error: {e}")
            flash(f'Registration failed: {str(e)}', 'error')
            return render_template('supervisor_registration.html')
    
    return render_template('supervisor_registration.html')

@app.route('/register/fic', methods=['GET', 'POST'])
def fic_registration():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        school = request.form.get('school')
        phone_number = request.form.get('phone_number')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        otp = request.form.get('otp')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('fic_registration.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('fic_registration.html')
        
        fic_count = FIC.query.filter_by(school=school).count()
        if fic_count >= 6:
            flash('Maximum FIC limit reached for this school', 'error')
            return render_template('fic_registration.html')
        
        otp_record = OTP.query.filter_by(
            email=email, 
            purpose='registration', 
            used=False
        ).order_by(OTP.created_at.desc()).first()
        
        current_time = get_utc_now()
        expires_at = make_timezone_aware(otp_record.expires_at) if otp_record else None
        
        if not otp_record or otp_record.otp != otp or (expires_at and expires_at < current_time):
            flash('Invalid or expired OTP', 'error')
            return render_template('fic_registration.html')
        
        try:
            hashed_password = generate_password_hash(password)
            user = User(email=email, password=hashed_password, role='fic')
            db.session.add(user)
            db.session.flush()
            
            fic = FIC(
                user_id=user.id,
                name=name,
                school=school,
                phone_number=phone_number
            )
            db.session.add(fic)
            
            otp_record.used = True
            db.session.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Registration error: {e}")
            flash('Registration failed. Please try again.', 'error')
            return render_template('fic_registration.html')
    
    return render_template('fic_registration.html')

@app.route('/send_otp', methods=['POST'])
def send_otp():
    email = request.json.get('email')
    purpose = request.json.get('purpose', 'registration')
    
    if not email:
        return jsonify({'success': False, 'message': 'Email is required'})
    
    # Validate email format
    import re
    if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
        return jsonify({'success': False, 'message': 'Invalid email format'})
    
    otp_code = ''.join(secrets.choice('0123456789') for _ in range(6))
    expires_at = get_utc_now() + timedelta(minutes=10)
    
    try:
        # Store OTP in database
        otp = OTP(
            email=email, 
            otp=otp_code, 
            purpose=purpose,
            expires_at=expires_at
        )
        db.session.add(otp)
        db.session.commit()
        
        # Send email
        if purpose == 'password_reset':
            subject = 'Password Reset OTP - Project Management System'
            body = f'''Your OTP for password reset is: {otp_code}

This OTP will expire in 10 minutes.

If you did not request this, please ignore this email.
'''
        else:
            subject = 'Your OTP for Registration - Project Management System'
            body = f'''Welcome to Project Management System!

Your OTP for registration is: {otp_code}

This OTP will expire in 10 minutes.

Please enter this OTP to complete your registration.
'''
        
        msg = Message(
            subject=subject,
            sender=app.config['MAIL_USERNAME'],
            recipients=[email]
        )
        msg.body = body
        
        # Try to send email with timeout
        socket.setdefaulttimeout(30)
        mail.send(msg)
        
        return jsonify({'success': True, 'message': 'OTP sent successfully! Please check your email.'})
        
    except Exception as e:
        print(f"Email error details: {str(e)}")
        db.session.rollback()
        
        error_msg = str(e)
        if "Authentication" in error_msg or "login" in error_msg.lower():
            return jsonify({'success': False, 'message': 'Email service authentication failed. Please contact support.'})
        elif "Timeout" in error_msg:
            return jsonify({'success': False, 'message': 'Email service timeout. Please try again.'})
        else:
            return jsonify({'success': False, 'message': f'Failed to send OTP: {error_msg[:100]}'})

@app.route('/student/<int:student_id>/details')
@login_required
def get_student_details(student_id):
    student = Student.query.get_or_404(student_id)
    
    if current_user.role == 'supervisor':
        supervisor = Supervisor.query.filter_by(user_id=current_user.id).first()
        if not supervisor:
            return jsonify({'success': False, 'message': 'Supervisor profile not found'})
        
        if student.group and student.group.supervisor_id == supervisor.id:
            authorized = True
        elif student.group:
            panel_membership = PanelMember.query.join(Panel).filter(
                Panel.group_id == student.group_id,
                PanelMember.supervisor_id == supervisor.id
            ).first()
            authorized = panel_membership is not None
        else:
            authorized = False
            
    elif current_user.role == 'fic':
        fic = FIC.query.filter_by(user_id=current_user.id).first()
        if not fic:
            return jsonify({'success': False, 'message': 'FIC profile not found'})
        authorized = student.school == fic.school
    else:
        authorized = False
    
    if not authorized:
        return jsonify({'success': False, 'message': 'Unauthorized to view student details'})
    
    student_data = {
        'success': True,
        'student': {
            'id': student.id,
            'name': student.name,
            'roll_number': student.roll_number,
            'year': student.year,
            'school': student.school,
            'branch': student.branch,
            'phone_number': student.phone_number or 'Not provided',
            'mentor_name': student.mentor_name or 'Not provided',
            'mentor_phone': student.mentor_phone or 'Not provided',
            'mentor_email': student.mentor_email or 'Not provided',
            'group_name': student.group.name if student.group else 'No group',
            'project_title': student.group.project_title if student.group else 'No project'
        }
    }
    
    return jsonify(student_data)

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        return redirect(url_for('index'))
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash('Student profile not found', 'error')
        return redirect(url_for('logout'))
    
    group = None
    group_members = []
    
    invites = GroupInvite.query.filter_by(receiver_id=student.id, status='pending').all()
    sent_invites = GroupInvite.query.filter_by(sender_id=student.id).order_by(GroupInvite.sent_at.desc()).all()
    
    if student.group_id:
        group = StudentGroup.query.get(student.group_id)
        group_members = Student.query.filter_by(group_id=student.group_id).all()
    
    available_students_query = Student.query.filter(
        Student.year == student.year,
        Student.branch == student.branch,
        Student.group_id.is_(None),
        Student.id != student.id
    )
    
    invited_student_ids = [invite.receiver_id for invite in sent_invites]
    available_students = available_students_query.filter(
        ~Student.id.in_(invited_student_ids)
    ).all()
    
    available_supervisors = Supervisor.query.filter_by(school=student.school).all()
    
    supervisor_change_requests = []
    if group and group.supervisor_id:
        supervisor_change_requests = SupervisorChangeRequest.query.filter_by(
            group_id=group.id
        ).all()
    
    panel_evaluations = []
    average_marks = 0
    panel_feedback = []
    global_feedback = []
    
    if group:
        panel_evaluations = Panel.query.filter_by(group_id=group.id).all()
        
        evaluations = Evaluation.query.filter_by(group_id=group.id).all()
        if evaluations:
            total_marks = sum([e.total_marks for e in evaluations])
            average_marks = total_marks / len(evaluations)
            panel_feedback = [e.feedback_to_students for e in evaluations if e.feedback_to_students]
            global_feedback = Notification.query.filter(
                Notification.target_type == 'all'
            ).order_by(Notification.created_at.desc()).limit(5).all()
    
    notifications = Notification.query.filter(
        (Notification.target_type == 'all') |
        (Notification.target_type == 'students') |
        ((Notification.target_type == 'specific_branch') & (Notification.target_branch == student.branch))
    ).order_by(Notification.created_at.desc()).limit(10).all()
    
    return render_template('student_dashboard.html', 
                          student=student, 
                          group=group, 
                          group_members=group_members,
                          invites=invites,
                          sent_invites=sent_invites,
                          available_students=available_students,
                          available_supervisors=available_supervisors,
                          supervisor_change_requests=supervisor_change_requests,
                          notifications=notifications,
                          panel_evaluations=panel_evaluations,
                          average_marks=average_marks,
                          panel_feedback=panel_feedback,
                          global_feedback=global_feedback)

@app.route('/supervisor/dashboard')
@login_required
def supervisor_dashboard():
    if current_user.role != 'supervisor':
        return redirect(url_for('index'))
    
    supervisor = Supervisor.query.filter_by(user_id=current_user.id).first()
    if not supervisor:
        flash('Supervisor profile not found', 'error')
        return redirect(url_for('logout'))
    
    supervised_groups = StudentGroup.query.filter_by(supervisor_id=supervisor.id).all()
    pending_requests = SupervisorRequest.query.filter_by(supervisor_id=supervisor.id, status='pending').all()
    
    supervisor_change_requests = SupervisorChangeRequest.query.filter_by(
        current_supervisor_id=supervisor.id,
        status='pending'
    ).all()
    
    panel_memberships = PanelMember.query.filter_by(supervisor_id=supervisor.id).all()
    panel_evaluations = []
    for membership in panel_memberships:
        panel = Panel.query.get(membership.panel_id)
        if panel:
            evaluations = Evaluation.query.filter_by(panel_id=panel.id).all()
            panel_evaluations.append({
                'panel': panel,
                'evaluations': evaluations
            })
    
    supervisor_feedback = []
    for group in supervised_groups:
        evaluations = Evaluation.query.filter_by(group_id=group.id).all()
        for eval in evaluations:
            if eval.feedback_to_supervisor:
                supervisor_feedback.append({
                    'group': group,
                    'feedback': eval.feedback_to_supervisor,
                    'evaluator': eval.evaluator
                })
    
    notifications = Notification.query.filter(
        (Notification.target_type == 'all') |
        (Notification.target_type == 'supervisors')
    ).order_by(Notification.created_at.desc()).limit(10).all()
    
    return render_template('supervisor_dashboard.html', 
                          supervisor=supervisor,
                          supervised_groups=supervised_groups,
                          pending_requests=pending_requests,
                          supervisor_change_requests=supervisor_change_requests,
                          panel_memberships=panel_memberships,
                          panel_evaluations=panel_evaluations,
                          supervisor_feedback=supervisor_feedback,
                          notifications=notifications)

@app.route('/panel/dashboard')
@login_required
def panel_dashboard():
    if current_user.role != 'supervisor':
        return redirect(url_for('index'))
    
    supervisor = Supervisor.query.filter_by(user_id=current_user.id).first()
    if not supervisor:
        flash('Supervisor profile not found', 'error')
        return redirect(url_for('logout'))
    
    panel_memberships = PanelMember.query.filter_by(supervisor_id=supervisor.id).all()
    panels = []
    
    for membership in panel_memberships:
        panel = Panel.query.get(membership.panel_id)
        if panel:
            group = StudentGroup.query.get(panel.group_id)
            evaluations = Evaluation.query.filter_by(
                panel_id=panel.id,
                evaluator_id=supervisor.id
            ).all()
            
            panels.append({
                'panel': panel,
                'group': group,
                'evaluations': evaluations
            })
    
    return render_template('panel_dashboard.html',
                          supervisor=supervisor,
                          panels=panels)

@app.route('/fic/dashboard')
@login_required
def fic_dashboard():
    if current_user.role != 'fic':
        return redirect(url_for('index'))
    
    fic = FIC.query.filter_by(user_id=current_user.id).first()
    if not fic:
        flash('FIC profile not found', 'error')
        return redirect(url_for('logout'))
    
    school_groups = StudentGroup.query.join(Student).filter(Student.school == fic.school).distinct().all()
    school_supervisors = Supervisor.query.filter_by(school=fic.school).all()
    
    supervisor_change_requests = SupervisorChangeRequest.query.filter(
        SupervisorChangeRequest.status == 'pending'
    ).all()
    
    filtered_requests = []
    for request in supervisor_change_requests:
        group = request.group
        if group and any(student.school == fic.school for student in group.students):
            filtered_requests.append(request)
    
    created_panels = Panel.query.filter_by(created_by=fic.id).all()
    notifications = Notification.query.filter_by(created_by=fic.id).order_by(Notification.created_at.desc()).limit(10).all()
    
    evaluation_progress = {}
    for group in school_groups:
        evaluations = Evaluation.query.filter_by(group_id=group.id).all()
        completed = len(evaluations)
        panel = Panel.query.filter_by(group_id=group.id).first()
        total = len(panel.members) if panel else 0
        evaluation_progress[group.id] = {
            'completed': completed,
            'total': total,
            'percentage': (completed / total * 100) if total > 0 else 0
        }
    
    branches = db.session.query(StudentGroup.branch).filter(
        StudentGroup.id.in_([g.id for g in school_groups])
    ).distinct().all()
    branches = [b[0] for b in branches]
    
    return render_template('fic_dashboard.html', 
                          fic=fic,
                          school_groups=school_groups,
                          school_supervisors=school_supervisors,
                          supervisor_change_requests=filtered_requests,
                          created_panels=created_panels,
                          evaluation_progress=evaluation_progress,
                          notifications=notifications,
                          branches=branches)

@app.route('/send_invite', methods=['POST'])
@login_required
def send_invite():
    if current_user.role != 'student':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    receiver_id = request.json.get('receiver_id')
    student = Student.query.filter_by(user_id=current_user.id).first()
    
    if not student:
        return jsonify({'success': False, 'message': 'Student profile not found'})
    
    if student.group_id:
        group_members_count = Student.query.filter_by(group_id=student.group_id).count()
        if group_members_count >= 4:
            return jsonify({'success': False, 'message': 'Your group already has maximum 4 members'})
    
    receiver = Student.query.get(receiver_id)
    if not receiver or receiver.group_id or receiver.year != student.year or receiver.branch != student.branch:
        return jsonify({'success': False, 'message': 'Invalid student'})
    
    existing_invite = GroupInvite.query.filter_by(
        sender_id=student.id, 
        receiver_id=receiver_id
    ).first()
    
    if existing_invite:
        if existing_invite.status == 'pending':
            return jsonify({'success': False, 'message': 'Invite already sent'})
        else:
            existing_invite.status = 'pending'
            existing_invite.sent_at = get_utc_now()
            db.session.commit()
            return jsonify({'success': True, 'message': 'Invite sent successfully'})
    
    invite = GroupInvite(sender_id=student.id, receiver_id=receiver_id)
    db.session.add(invite)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Invite sent successfully'})

@app.route('/respond_invite', methods=['POST'])
@login_required
def respond_invite():
    if current_user.role != 'student':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    invite_id = request.json.get('invite_id')
    action = request.json.get('action')
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        return jsonify({'success': False, 'message': 'Student profile not found'})
    
    invite = GroupInvite.query.get(invite_id)
    
    if not invite or invite.receiver_id != student.id:
        return jsonify({'success': False, 'message': 'Invalid invite'})
    
    if action == 'accept':
        if student.group_id:
            group_members_count = Student.query.filter_by(group_id=student.group_id).count()
            if group_members_count >= 4:
                return jsonify({'success': False, 'message': 'Your group already has maximum 4 members'})
        
        sender = Student.query.get(invite.sender_id)
        if not sender:
            return jsonify({'success': False, 'message': 'Sender not found'})
        
        if sender.group_id:
            group_members_count = Student.query.filter_by(group_id=sender.group_id).count()
            if group_members_count >= 4:
                invite.status = 'rejected'
                db.session.commit()
                return jsonify({'success': False, 'message': 'The group you were invited to is now full'})
        
        if sender.group_id:
            student.group_id = sender.group_id
            group = StudentGroup.query.get(sender.group_id)
        else:
            group_count = StudentGroup.query.filter_by(branch=student.branch).count()
            group_name = f"{student.branch}{group_count + 1:02d}"
            
            group = StudentGroup(name=group_name, branch=student.branch, year=student.year)
            db.session.add(group)
            db.session.flush()
            
            sender.group_id = group.id
            student.group_id = group.id
        
        invite.status = 'accepted'
        
        other_pending_invites = GroupInvite.query.filter_by(
            receiver_id=student.id,
            status='pending'
        ).filter(GroupInvite.id != invite.id).all()
        
        for other_invite in other_pending_invites:
            other_invite.status = 'rejected'
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Invite accepted. You are now in a group!'})
    
    elif action == 'reject':
        invite.status = 'rejected'
        db.session.commit()
        return jsonify({'success': True, 'message': 'Invite rejected'})
    
    return jsonify({'success': False, 'message': 'Invalid action'})

@app.route('/cancel_invite', methods=['POST'])
@login_required
def cancel_invite():
    if current_user.role != 'student':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    invite_id = request.json.get('invite_id')
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        return jsonify({'success': False, 'message': 'Student profile not found'})
    
    invite = GroupInvite.query.get(invite_id)
    
    if not invite or invite.sender_id != student.id:
        return jsonify({'success': False, 'message': 'Invalid invite'})
    
    if invite.status != 'pending':
        return jsonify({'success': False, 'message': 'Can only cancel pending invites'})
    
    invite.status = 'cancelled'
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Invite cancelled'})

@app.route('/leave_group', methods=['POST'])
@login_required
def leave_group():
    if current_user.role != 'student':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        return jsonify({'success': False, 'message': 'Student profile not found'})
    
    if not student.group_id:
        return jsonify({'success': False, 'message': 'You are not in any group'})
    
    group = StudentGroup.query.get(student.group_id)
    
    remaining_members = Student.query.filter_by(group_id=student.group_id).filter(Student.id != student.id).count()
    
    if remaining_members == 0:
        SupervisorRequest.query.filter_by(group_id=group.id).delete()
        SupervisorChangeRequest.query.filter_by(group_id=group.id).delete()
        db.session.delete(group)
    else:
        student.group_id = None
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'You have left the group'})

@app.route('/request_supervisor', methods=['POST'])
@login_required
def request_supervisor():
    if current_user.role != 'student':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        return jsonify({'success': False, 'message': 'Student profile not found'})
    
    group = StudentGroup.query.get(student.group_id)
    
    if not group:
        return jsonify({'success': False, 'message': 'You are not in a group'})
    
    supervisor_id = request.json.get('supervisor_id')
    
    if group.supervisor_id:
        return jsonify({'success': False, 'message': 'Your group already has a supervisor'})
    
    existing_requests = SupervisorRequest.query.filter_by(group_id=group.id).count()
    if existing_requests >= 5:
        return jsonify({'success': False, 'message': 'Maximum request limit reached'})
    
    existing_request = SupervisorRequest.query.filter_by(
        group_id=group.id, 
        supervisor_id=supervisor_id
    ).first()
    
    if existing_request:
        return jsonify({'success': False, 'message': 'Request already sent to this supervisor'})
    
    request_obj = SupervisorRequest(group_id=group.id, supervisor_id=supervisor_id)
    db.session.add(request_obj)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Supervisor request sent'})

@app.route('/respond_supervisor_request', methods=['POST'])
@login_required
def respond_supervisor_request():
    if current_user.role != 'supervisor':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    request_id = request.json.get('request_id')
    action = request.json.get('action')
    
    supervisor = Supervisor.query.filter_by(user_id=current_user.id).first()
    if not supervisor:
        return jsonify({'success': False, 'message': 'Supervisor profile not found'})
    
    supervisor_request = SupervisorRequest.query.get(request_id)
    
    if not supervisor_request or supervisor_request.supervisor_id != supervisor.id:
        return jsonify({'success': False, 'message': 'Invalid request'})
    
    if action == 'accept':
        supervised_groups_count = StudentGroup.query.filter_by(supervisor_id=supervisor.id).count()
        if supervised_groups_count >= supervisor.max_groups:
            return jsonify({'success': False, 'message': f'You can only supervise maximum {supervisor.max_groups} groups'})
        
        group = supervisor_request.group
        if group.supervisor_id:
            return jsonify({'success': False, 'message': 'This group already has a supervisor'})
        
        group.supervisor_id = supervisor.id
        supervisor_request.status = 'accepted'
        
        SupervisorRequest.query.filter_by(
            group_id=group.id, 
            status='pending'
        ).update({'status': 'rejected'})
        
    elif action == 'reject':
        supervisor_request.status = 'rejected'
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Request {action}ed'})

@app.route('/request_supervisor_change', methods=['POST'])
@login_required
def request_supervisor_change():
    if current_user.role != 'student':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        return jsonify({'success': False, 'message': 'Student profile not found'})
    
    group = StudentGroup.query.get(student.group_id)
    
    if not group:
        return jsonify({'success': False, 'message': 'You are not in a group'})
    
    if not group.supervisor_id:
        return jsonify({'success': False, 'message': 'Your group does not have a supervisor'})
    
    new_supervisor_id = request.json.get('new_supervisor_id')
    reason = request.json.get('reason', '')
    
    new_supervisor = Supervisor.query.get(new_supervisor_id)
    if not new_supervisor or new_supervisor.school != student.school:
        return jsonify({'success': False, 'message': 'Invalid supervisor'})
    
    existing_request = SupervisorChangeRequest.query.filter_by(
        group_id=group.id,
        status='pending'
    ).first()
    
    if existing_request:
        return jsonify({'success': False, 'message': 'You already have a pending supervisor change request'})
    
    change_request = SupervisorChangeRequest(
        group_id=group.id,
        current_supervisor_id=group.supervisor_id,
        new_supervisor_id=new_supervisor_id,
        reason=reason
    )
    db.session.add(change_request)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Supervisor change request submitted for FIC approval'})

@app.route('/respond_supervisor_change_request', methods=['POST'])
@login_required
def respond_supervisor_change_request():
    if current_user.role != 'fic':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    request_id = request.json.get('request_id')
    action = request.json.get('action')
    
    fic = FIC.query.filter_by(user_id=current_user.id).first()
    if not fic:
        return jsonify({'success': False, 'message': 'FIC profile not found'})
    
    change_request = SupervisorChangeRequest.query.get(request_id)
    
    if not change_request:
        return jsonify({'success': False, 'message': 'Invalid request'})
    
    group = change_request.group
    if not any(student.school == fic.school for student in group.students):
        return jsonify({'success': False, 'message': 'Unauthorized to process this request'})
    
    if action == 'approve':
        supervised_groups_count = StudentGroup.query.filter_by(supervisor_id=change_request.new_supervisor_id).count()
        new_supervisor = Supervisor.query.get(change_request.new_supervisor_id)
        if supervised_groups_count >= new_supervisor.max_groups:
            return jsonify({'success': False, 'message': 'New supervisor can only supervise maximum 3 groups'})
        
        group.supervisor_id = change_request.new_supervisor_id
        change_request.status = 'approved'
        
    elif action == 'reject':
        change_request.status = 'rejected'
    
    change_request.processed_at = get_utc_now()
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Supervisor change request {action}d'})

@app.route('/update_whatsapp_link', methods=['POST'])
@login_required
def update_whatsapp_link():
    if current_user.role != 'supervisor':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    supervisor = Supervisor.query.filter_by(user_id=current_user.id).first()
    if not supervisor:
        return jsonify({'success': False, 'message': 'Supervisor profile not found'})
    
    group_id = request.json.get('group_id')
    whatsapp_link = request.json.get('whatsapp_link', '').strip()
    
    group = StudentGroup.query.get(group_id)
    if not group or group.supervisor_id != supervisor.id:
        return jsonify({'success': False, 'message': 'You are not supervising this group'})
    
    if whatsapp_link and not whatsapp_link.startswith('https://chat.whatsapp.com/'):
        return jsonify({'success': False, 'message': 'Invalid WhatsApp group link. Must start with https://chat.whatsapp.com/'})
    
    group.whatsapp_link = whatsapp_link
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'WhatsApp link updated successfully'})

@app.route('/update_project_details', methods=['POST'])
@login_required
def update_project_details():
    if current_user.role != 'student':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        return jsonify({'success': False, 'message': 'Student profile not found'})
    
    group = StudentGroup.query.get(student.group_id)
    
    if not group:
        return jsonify({'success': False, 'message': 'You are not in a group'})
    
    project_title = request.json.get('project_title')
    project_description = request.json.get('project_description')
    document_link = request.json.get('document_link')
    
    if project_title:
        group.project_title = project_title
    if project_description:
        group.project_description = project_description
    if document_link:
        group.document_link = document_link
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Project details updated'})

@app.route('/create_panel', methods=['POST'])
@login_required
def create_panel():
    if current_user.role != 'fic':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    group_id = request.json.get('group_id')
    panel_number = request.json.get('panel_number')
    supervisor_ids = request.json.get('supervisor_ids', [])
    phase = request.json.get('phase', 'Phase 1')
    evaluation_date = request.json.get('evaluation_date')
    evaluation_time = request.json.get('evaluation_time')
    venue = request.json.get('venue')
    
    fic = FIC.query.filter_by(user_id=current_user.id).first()
    if not fic:
        return jsonify({'success': False, 'message': 'FIC profile not found'})
    
    group = StudentGroup.query.get(group_id)
    if not group:
        return jsonify({'success': False, 'message': 'Group not found'})
    
    if not any(student.school == fic.school for student in group.students):
        return jsonify({'success': False, 'message': 'Unauthorized to create panel for this group'})
    
    existing_panel = Panel.query.filter_by(group_id=group_id).first()
    if existing_panel:
        return jsonify({'success': False, 'message': 'Panel already exists for this group'})
    
    if evaluation_date:
        try:
            eval_date = datetime.strptime(evaluation_date, '%Y-%m-%d').date()
        except:
            eval_date = None
    else:
        eval_date = None
    
    if evaluation_time:
        try:
            eval_time = datetime.strptime(evaluation_time, '%H:%M').time()
        except:
            eval_time = None
    else:
        eval_time = None
    
    panel = Panel(
        panel_number=panel_number,
        group_id=group_id,
        created_by=fic.id,
        phase=phase,
        evaluation_date=eval_date,
        evaluation_time=eval_time,
        venue=venue
    )
    db.session.add(panel)
    db.session.flush()
    
    for supervisor_id in supervisor_ids:
        panel_member = PanelMember(panel_id=panel.id, supervisor_id=supervisor_id)
        db.session.add(panel_member)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Panel created successfully'})

@app.route('/submit_evaluation', methods=['POST'])
@login_required
def submit_evaluation():
    if current_user.role != 'supervisor':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    supervisor = Supervisor.query.filter_by(user_id=current_user.id).first()
    if not supervisor:
        return jsonify({'success': False, 'message': 'Supervisor profile not found'})
    
    panel_id = request.json.get('panel_id')
    group_id = request.json.get('group_id')
    presentation_marks = float(request.json.get('presentation_marks', 0))
    documentation_marks = float(request.json.get('documentation_marks', 0))
    collaboration_marks = float(request.json.get('collaboration_marks', 0))
    innovation_marks = float(request.json.get('innovation_marks', 0))
    feedback_to_students = request.json.get('feedback_to_students', '')
    feedback_to_supervisor = request.json.get('feedback_to_supervisor', '')
    
    max_marks = 25
    if not (0 <= presentation_marks <= max_marks and 
            0 <= documentation_marks <= max_marks and 
            0 <= collaboration_marks <= max_marks and 
            0 <= innovation_marks <= max_marks):
        return jsonify({'success': False, 'message': f'Marks must be between 0 and {max_marks}'})
    
    total_marks = presentation_marks + documentation_marks + collaboration_marks + innovation_marks
    
    existing_evaluation = Evaluation.query.filter_by(
        panel_id=panel_id,
        group_id=group_id,
        evaluator_id=supervisor.id
    ).first()
    
    if existing_evaluation:
        existing_evaluation.presentation_marks = presentation_marks
        existing_evaluation.documentation_marks = documentation_marks
        existing_evaluation.collaboration_marks = collaboration_marks
        existing_evaluation.innovation_marks = innovation_marks
        existing_evaluation.total_marks = total_marks
        existing_evaluation.feedback_to_students = feedback_to_students
        existing_evaluation.feedback_to_supervisor = feedback_to_supervisor
    else:
        evaluation = Evaluation(
            panel_id=panel_id,
            group_id=group_id,
            evaluator_id=supervisor.id,
            presentation_marks=presentation_marks,
            documentation_marks=documentation_marks,
            collaboration_marks=collaboration_marks,
            innovation_marks=innovation_marks,
            total_marks=total_marks,
            feedback_to_students=feedback_to_students,
            feedback_to_supervisor=feedback_to_supervisor
        )
        db.session.add(evaluation)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Evaluation submitted successfully'})

@app.route('/assign_marks', methods=['POST'])
@login_required
def assign_marks():
    if current_user.role != 'supervisor':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    supervisor = Supervisor.query.filter_by(user_id=current_user.id).first()
    if not supervisor:
        return jsonify({'success': False, 'message': 'Supervisor profile not found'})
    
    student_id = request.json.get('student_id')
    presentation = float(request.json.get('presentation', 0))
    documents = float(request.json.get('documents', 0))
    collaboration = float(request.json.get('collaboration', 0))
    
    if not (0 <= presentation <= 10 and 0 <= documents <= 10 and 0 <= collaboration <= 10):
        return jsonify({'success': False, 'message': 'Marks must be between 0 and 10'})
    
    total = presentation + documents + collaboration
    
    existing_marks = Marks.query.filter_by(student_id=student_id, given_by=supervisor.id).first()
    
    if existing_marks:
        existing_marks.presentation = presentation
        existing_marks.documents = documents
        existing_marks.collaboration = collaboration
        existing_marks.total = total
    else:
        marks = Marks(
            student_id=student_id,
            presentation=presentation,
            documents=documents,
            collaboration=collaboration,
            total=total,
            given_by=supervisor.id
        )
        db.session.add(marks)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Marks assigned successfully'})

@app.route('/send_notification', methods=['POST'])
@login_required
def send_notification():
    if current_user.role != 'fic':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    fic = FIC.query.filter_by(user_id=current_user.id).first()
    if not fic:
        return jsonify({'success': False, 'message': 'FIC profile not found'})
    
    title = request.json.get('title')
    message = request.json.get('message')
    target_type = request.json.get('target_type', 'all')
    target_branch = request.json.get('target_branch')
    
    if not title or not message:
        return jsonify({'success': False, 'message': 'Title and message are required'})
    
    notification = Notification(
        title=title,
        message=message,
        target_type=target_type,
        target_branch=target_branch,
        created_by=fic.id
    )
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Notification created successfully'})

@app.route('/assign_supervisor', methods=['POST'])
@login_required
def assign_supervisor():
    if current_user.role != 'fic':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    group_id = request.json.get('group_id')
    supervisor_id = request.json.get('supervisor_id')
    
    fic = FIC.query.filter_by(user_id=current_user.id).first()
    if not fic:
        return jsonify({'success': False, 'message': 'FIC profile not found'})
    
    group = StudentGroup.query.get(group_id)
    supervisor = Supervisor.query.get(supervisor_id)
    
    if not group or not supervisor:
        return jsonify({'success': False, 'message': 'Group or supervisor not found'})
    
    if not any(student.school == fic.school for student in group.students):
        return jsonify({'success': False, 'message': 'Unauthorized to assign supervisor to this group'})
    
    supervised_groups_count = StudentGroup.query.filter_by(supervisor_id=supervisor.id).count()
    if supervised_groups_count >= supervisor.max_groups:
        return jsonify({'success': False, 'message': f'Supervisor can only supervise maximum {supervisor.max_groups} groups'})
    
    group.supervisor_id = supervisor.id
    
    SupervisorRequest.query.filter_by(
        group_id=group.id,
        status='pending'
    ).update({'status': 'rejected'})
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Supervisor assigned successfully'})

@app.route('/download_groups_csv')
@login_required
def download_groups_csv():
    try:
        if current_user.role != 'fic':
            flash('Unauthorized access', 'error')
            return redirect(url_for('index'))
        
        fic = FIC.query.filter_by(user_id=current_user.id).first()
        if not fic:
            flash('FIC profile not found', 'error')
            return redirect(url_for('index'))
        
        branch = request.args.get('branch')
        
        query = StudentGroup.query.join(Student).filter(Student.school == fic.school)
        
        if branch:
            query = query.filter(StudentGroup.branch == branch)
        
        groups = query.distinct().all()
        
        if not groups:
            flash('No groups found for download', 'info')
            return redirect(url_for('fic_dashboard'))
        
        output = io.BytesIO()
        wrapper = io.TextIOWrapper(output, encoding='utf-8-sig', newline='')
        writer = csv.writer(wrapper)
        
        writer.writerow(['Group Name', 'Branch', 'Year', 'Project Title', 'Supervisor', 
                         'WhatsApp Link', 'Student Name', 'Roll Number', 'Phone', 
                         'Mentor Name', 'Mentor Phone', 'Mentor Email'])
        
        for group in groups:
            supervisor_name = group.supervisor.name if group.supervisor else 'Not Assigned'
            for student in group.students:
                writer.writerow([
                    group.name,
                    group.branch,
                    group.year,
                    group.project_title or 'Not Set',
                    supervisor_name,
                    group.whatsapp_link or 'Not Set',
                    student.name,
                    student.roll_number,
                    student.phone_number or 'Not Provided',
                    student.mentor_name or 'Not Provided',
                    student.mentor_phone or 'Not Provided',
                    student.mentor_email or 'Not Provided'
                ])
        
        wrapper.flush()
        output.seek(0)
        wrapper.detach()
        
        filename = f'groups_{fic.school.replace(" ", "_")}'
        if branch:
            filename += f'_{branch}'
        filename += '.csv'
        
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"Error downloading CSV: {e}")
        flash(f'Error generating CSV: {str(e)}', 'error')
        return redirect(url_for('fic_dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    print("=" * 60)
    print("Starting Project Management System...")
    print("=" * 60)
    print(f"Database Type: {os.getenv('DATABASE_TYPE', 'postgresql')}")
    print(f"Database Host: {os.getenv('DB_HOST', 'localhost')}")
    
    with app.app_context():
        try:
            db.create_all()
            print("✅ Database tables verified/created successfully!")
        except Exception as e:
            print(f"⚠️ Database warning: {e}")
            print("Continuing with existing tables...")
    
    print("=" * 60)
    print("✅ Application started successfully!")
    port = int(os.getenv('PORT', 5000))
    print(f"🌐 Server running on port: {port}")
    print("=" * 60)
    app.run(debug=False, host='0.0.0.0', port=port)
