from flask import render_template
from flask_login import current_user, login_required

from app.dashboard import dashboard_bp
from app.models import Resume


@dashboard_bp.route("/")
@login_required
def index():
    """Render the authenticated dashboard for the current user."""
    user_resumes = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.upload_time.desc()).all()
    latest_resume = user_resumes[0] if user_resumes else None

    return render_template(
        "dashboard/index.html",
        user=current_user,
        total_resumes=len(user_resumes),
        latest_resume=latest_resume,
    )
