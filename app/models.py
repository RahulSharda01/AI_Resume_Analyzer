from datetime import datetime

from flask_login import UserMixin

from app import db


class User(UserMixin, db.Model):
    """Core user model for authentication and role-based access."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    last_login_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<User {self.username}>"


class Resume(db.Model):
    """Model for storing uploaded resume files and associated metadata."""

    __tablename__ = "resumes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False, unique=True)
    file_size = db.Column(db.Integer, nullable=False)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    extracted_text = db.Column(db.Text, nullable=True)
    ats_score = db.Column(db.Float, nullable=True)

    user = db.relationship("User", backref=db.backref("resumes", lazy=True))

    def __repr__(self):
        return f"<Resume {self.original_filename}>"


class JobDescriptionMatch(db.Model):
    """Stores job description matching results for a resume."""

    __tablename__ = "job_description_matches"

    id = db.Column(db.Integer, primary_key=True)
    resume_id = db.Column(db.Integer, db.ForeignKey("resumes.id"), nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    similarity_score = db.Column(db.Float, nullable=False)
    matched_skills = db.Column(db.Text, nullable=True)
    missing_skills = db.Column(db.Text, nullable=True)
    suggested_skills = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    resume = db.relationship("Resume", backref=db.backref("job_matches", lazy=True))

    def __repr__(self):
        return f"<JobDescriptionMatch {self.id}>"


class InterviewQuestionSet(db.Model):
    """Stores generated interview questions for a resume."""

    __tablename__ = "interview_question_sets"

    id = db.Column(db.Integer, primary_key=True)
    resume_id = db.Column(db.Integer, db.ForeignKey("resumes.id"), nullable=False)
    technical_questions = db.Column(db.Text, nullable=False)
    project_questions = db.Column(db.Text, nullable=False)
    hr_questions = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    resume = db.relationship("Resume", backref=db.backref("interview_question_sets", lazy=True))

    def __repr__(self):
        return f"<InterviewQuestionSet {self.id}>"


class AdminUser(db.Model):
    """Separate admin user store for platform administrators.

    Admins are stored separately from regular `User` accounts and have
    independent credentials and sessions.
    """

    __tablename__ = "admin_users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login_at = db.Column(db.DateTime, nullable=True)

    def set_password(self, pw: str):
        from werkzeug.security import generate_password_hash

        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw: str) -> bool:
        from werkzeug.security import check_password_hash

        return check_password_hash(self.password_hash, pw)

    def __repr__(self):
        return f"<AdminUser {self.username}>"
