from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import secrets

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # student, supervisor, fic
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    student_profile = db.relationship('Student', backref='user', uselist=False, cascade='all, delete-orphan')
    supervisor_profile = db.relationship('Supervisor', backref='user', uselist=False, cascade='all, delete-orphan')
    fic_profile = db.relationship('FIC', backref='user', uselist=False, cascade='all, delete-orphan')

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(20), unique=True, nullable=False)
    year = db.Column(db.String(10), nullable=False)  # Third, Fourth
    school = db.Column(db.String(100), nullable=False)
    branch = db.Column(db.String(50), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('student_group.id'))
    
    # Relationships
    marks = db.relationship('Marks', backref='student', lazy=True, cascade='all, delete-orphan')
    sent_invites = db.relationship('GroupInvite', foreign_keys='GroupInvite.sender_id', backref='sender', lazy=True)
    received_invites = db.relationship('GroupInvite', foreign_keys='GroupInvite.receiver_id', backref='receiver', lazy=True)

class Supervisor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    domain = db.Column(db.String(50), nullable=False)
    school = db.Column(db.String(100), nullable=False)
    
    # Relationships
    supervised_groups = db.relationship('StudentGroup', backref='supervisor', lazy=True)
    panel_memberships = db.relationship('PanelMember', backref='supervisor', lazy=True, cascade='all, delete-orphan')
    given_marks = db.relationship('Marks', backref='given_by_supervisor', lazy=True)
    received_requests = db.relationship('SupervisorRequest', backref='supervisor', lazy=True)

class FIC(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    school = db.Column(db.String(100), nullable=False)
    
    # Relationships
    created_panels = db.relationship('Panel', backref='created_by_fic', lazy=True)

class StudentGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('supervisor.id'))
    project_title = db.Column(db.String(255))
    project_description = db.Column(db.Text)
    document_link = db.Column(db.String(500))
    branch = db.Column(db.String(50), nullable=False)
    year = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    students = db.relationship('Student', backref='group', lazy=True)
    supervisor_requests = db.relationship('SupervisorRequest', backref='group', lazy=True, cascade='all, delete-orphan')
    panels = db.relationship('Panel', backref='group', lazy=True, cascade='all, delete-orphan')

class SupervisorRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('student_group.id'), nullable=False)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('supervisor.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)

class GroupInvite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)

class Panel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('student_group.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('fic.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    members = db.relationship('PanelMember', backref='panel', lazy=True, cascade='all, delete-orphan')

class PanelMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    panel_id = db.Column(db.Integer, db.ForeignKey('panel.id'), nullable=False)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('supervisor.id'), nullable=False)

class Marks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    presentation = db.Column(db.Float, default=0)
    documents = db.Column(db.Float, default=0)
    collaboration = db.Column(db.Float, default=0)
    total = db.Column(db.Float, default=0)
    given_by = db.Column(db.Integer, db.ForeignKey('supervisor.id'), nullable=False)
    given_at = db.Column(db.DateTime, default=datetime.utcnow)

class OTP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    otp = db.Column(db.String(6), nullable=False)
    purpose = db.Column(db.String(20), default='registration')  # 'registration' or 'password_reset'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)