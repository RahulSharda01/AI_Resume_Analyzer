import os
from functools import wraps
from datetime import datetime

from flask import (
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from werkzeug.utils import secure_filename

from app import db
from app.admin import admin_bp
from app.admin.forms import AdminLoginForm
from app.models import (
    AdminUser,
    JobDescriptionMatch,
    InterviewQuestionSet,
    Resume,
    User,
)
from app.resume.report_service import ResumeReportService


def admin_login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_user_id"):
            return redirect(url_for("admin.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def _get_page_number(default: int = 1) -> int:
    try:
        page = int(request.args.get("page", default))
    except (TypeError, ValueError):
        page = default
    return max(page, 1)


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    """Admin login (separate from normal user authentication)."""
    form = AdminLoginForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data
        admin = AdminUser.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            session["admin_user_id"] = admin.id
            session["admin_username"] = admin.username
            admin.last_login_at = datetime.utcnow()
            db.session.commit()
            flash("Admin signed in.", "success")
            next_url = request.args.get("next") or url_for("admin.index")
            return redirect(next_url)
        flash("Invalid credentials.", "danger")

    return render_template("admin/login.html", form=form)


@admin_bp.route("/logout")
def logout():
    session.pop("admin_user_id", None)
    session.pop("admin_username", None)
    flash("Signed out of admin.", "info")
    return redirect(url_for("admin.login"))


@admin_bp.route("/")
@admin_login_required
def index():
    """Render admin dashboard with application statistics and activity."""
    total_users = User.query.count()
    total_resumes = Resume.query.count()
    total_ats = Resume.query.filter(Resume.ats_score.isnot(None)).count()
    total_jd = JobDescriptionMatch.query.count()
    total_interview = InterviewQuestionSet.query.count()
    latest_resume = Resume.query.order_by(Resume.upload_time.desc()).first()

    return render_template(
        "admin/index.html",
        total_users=total_users,
        total_resumes=total_resumes,
        total_ats=total_ats,
        total_matches=total_jd,
        total_interview=total_interview,
        latest_resume=latest_resume,
    )


@admin_bp.route("/users")
@admin_login_required
def users():
    """List registered users with search and pagination."""
    q = request.args.get("q", "").strip()
    page = _get_page_number()
    per_page = 20

    query = User.query
    if q:
        query = query.filter(
            (User.full_name.ilike(f"%{q}%")) | (User.email.ilike(f"%{q}%"))
        )

    pagination = query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return render_template("admin/users.html", pagination=pagination, q=q)


@admin_bp.route("/resumes")
@admin_login_required
def resumes():
    """Manage uploaded resumes with filters and actions."""
    q = request.args.get("q", "").strip()
    page = _get_page_number()
    per_page = 20

    query = Resume.query.join(User)
    if q:
        likeq = f"%{q}%"
        query = query.filter((User.full_name.ilike(likeq)) | (User.email.ilike(likeq)) | (Resume.original_filename.ilike(likeq)))

    pagination = query.order_by(Resume.upload_time.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return render_template("admin/resumes.html", pagination=pagination, q=q)


@admin_bp.route("/resume/<int:resume_id>")
@admin_login_required
def view_resume(resume_id: int):
    resume = Resume.query.get_or_404(resume_id)
    latest_match = (
        JobDescriptionMatch.query.filter_by(resume_id=resume.id)
        .order_by(JobDescriptionMatch.created_at.desc())
        .first()
    )
    question_set = (
        InterviewQuestionSet.query.filter_by(resume_id=resume.id)
        .order_by(InterviewQuestionSet.created_at.desc())
        .first()
    )

    return render_template(
        "admin/resume_details.html",
        resume=resume,
        latest_match=latest_match,
        question_set=question_set,
    )


@admin_bp.route("/resume/download/<int:resume_id>")
@admin_login_required
def download_report(resume_id: int):
    resume = Resume.query.get_or_404(resume_id)

    ats_analysis = None
    if resume.extracted_text:
        from app.resume.ats_service import ATSScoringService

        scoring_service = ATSScoringService()
        ats_analysis = scoring_service.analyze(resume.extracted_text)

    latest_match = (
        JobDescriptionMatch.query.filter_by(resume_id=resume.id)
        .order_by(JobDescriptionMatch.created_at.desc())
        .first()
    )
    match_result = None
    if latest_match:
        match_result = {
            "similarity_percent": latest_match.similarity_score,
            "matched_skills": [skill.strip() for skill in latest_match.matched_skills.split(",") if skill.strip()],
            "missing_skills": [skill.strip() for skill in latest_match.missing_skills.split(",") if skill.strip()],
            "suggested_skills": [skill.strip() for skill in latest_match.suggested_skills.split(",") if skill.strip()],
        }

    question_set = (
        InterviewQuestionSet.query.filter_by(resume_id=resume.id)
        .order_by(InterviewQuestionSet.created_at.desc())
        .first()
    )
    interview_questions = None
    if question_set:
        interview_questions = {
            "technical": [line.strip() for line in question_set.technical_questions.splitlines() if line.strip()],
            "project": [line.strip() for line in question_set.project_questions.splitlines() if line.strip()],
            "hr": [line.strip() for line in question_set.hr_questions.splitlines() if line.strip()],
        }

    report_service = ResumeReportService()
    pdf_buffer = report_service.generate_report(
        resume, ats_analysis=ats_analysis, match_result=match_result, interview_questions=interview_questions
    )

    return (
        pdf_buffer.getvalue(),
        200,
        {
            "Content-Type": "application/pdf",
            "Content-Disposition": f"attachment; filename={secure_filename(resume.original_filename.rsplit('.',1)[0] or resume.original_filename)}.pdf",
        },
    )


@admin_bp.route("/resume/delete/<int:resume_id>", methods=["POST"])
@admin_login_required
def delete_resume(resume_id: int):
    resume = Resume.query.get_or_404(resume_id)
    try:
        # Remove stored file if exists
        storage_path = None
        if resume.stored_filename:
            from flask import current_app

            storage_path = current_app.config["UPLOAD_FOLDER"]
            full = os.path.join(storage_path, resume.stored_filename)
            if os.path.exists(full):
                os.remove(full)

        db.session.delete(resume)
        db.session.commit()
        flash("Resume deleted.", "success")
    except Exception:
        db.session.rollback()
        flash("Unable to delete resume.", "danger")

    return redirect(url_for("admin.resumes"))
