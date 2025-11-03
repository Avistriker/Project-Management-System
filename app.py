from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import secrets
import os
from dotenv import load_dotenv
import csv
from io import StringIO

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', '08d8440116c5b8b558bd90d064310f2aeb9846ae028c3c89b66d4e289baa5fbe')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql://{os.getenv('MYSQL_USER', 'root')}:{os.getenv('MYSQL_PASSWORD', '')}@{os.getenv('MYSQL_HOST', 'localhost')}:{os.getenv('MYSQL_PORT', '3306')}/{os.getenv('MYSQL_DB', 'project_management_system')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', '2230239@kiit.ac.in')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'yvuv nhba anal xcwj')

db = SQLAlchemy(app)
mail = Mail(app)

# Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Flask-Login required methods
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
    group_id = db.Column(db.Integer, db.ForeignKey('student_group.id'))
    
    user = db.relationship('User', backref=db.backref('student', uselist=False))
    group = db.relationship('StudentGroup', backref=db.backref('students', lazy=True))

class Supervisor(db.Model):
    __tablename__ = 'supervisor'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    domain = db.Column(db.String(50), nullable=False)
    school = db.Column(db.String(100), nullable=False)
    
    user = db.relationship('User', backref=db.backref('supervisor', uselist=False))
    supervised_groups = db.relationship('StudentGroup', backref='supervisor', lazy=True)

class FIC(db.Model):
    __tablename__ = 'fic'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    school = db.Column(db.String(100), nullable=False)
    
    user = db.relationship('User', backref=db.backref('fic', uselist=False))

class StudentGroup(db.Model):
    __tablename__ = 'student_group'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('supervisor.id'))
    project_title = db.Column(db.String(255))
    project_description = db.Column(db.Text)
    document_link = db.Column(db.String(500))
    branch = db.Column(db.String(50), nullable=False)
    year = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class GroupInvite(db.Model):
    __tablename__ = 'group_invite'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    sender = db.relationship('Student', foreign_keys=[sender_id], backref='sent_invites')
    receiver = db.relationship('Student', foreign_keys=[receiver_id], backref='received_invites')

class SupervisorRequest(db.Model):
    __tablename__ = 'supervisor_request'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('student_group.id'), nullable=False)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('supervisor.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    group = db.relationship('StudentGroup', backref='supervisor_requests')
    supervisor = db.relationship('Supervisor', backref='received_requests')

class SupervisorChangeRequest(db.Model):
    __tablename__ = 'supervisor_change_request'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('student_group.id'), nullable=False)
    current_supervisor_id = db.Column(db.Integer, db.ForeignKey('supervisor.id'), nullable=False)
    new_supervisor_id = db.Column(db.Integer, db.ForeignKey('supervisor.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    
    group = db.relationship('StudentGroup', backref='supervisor_change_requests')
    current_supervisor = db.relationship('Supervisor', foreign_keys=[current_supervisor_id])
    new_supervisor = db.relationship('Supervisor', foreign_keys=[new_supervisor_id])

class Panel(db.Model):
    __tablename__ = 'panel'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('student_group.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('fic.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    group = db.relationship('StudentGroup', backref='panels')
    fic = db.relationship('FIC', backref='created_panels')

class PanelMember(db.Model):
    __tablename__ = 'panel_member'
    id = db.Column(db.Integer, primary_key=True)
    panel_id = db.Column(db.Integer, db.ForeignKey('panel.id'), nullable=False)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('supervisor.id'), nullable=False)
    
    panel = db.relationship('Panel', backref='members')
    supervisor = db.relationship('Supervisor', backref='panel_memberships')

class Marks(db.Model):
    __tablename__ = 'marks'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    presentation = db.Column(db.Float, default=0)
    documents = db.Column(db.Float, default=0)
    collaboration = db.Column(db.Float, default=0)
    total = db.Column(db.Float, default=0)
    given_by = db.Column(db.Integer, db.ForeignKey('supervisor.id'), nullable=False)
    given_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    student = db.relationship('Student', backref='marks')
    supervisor_given = db.relationship('Supervisor', backref='given_marks')

class OTP(db.Model):
    __tablename__ = 'otp'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    otp = db.Column(db.String(6), nullable=False)
    purpose = db.Column(db.String(20), default='registration')  # 'registration' or 'password_reset'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)

class Notification(db.Model):
    __tablename__ = 'notification'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    target_type = db.Column(db.String(20), nullable=False)  # all, students, supervisors, specific_branch
    target_branch = db.Column(db.String(50))
    created_by = db.Column(db.Integer, db.ForeignKey('fic.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    fic = db.relationship('FIC', backref='sent_notifications')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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
            
            # Redirect based on role
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
            # Don't reveal whether email exists for security
            flash('If this email exists, a password reset OTP has been sent.', 'info')
            return render_template('forgot_password.html')
        
        # Generate OTP for password reset
        otp_code = ''.join(secrets.choice('0123456789') for _ in range(6))
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        # Save OTP to database with purpose 'password_reset'
        otp = OTP(
            email=email, 
            otp=otp_code, 
            purpose='password_reset',
            expires_at=expires_at
        )
        db.session.add(otp)
        db.session.commit()
        
        # Send OTP email
        try:
            msg = Message('Password Reset OTP - Project Management System', 
                         sender=app.config['MAIL_USERNAME'], 
                         recipients=[email])
            msg.body = f'''You have requested to reset your password for the Project Management System.

Your OTP for password reset is: {otp_code}

This OTP will expire in 10 minutes.

If you did not request a password reset, please ignore this email.
'''
            mail.send(msg)
            flash('Password reset OTP has been sent to your email.', 'success')
            # Redirect to reset password page with email
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
        
        # Verify OTP
        otp_record = OTP.query.filter_by(
            email=email, 
            purpose='password_reset', 
            used=False
        ).order_by(OTP.created_at.desc()).first()
        
        if not otp_record or otp_record.otp != otp or otp_record.expires_at < datetime.utcnow():
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
        # Don't reveal whether email exists
        return jsonify({'success': True, 'message': 'If this email exists, a password reset OTP has been sent.'})
    
    # Generate OTP
    otp_code = ''.join(secrets.choice('0123456789') for _ in range(6))
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    # Save OTP to database with password_reset purpose
    otp = OTP(
        email=email, 
        otp=otp_code, 
        purpose='password_reset',
        expires_at=expires_at
    )
    db.session.add(otp)
    db.session.commit()
    
    # Send email
    try:
        msg = Message('Password Reset OTP - Project Management System', 
                     sender=app.config['MAIL_USERNAME'], 
                     recipients=[email])
        msg.body = f'''You have requested to reset your password for the Project Management System.

Your OTP for password reset is: {otp_code}

This OTP will expire in 10 minutes.

If you did not request a password reset, please ignore this email.
'''
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
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        otp = request.form.get('otp')
        
        # Validation
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('student_registration.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('student_registration.html')
        
        if Student.query.filter_by(roll_number=roll_number).first():
            flash('Roll number already registered', 'error')
            return render_template('student_registration.html')
        
        # Verify OTP
        otp_record = OTP.query.filter_by(email=email, purpose='registration', used=False).order_by(OTP.created_at.desc()).first()
        if not otp_record or otp_record.otp != otp or otp_record.expires_at < datetime.utcnow():
            flash('Invalid or expired OTP', 'error')
            return render_template('student_registration.html')
        
        # Create user
        hashed_password = generate_password_hash(password)
        user = User(email=email, password=hashed_password, role='student')
        db.session.add(user)
        db.session.flush()  # Get user ID without committing
        
        # Create student profile
        student = Student(
            user_id=user.id,
            name=name,
            roll_number=roll_number,
            year=year,
            school=school,
            branch=branch
        )
        db.session.add(student)
        
        # Mark OTP as used
        otp_record.used = True
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
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
        otp = request.form.get('otp')
        
        # Validation
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('supervisor_registration.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('supervisor_registration.html')
        
        # Verify OTP
        otp_record = OTP.query.filter_by(email=email, purpose='registration', used=False).order_by(OTP.created_at.desc()).first()
        if not otp_record or otp_record.otp != otp or otp_record.expires_at < datetime.utcnow():
            flash('Invalid or expired OTP', 'error')
            return render_template('supervisor_registration.html')
        
        # Create user
        hashed_password = generate_password_hash(password)
        user = User(email=email, password=hashed_password, role='supervisor')
        db.session.add(user)
        db.session.flush()
        
        # Create supervisor profile
        supervisor = Supervisor(
            user_id=user.id,
            name=name,
            domain=domain,
            school=school
        )
        db.session.add(supervisor)
        
        # Mark OTP as used
        otp_record.used = True
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('supervisor_registration.html')

@app.route('/register/fic', methods=['GET', 'POST'])
def fic_registration():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        school = request.form.get('school')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        otp = request.form.get('otp')
        
        # Validation
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('fic_registration.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('fic_registration.html')
        
        # Check FIC limit per school
        fic_count = FIC.query.filter_by(school=school).count()
        if fic_count >= 6:
            flash('Maximum FIC limit reached for this school', 'error')
            return render_template('fic_registration.html')
        
        # Verify OTP
        otp_record = OTP.query.filter_by(email=email, purpose='registration', used=False).order_by(OTP.created_at.desc()).first()
        if not otp_record or otp_record.otp != otp or otp_record.expires_at < datetime.utcnow():
            flash('Invalid or expired OTP', 'error')
            return render_template('fic_registration.html')
        
        # Create user
        hashed_password = generate_password_hash(password)
        user = User(email=email, password=hashed_password, role='fic')
        db.session.add(user)
        db.session.flush()
        
        # Create FIC profile
        fic = FIC(
            user_id=user.id,
            name=name,
            school=school
        )
        db.session.add(fic)
        
        # Mark OTP as used
        otp_record.used = True
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('fic_registration.html')

@app.route('/send_otp', methods=['POST'])
def send_otp():
    email = request.json.get('email')
    purpose = request.json.get('purpose', 'registration')
    
    if not email:
        return jsonify({'success': False, 'message': 'Email is required'})
    
    # Generate OTP
    otp_code = ''.join(secrets.choice('0123456789') for _ in range(6))
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    # Save OTP to database
    otp = OTP(
        email=email, 
        otp=otp_code, 
        purpose=purpose,
        expires_at=expires_at
    )
    db.session.add(otp)
    db.session.commit()
    
    # Send email
    try:
        if purpose == 'password_reset':
            subject = 'Password Reset OTP - Project Management System'
            body = f'''You have requested to reset your password for the Project Management System.

Your OTP for password reset is: {otp_code}

This OTP will expire in 10 minutes.

If you did not request a password reset, please ignore this email.
'''
        else:
            subject = 'Your OTP for Registration - Project Management System'
            body = f'Your OTP for registration is: {otp_code}. It will expire in 10 minutes.'
        
        msg = Message(subject, sender=app.config['MAIL_USERNAME'], recipients=[email])
        msg.body = body
        mail.send(msg)
        return jsonify({'success': True, 'message': 'OTP sent successfully'})
    except Exception as e:
        print(f"Email error: {e}")
        return jsonify({'success': False, 'message': 'Failed to send OTP'})

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
    
    if student.group_id:
        group = StudentGroup.query.get(student.group_id)
        group_members = Student.query.filter_by(group_id=student.group_id).all()
    
    # Get students for inviting (same year and branch, not in any group)
    available_students = Student.query.filter(
        Student.year == student.year,
        Student.branch == student.branch,
        Student.group_id.is_(None),
        Student.id != student.id
    ).all()
    
    # Get available supervisors for the student's school
    available_supervisors = Supervisor.query.filter_by(school=student.school).all()
    
    # Get supervisor change requests for the group
    supervisor_change_requests = []
    if group and group.supervisor_id:
        supervisor_change_requests = SupervisorChangeRequest.query.filter_by(
            group_id=group.id
        ).all()
    
    # Get notifications
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
                          available_students=available_students,
                          available_supervisors=available_supervisors,
                          supervisor_change_requests=supervisor_change_requests,
                          notifications=notifications)

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
    
    # Get supervisor change requests where this supervisor is the current supervisor
    supervisor_change_requests = SupervisorChangeRequest.query.filter_by(
        current_supervisor_id=supervisor.id,
        status='pending'
    ).all()
    
    # Get notifications
    notifications = Notification.query.filter(
        (Notification.target_type == 'all') |
        (Notification.target_type == 'supervisors')
    ).order_by(Notification.created_at.desc()).limit(10).all()
    
    return render_template('supervisor_dashboard.html', 
                          supervisor=supervisor,
                          supervised_groups=supervised_groups,
                          pending_requests=pending_requests,
                          supervisor_change_requests=supervisor_change_requests,
                          notifications=notifications)

@app.route('/fic/dashboard')
@login_required
def fic_dashboard():
    if current_user.role != 'fic':
        return redirect(url_for('index'))
    
    fic = FIC.query.filter_by(user_id=current_user.id).first()
    if not fic:
        flash('FIC profile not found', 'error')
        return redirect(url_for('logout'))
    
    # Get all groups from the same school
    school_groups = StudentGroup.query.join(Student).filter(Student.school == fic.school).distinct().all()
    school_supervisors = Supervisor.query.filter_by(school=fic.school).all()
    
    # Get supervisor change requests for the school
    supervisor_change_requests = SupervisorChangeRequest.query.join(
        StudentGroup
    ).join(
        Student
    ).filter(
        Student.school == fic.school,
        SupervisorChangeRequest.status == 'pending'
    ).all()
    
    # Get sent notifications
    notifications = Notification.query.filter_by(created_by=fic.id).order_by(Notification.created_at.desc()).limit(10).all()
    
    # Get all branches in the school for download
    branches = db.session.query(StudentGroup.branch).filter(
        StudentGroup.id.in_([g.id for g in school_groups])
    ).distinct().all()
    branches = [b[0] for b in branches]
    
    return render_template('fic_dashboard.html', 
                          fic=fic,
                          school_groups=school_groups,
                          school_supervisors=school_supervisors,
                          supervisor_change_requests=supervisor_change_requests,
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
    
    # Check if student is already in a group
    if student.group_id:
        # Check if group has less than 4 members
        group_members_count = Student.query.filter_by(group_id=student.group_id).count()
        if group_members_count >= 4:
            return jsonify({'success': False, 'message': 'Your group already has maximum 4 members'})
    
    # Check if receiver exists and is available
    receiver = Student.query.get(receiver_id)
    if not receiver or receiver.group_id or receiver.year != student.year or receiver.branch != student.branch:
        return jsonify({'success': False, 'message': 'Invalid student'})
    
    # Check if invite already exists
    existing_invite = GroupInvite.query.filter_by(
        sender_id=student.id, 
        receiver_id=receiver_id, 
        status='pending'
    ).first()
    
    if existing_invite:
        return jsonify({'success': False, 'message': 'Invite already sent'})
    
    # Create invite
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
    action = request.json.get('action')  # 'accept' or 'reject'
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        return jsonify({'success': False, 'message': 'Student profile not found'})
    
    invite = GroupInvite.query.get(invite_id)
    
    if not invite or invite.receiver_id != student.id:
        return jsonify({'success': False, 'message': 'Invalid invite'})
    
    if action == 'accept':
        # Check if student is already in a group
        if student.group_id:
            # Check if group has less than 4 members
            group_members_count = Student.query.filter_by(group_id=student.group_id).count()
            if group_members_count >= 4:
                return jsonify({'success': False, 'message': 'Your group already has maximum 4 members'})
        
        # Check if sender is still available or in a group with less than 4 members
        sender = Student.query.get(invite.sender_id)
        if not sender:
            return jsonify({'success': False, 'message': 'Sender not found'})
        
        # Create or join group
        if sender.group_id:
            # Join existing group (check if group has less than 4 members)
            group_members_count = Student.query.filter_by(group_id=sender.group_id).count()
            if group_members_count >= 4:
                return jsonify({'success': False, 'message': 'The group already has maximum 4 members'})
            
            student.group_id = sender.group_id
            group = StudentGroup.query.get(sender.group_id)
        else:
            # Create new group
            group_count = StudentGroup.query.filter_by(branch=student.branch).count()
            group_name = f"{student.branch}{group_count + 1:02d}"
            
            group = StudentGroup(name=group_name, branch=student.branch, year=student.year)
            db.session.add(group)
            db.session.flush()  # Get group ID
            
            sender.group_id = group.id
            student.group_id = group.id
        
        invite.status = 'accepted'
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Invite accepted'})
    
    elif action == 'reject':
        invite.status = 'rejected'
        db.session.commit()
        return jsonify({'success': True, 'message': 'Invite rejected'})
    
    return jsonify({'success': False, 'message': 'Invalid action'})

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
    
    # Check if this is the last member
    remaining_members = Student.query.filter_by(group_id=student.group_id).filter(Student.id != student.id).count()
    
    if remaining_members == 0:
        # Last member leaving - delete the group and related data
        # Delete supervisor requests
        SupervisorRequest.query.filter_by(group_id=group.id).delete()
        # Delete supervisor change requests
        SupervisorChangeRequest.query.filter_by(group_id=group.id).delete()
        # Delete the group
        db.session.delete(group)
    else:
        # Remove student from group
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
    
    # Check if group already has a supervisor
    if group.supervisor_id:
        return jsonify({'success': False, 'message': 'Your group already has a supervisor'})
    
    # Check if request limit reached (max 5)
    existing_requests = SupervisorRequest.query.filter_by(group_id=group.id).count()
    if existing_requests >= 5:
        return jsonify({'success': False, 'message': 'Maximum request limit reached'})
    
    # Check if request already sent
    existing_request = SupervisorRequest.query.filter_by(
        group_id=group.id, 
        supervisor_id=supervisor_id
    ).first()
    
    if existing_request:
        return jsonify({'success': False, 'message': 'Request already sent to this supervisor'})
    
    # Create request
    request_obj = SupervisorRequest(group_id=group.id, supervisor_id=supervisor_id)
    db.session.add(request_obj)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Request sent successfully'})

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
    
    if not new_supervisor_id:
        return jsonify({'success': False, 'message': 'Please select a new supervisor'})
    
    if int(new_supervisor_id) == group.supervisor_id:
        return jsonify({'success': False, 'message': 'New supervisor cannot be the same as current supervisor'})
    
    # Check if request already exists
    existing_request = SupervisorChangeRequest.query.filter_by(
        group_id=group.id,
        status='pending'
    ).first()
    
    if existing_request:
        return jsonify({'success': False, 'message': 'A supervisor change request is already pending'})
    
    # Create supervisor change request
    change_request = SupervisorChangeRequest(
        group_id=group.id,
        current_supervisor_id=group.supervisor_id,
        new_supervisor_id=new_supervisor_id,
        reason=reason
    )
    db.session.add(change_request)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Supervisor change request submitted to FIC'})

@app.route('/respond_supervisor_request', methods=['POST'])
@login_required
def respond_supervisor_request():
    if current_user.role != 'supervisor':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    request_id = request.json.get('request_id')
    action = request.json.get('action')  # 'accept' or 'reject'
    
    supervisor = Supervisor.query.filter_by(user_id=current_user.id).first()
    if not supervisor:
        return jsonify({'success': False, 'message': 'Supervisor profile not found'})
    
    request_obj = SupervisorRequest.query.get(request_id)
    
    if not request_obj or request_obj.supervisor_id != supervisor.id:
        return jsonify({'success': False, 'message': 'Invalid request'})
    
    if action == 'accept':
        # Check if supervisor can accept more groups (max 3)
        supervised_groups = StudentGroup.query.filter_by(supervisor_id=supervisor.id).count()
        if supervised_groups >= 3:
            return jsonify({'success': False, 'message': 'You can only supervise up to 3 groups'})
        
        # Check if group already has a supervisor
        group = StudentGroup.query.get(request_obj.group_id)
        if group.supervisor_id:
            return jsonify({'success': False, 'message': 'Group already has a supervisor'})
        
        # Assign supervisor to group
        group.supervisor_id = supervisor.id
        request_obj.status = 'accepted'
        
        # Reject other pending requests for this group
        other_requests = SupervisorRequest.query.filter_by(
            group_id=group.id, 
            status='pending'
        ).all()
        
        for req in other_requests:
            if req.id != request_id:
                req.status = 'rejected'
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Request accepted'})
    
    elif action == 'reject':
        request_obj.status = 'rejected'
        db.session.commit()
        return jsonify({'success': True, 'message': 'Request rejected'})
    
    return jsonify({'success': False, 'message': 'Invalid action'})

@app.route('/respond_supervisor_change_request', methods=['POST'])
@login_required
def respond_supervisor_change_request():
    if current_user.role != 'fic':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    fic = FIC.query.filter_by(user_id=current_user.id).first()
    if not fic:
        return jsonify({'success': False, 'message': 'FIC profile not found'})
    
    request_id = request.json.get('request_id')
    action = request.json.get('action')  # 'approve' or 'reject'
    
    change_request = SupervisorChangeRequest.query.get(request_id)
    if not change_request:
        return jsonify({'success': False, 'message': 'Invalid request'})
    
    # Verify the group belongs to FIC's school
    group = StudentGroup.query.get(change_request.group_id)
    if not group or not group.students or group.students[0].school != fic.school:
        return jsonify({'success': False, 'message': 'Invalid group'})
    
    if action == 'approve':
        # Check if new supervisor can accept more groups
        supervised_groups = StudentGroup.query.filter_by(supervisor_id=change_request.new_supervisor_id).count()
        if supervised_groups >= 3:
            return jsonify({'success': False, 'message': 'New supervisor can only supervise up to 3 groups'})
        
        # Update group supervisor
        group.supervisor_id = change_request.new_supervisor_id
        change_request.status = 'approved'
        
        # Reject any other pending supervisor requests for this group
        other_requests = SupervisorRequest.query.filter_by(
            group_id=group.id,
            status='pending'
        ).all()
        
        for req in other_requests:
            req.status = 'rejected'
        
    elif action == 'reject':
        change_request.status = 'rejected'
    
    change_request.processed_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Supervisor change request {action}d'})

@app.route('/update_project_title', methods=['POST'])
@login_required
def update_project_title():
    if current_user.role != 'student':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        return jsonify({'success': False, 'message': 'Student profile not found'})
    
    group = StudentGroup.query.get(student.group_id)
    
    if not group:
        return jsonify({'success': False, 'message': 'You are not in a group'})
    
    new_title = request.json.get('title')
    group.project_title = new_title
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Project title updated'})

@app.route('/update_document_link', methods=['POST'])
@login_required
def update_document_link():
    if current_user.role != 'student':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        return jsonify({'success': False, 'message': 'Student profile not found'})
    
    group = StudentGroup.query.get(student.group_id)
    
    if not group:
        return jsonify({'success': False, 'message': 'You are not in a group'})
    
    new_link = request.json.get('link')
    group.document_link = new_link
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Document link updated'})

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
    
    student = Student.query.get(student_id)
    if not student or not student.group or student.group.supervisor_id != supervisor.id:
        return jsonify({'success': False, 'message': 'Invalid student'})
    
    total = presentation + documents + collaboration
    
    # Check if marks already exist
    marks = Marks.query.filter_by(student_id=student_id, given_by=supervisor.id).first()
    if marks:
        marks.presentation = presentation
        marks.documents = documents
        marks.collaboration = collaboration
        marks.total = total
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

@app.route('/create_panel', methods=['POST'])
@login_required
def create_panel():
    if current_user.role != 'fic':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    fic = FIC.query.filter_by(user_id=current_user.id).first()
    if not fic:
        return jsonify({'success': False, 'message': 'FIC profile not found'})
    
    group_id = request.json.get('group_id')
    supervisor_ids = request.json.get('supervisor_ids')  # List of 3 supervisor IDs
    
    if len(supervisor_ids) != 3:
        return jsonify({'success': False, 'message': 'Exactly 3 panel members required'})
    
    group = StudentGroup.query.get(group_id)
    if not group or not group.students or group.students[0].school != fic.school:
        return jsonify({'success': False, 'message': 'Invalid group'})
    
    # Check if panel already exists
    existing_panel = Panel.query.filter_by(group_id=group_id).first()
    if existing_panel:
        return jsonify({'success': False, 'message': 'Panel already exists for this group'})
    
    # Create panel
    panel = Panel(group_id=group_id, created_by=fic.id)
    db.session.add(panel)
    db.session.flush()  # Get panel ID
    
    # Add panel members (can include the group's supervisor)
    for supervisor_id in supervisor_ids:
        panel_member = PanelMember(panel_id=panel.id, supervisor_id=supervisor_id)
        db.session.add(panel_member)
    
    db.session.commit()
    return jsonify({'success': True, 'message': 'Panel created successfully'})

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
    target_type = request.json.get('target_type')
    target_branch = request.json.get('target_branch')
    
    if not title or not message:
        return jsonify({'success': False, 'message': 'Title and message are required'})
    
    # Create notification
    notification = Notification(
        title=title,
        message=message,
        target_type=target_type,
        target_branch=target_branch if target_type == 'specific_branch' else None,
        created_by=fic.id
    )
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Notification sent successfully'})

@app.route('/download_group_details')
@login_required
def download_group_details():
    if current_user.role != 'fic':
        return redirect(url_for('index'))
    
    fic = FIC.query.filter_by(user_id=current_user.id).first()
    if not fic:
        flash('FIC profile not found', 'error')
        return redirect(url_for('logout'))
    
    branch = request.args.get('branch', '')
    
    # Get groups from the same school, optionally filtered by branch
    query = StudentGroup.query.join(Student).filter(Student.school == fic.school)
    if branch:
        query = query.filter(StudentGroup.branch == branch)
    
    school_groups = query.order_by(StudentGroup.name).all()
    
    # Create CSV content
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Group Name', 'Branch', 'Year', 'Project Title', 'Supervisor', 'Member Names', 'Roll Numbers'])
    
    # Write data
    for group in school_groups:
        member_names = ', '.join([student.name for student in group.students])
        roll_numbers = ', '.join([student.roll_number for student in group.students])
        supervisor_name = group.supervisor.name if group.supervisor else 'Not assigned'
        
        writer.writerow([
            group.name,
            group.branch,
            group.year,
            group.project_title or 'Not set',
            supervisor_name,
            member_names,
            roll_numbers
        ])
    
    # Prepare response
    output.seek(0)
    filename = f"group_details_{fic.school.replace(' ', '_')}"
    if branch:
        filename += f"_{branch}"
    filename += ".csv"
    
    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500



# Update the main block to this:
if __name__ == '__main__':
    with app.app_context():
        # This will create all tables when the app starts
        db.create_all()
        print("Database tables created successfully")
    
    # Use environment variable for port (Render provides this)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)