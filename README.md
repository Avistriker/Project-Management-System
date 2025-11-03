
# Project Management System

A comprehensive web-based Project Management System designed for academic institutions to manage student projects, supervisors, and FIC (Faculty In Charge) coordination efficiently.

## 🚀 Features

### 👥 Multi-Role System
- Students: Form groups, invite members, request supervisors, submit projects

- Supervisors: Manage multiple student groups, assign marks, evaluate projects

- FIC (Faculty In Charge): Oversee school operations, create evaluation panels, send notifications

### 🔐 Authentication & Security
- Role-based access control

- OTP verification for registration and password reset

- Secure password hashing

- Session management

### 📋 Core Functionalities
- Group Management: Students can form groups (2-4 members) with same branch/year

- Supervisor Allocation: Request and manage supervisor assignments

- Project Submission: Upload project titles and document links

- Evaluation System: Supervisors can assign marks (Presentation, Documents, Collaboration)

- Panel Creation: FIC can create evaluation panels with 3 supervisors

- Notifications: FIC can send targeted notifications to users

- Supervisor Change Requests: Students can request supervisor changes with FIC approval

## 🛠️ Technology Stack

### Backend
- Flask - Python web framework

- Flask-Login - User session management

- Flask-SQLAlchemy - Database ORM

- Flask-Mail - Email functionality

- MySQL - Database

### Frontend
- HTML5 - Markup

- CSS3 - Styling

- JavaScript - Client-side functionality

- Jinja2 - Templating engine

### Deployment
- Render - Cloud platform

- Gunicorn - WSGI HTTP Server

## 📦 Installation & Setup
### Prerequisites
- Python 3.8+

- MySQL 5.7+

- Git

## Local Development
#### 1. Clone the repository
```
git clone https://github.com/yourusername/project-management-system.git
cd project-management-system

```

#### 2. Create virtual environment

```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 3. Install dependencies

```
pip install -r requirements.txt
```

#### 4. Set up environment variables

> Create a ``` .env ``` file in the root directory:

```
SECRET_KEY=your-secret-key-here
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your-mysql-password
MYSQL_DB=project_management_system
MYSQL_PORT=3306
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

#### 5. Set up MySQL Database
```
python database_setup.py
```

#### 6. Run the application

```
python app.py
```

## Production Deployment on Render

### Prepare for deployment

- Ensure all files are committed to GitHub

- Update environment variables in Render dashboard

- Set up Gmail App Password for email functionality

### Automatic deployment

- Connect your GitHub repository to Render

- Render will automatically deploy using render.yaml

### Manual deployment steps

- Create a new Web Service on Render

- Connect your GitHub repository

- Set build command: pip install -r requirements.txt

- Set start command: gunicorn app:app --bind 0.0.0.0:$PORT

- Configure environment variables

## 🗄️ Database Schema

### Main Tables

```
user - Base user accounts with roles

student - Student profiles and information

supervisor - Supervisor profiles and domains

fic - FIC profiles

student_group - Group information and projects

group_invite - Group invitation management

supervisor_request - Supervisor assignment requests

marks - Evaluation marks and scores

panel & panel_member - Evaluation panels

otp - OTP management for verification

notification - System notifications
```

## 👨‍💻 User Guides

### Student Registration & Usage

- Register as a student with valid institutional email

- Verify email using OTP sent to your inbox

- Form groups by inviting other students from same branch/year

- Request supervisors (max 5 requests)

- Submit project details and document links

- View marks assigned by supervisors

### Supervisor Registration & Usage

- Register as a supervisor with institutional credentials

- Set domain expertise (ML, IOT, VLSI, etc.)

- Accept/Reject supervisor requests from student groups

- Assign marks to students in supervised groups

- Manage up to 3 groups simultaneously

### FIC Registration & Usage

- Register as FIC (limited to 6 per school)

- Oversee operations for your school

- Create evaluation panels with 3 supervisors

- Send notifications to targeted audiences

- Approve/Reject supervisor change requests

- Download group details as CSV reports

## 🔧 Configuration

### Email Setup (Gmail)
#### 1. Enable 2-Factor Authentication on your Gmail account

#### 2. Generate an App Password:

#### 3. Go to Google Account → Security → 2-Step Verification → App passwords

#### 4. Generate password for "Mail"

#### 5. Use this password in MAIL_PASSWORD environment variable

### Database Configuration

> The system uses MySQL with the following default configuration:

- Host: localhost

- Port: 3306

- Database: project_management_system

- Character Set: utf8mb4

## 🚀 API Endpoints

### Authentication

- ``` GET/POST /login``` - User login

- ``` GET/POST /register``` - Role selection

- ```GET/POST /forgot_password``` - Password reset initiation

- ```GET/POST /reset_password/<email>``` - Password reset with OTP

- ```POST /send_otp``` - OTP sending API

### Student Routes

- ``` GET /student/dashboard ``` - Student dashboard

- ``` POST /send_invite``` - Send group invitation

- ``` POST /respond_invite``` - Accept/Reject invitation

- ``` POST /request_supervisor ``` - Request supervisor

- ``` POST /leave_group ```- Leave current group

### Supervisor Routes

- ``` GET /supervisor/dashboard``` - Supervisor dashboard

- ``` POST /respond_supervisor_request``` - Handle supervisor requests

- ``` POST /assign_marks``` - Assign marks to students


### FIC Routes

- ``` GET /fic/dashboard``` - FIC dashboard

- ``` POST /create_panel``` - Create evaluation panel

- ``` POST /send_notification``` - Send notifications

- ``` GET /download_group_details``` - Export group data


## 🙏 Acknowledgments
- Flask community for excellent documentation

- Render for free hosting services

- MySQL for robust database solutions