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

# Database configuration for Render PostgreSQL
database_url = os.getenv('DATABASE_URL')

if database_url:
    # Use PostgreSQL on Render
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace('postgres://', 'postgresql://')
else:
    # Fallback to SQLite for local development
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project_management.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 300,
    'pool_pre_ping': True
}

# Email configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', '')

db = SQLAlchemy(app)
mail = Mail(app)

# Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models (Keep your existing models as they are)
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
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
    status = db.Column(db.String(20), default='pending')
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
    purpose = db.Column(db.String(20), default='registration')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    fic = db.relationship('FIC', backref='sent_notifications')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize database
def init_db():
    with app.app_context():
        try:
            db.create_all()
            print("✅ Database tables created successfully!")
        except Exception as e:
            print(f"❌ Error creating database tables: {e}")

# Routes (Keep all your existing routes as they are)
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
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
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
            msg.body = f'''You have requested to reset your password for the Project Management System.

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
        return jsonify({'success': True, 'message': 'If this email exists, a password reset OTP has been sent.'})
    
    otp_code = ''.join(secrets.choice('0123456789') for _ in range(6))
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
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
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('student_registration.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('student_registration.html')
        
        if Student.query.filter_by(roll_number=roll_number).first():
            flash('Roll number already registered', 'error')
            return render_template('student_registration.html')
        
        otp_record = OTP.query.filter_by(email=email, purpose='registration', used=False).order_by(OTP.created_at.desc()).first()
        if not otp_record or otp_record.otp != otp or otp_record.expires_at < datetime.utcnow():
            flash('Invalid or expired OTP', 'error')
            return render_template('student_registration.html')
        
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
            branch=branch
        )
        db.session.add(student)
        
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
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('supervisor_registration.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('supervisor_registration.html')
        
        otp_record = OTP.query.filter_by(email=email, purpose='registration', used=False).order_by(OTP.created_at.desc()).first()
        if not otp_record or otp_record.otp != otp or otp_record.expires_at < datetime.utcnow():
            flash('Invalid or expired OTP', 'error')
            return render_template('supervisor_registration.html')
        
        hashed_password = generate_password_hash(password)
        user = User(email=email, password=hashed_password, role='supervisor')
        db.session.add(user)
        db.session.flush()
        
        supervisor = Supervisor(
            user_id=user.id,
            name=name,
            domain=domain,
            school=school
        )
        db.session.add(supervisor)
        
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
        
        otp_record = OTP.query.filter_by(email=email, purpose='registration', used=False).order_by(OTP.created_at.desc()).first()
        if not otp_record or otp_record.otp != otp or otp_record.expires_at < datetime.utcnow():
            flash('Invalid or expired OTP', 'error')
            return render_template('fic_registration.html')
        
        hashed_password = generate_password_hash(password)
        user = User(email=email, password=hashed_password, role='fic')
        db.session.add(user)
        db.session.flush()
        
        fic = FIC(
            user_id=user.id,
            name=name,
            school=school
        )
        db.session.add(fic)
        
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
    
    otp_code = ''.join(secrets.choice('0123456789') for _ in range(6))
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    otp = OTP(
        email=email, 
        otp=otp_code, 
        purpose=purpose,
        expires_at=expires_at
    )
    db.session.add(otp)
    db.session.commit()
    
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
    
    available_students = Student.query.filter(
        Student.year == student.year,
        Student.branch == student.branch,
        Student.group_id.is_(None),
        Student.id != student.id
    ).all()
    
    available_supervisors = Supervisor.query.filter_by(school=student.school).all()
    
    supervisor_change_requests = []
    if group and group.supervisor_id:
        supervisor_change_requests = SupervisorChangeRequest.query.filter_by(
            group_id=group.id
        ).all()
    
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
    
    supervisor_change_requests = SupervisorChangeRequest.query.filter_by(
        current_supervisor_id=supervisor.id,
        status='pending'
    ).all()
    
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
    
    school_groups = StudentGroup.query.join(Student).filter(Student.school == fic.school).distinct().all()
    school_supervisors = Supervisor.query.filter_by(school=fic.school).all()
    
    supervisor_change_requests = SupervisorChangeRequest.query.join(
        StudentGroup
    ).join(
        Student
    ).filter(
        Student.school == fic.school,
        SupervisorChangeRequest.status == 'pending'
    ).all()
    
    notifications = Notification.query.filter_by(created_by=fic.id).order_by(Notification.created_at.desc()).limit(10).all()
    
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

# Add all your other routes here (send_invite, respond_invite, leave_group, etc.)
# Keep them exactly as they were in your original code

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

# Initialize database when app starts
init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
