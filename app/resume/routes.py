import os
import uuid
from datetime import datetime

from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from app import db
from app.models import InterviewQuestionSet, JobDescriptionMatch, Resume
from app.resume import resume_bp
from app.resume.ats_service import ATSScoringService
from app.resume.forms import InterviewQuestionForm, JobDescriptionForm, ResumeUploadForm
from app.resume.interview_service import InterviewQuestionService
from app.resume.jd_service import JobDescriptionService
from app.resume.report_service import ResumeReportService
from app.resume.services import extract_resume_text, validate_resume_upload


@resume_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Render the resume upload page and process uploads."""
    form = ResumeUploadForm()

    if request.method == "POST":
        if form.validate_on_submit():
            file_storage = form.resume_file.data
            if not file_storage:
                flash("Please select a file to upload.", "warning")
                return render_template("resume/index.html", form=form)

            try:
                filename, file_size = validate_resume_upload(
                    file_storage,
                    max_content_length=current_app.config["MAX_CONTENT_LENGTH"],
                )
            except ValueError as exc:
                flash(str(exc), "warning")
                return render_template("resume/index.html", form=form)

            # Preserve the original filename, but keep the stored file name unique.
            extension = os.path.splitext(filename)[1]
            unique_name = f"{uuid.uuid4().hex}{extension}"
            storage_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_name)

            try:
                file_storage.save(storage_path)
                extracted_text = extract_resume_text(storage_path, filename)
                resume = Resume(
                    user_id=current_user.id,
                    original_filename=filename,
                    stored_filename=unique_name,
                    file_size=file_size,
                    upload_time=datetime.utcnow(),
                    extracted_text=extracted_text,
                    ats_score=None,
                )
                db.session.add(resume)
                db.session.commit()
                flash("Resume uploaded and text extracted successfully.", "success")
                return redirect(url_for("resume.details", resume_id=resume.id))
            except ValueError as exc:
                db.session.rollback()
                if os.path.exists(storage_path):
                    os.remove(storage_path)
                flash(str(exc), "warning")
            except Exception as exc:
                current_app.logger.exception("Resume upload failed for %s", filename)
                db.session.rollback()
                if os.path.exists(storage_path):
                    os.remove(storage_path)
                flash(f"Extraction failed: {exc}", "danger")
        else:
            for field_errors in form.errors.values():
                for error in field_errors:
                    flash(error, "danger")

    user_resumes = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.upload_time.desc()).all()
    latest_resume = user_resumes[0] if user_resumes else None

    return render_template(
        "resume/index.html",
        form=form,
        total_resumes=len(user_resumes),
        latest_resume=latest_resume,
        user_resumes=user_resumes,
    )


@resume_bp.route("/details/<int:resume_id>")
@login_required
def details(resume_id: int):
    """Display the uploaded resume and its extracted text."""
    resume = Resume.query.filter_by(id=resume_id, user_id=current_user.id).first_or_404()
    return render_template("resume/details.html", resume=resume)


@resume_bp.route("/report/<int:resume_id>")
@login_required
def download_report(resume_id: int):
    """Generate and return a PDF report for the resume analysis summary."""
    resume = Resume.query.filter_by(id=resume_id, user_id=current_user.id).first_or_404()

    ats_analysis = None
    if resume.extracted_text:
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

    latest_question_set = (
        InterviewQuestionSet.query.filter_by(resume_id=resume.id)
        .order_by(InterviewQuestionSet.created_at.desc())
        .first()
    )
    interview_questions = None
    if latest_question_set:
        interview_questions = {
            "technical": [line.strip() for line in latest_question_set.technical_questions.splitlines() if line.strip()],
            "project": [line.strip() for line in latest_question_set.project_questions.splitlines() if line.strip()],
            "hr": [line.strip() for line in latest_question_set.hr_questions.splitlines() if line.strip()],
        }

    report_service = ResumeReportService()
    pdf_buffer = report_service.generate_report(
        resume,
        ats_analysis=ats_analysis,
        match_result=match_result,
        interview_questions=interview_questions,
    )

    return (
        pdf_buffer.getvalue(),
        200,
        {
            "Content-Type": "application/pdf",
            "Content-Disposition": f"attachment; filename={resume.original_filename.rsplit('.', 1)[0] or resume.original_filename}.pdf",
        },
    )


@resume_bp.route("/ats/<int:resume_id>")
@login_required
def ats_result(resume_id: int):
    """Generate and display ATS scoring insights for a resume."""
    resume = Resume.query.filter_by(id=resume_id, user_id=current_user.id).first_or_404()

    if not resume.extracted_text:
        flash("No extracted text is available yet for ATS analysis.", "warning")
        return redirect(url_for("resume.details", resume_id=resume.id))

    scoring_service = ATSScoringService()
    analysis = scoring_service.analyze(resume.extracted_text)

    try:
        resume.ats_score = analysis["overall_score"]
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("Unable to save the ATS score at the moment.", "danger")
        return redirect(url_for("resume.details", resume_id=resume.id))

    return render_template(
        "resume/ats_result.html",
        resume=resume,
        analysis=analysis,
    )


@resume_bp.route("/job-description/<int:resume_id>", methods=["GET", "POST"])
@login_required
def job_description(resume_id: int):
    """Allow users to compare a resume against a pasted job description."""
    form = JobDescriptionForm()
    resume = Resume.query.filter_by(id=resume_id, user_id=current_user.id).first_or_404()

    if not resume.extracted_text:
        flash("No extracted text is available yet for matching.", "warning")
        return redirect(url_for("resume.details", resume_id=resume.id))

    match_result = None
    history = []

    if form.validate_on_submit():
        job_description_text = form.job_description.data.strip()
        service = JobDescriptionService()
        try:
            match_result = service.compare(resume.extracted_text, job_description_text)
            history_entry = JobDescriptionMatch(
                resume_id=resume.id,
                job_description=job_description_text,
                similarity_score=match_result["similarity_percent"],
                matched_skills=", ".join(match_result["matched_skills"]),
                missing_skills=", ".join(match_result["missing_skills"]),
                suggested_skills=", ".join(match_result["suggested_skills"]),
            )
            db.session.add(history_entry)
            db.session.commit()
            flash("Job description match calculated successfully.", "success")
        except Exception:
            db.session.rollback()
            flash("Unable to perform the comparison at the moment.", "danger")
    elif request.method == "POST":
        flash("Please paste a job description before submitting.", "warning")

    history = (
        JobDescriptionMatch.query.filter_by(resume_id=resume.id)
        .order_by(JobDescriptionMatch.created_at.desc())
        .all()
    )

    return render_template(
        "resume/job_description.html",
        resume=resume,
        form=form,
        match_result=match_result,
        history=history,
    )


@resume_bp.route("/interview-questions/<int:resume_id>", methods=["GET", "POST"])
@login_required
def interview_questions(resume_id: int):
    """Generate and display interview questions for a resume."""
    form = InterviewQuestionForm()
    resume = Resume.query.filter_by(id=resume_id, user_id=current_user.id).first_or_404()

    if not resume.extracted_text:
        flash("No extracted text is available yet for interview generation.", "warning")
        return redirect(url_for("resume.details", resume_id=resume.id))

    latest_match = (
        JobDescriptionMatch.query.filter_by(resume_id=resume.id)
        .order_by(JobDescriptionMatch.created_at.desc())
        .first()
    )
    ats_analysis = None

    if form.validate_on_submit():
        service = InterviewQuestionService()
        ats_service = ATSScoringService()
        ats_analysis = ats_service.analyze(resume.extracted_text)
        generated = service.generate_questions(resume.extracted_text, ats_analysis, latest_match)

        try:
            question_set = InterviewQuestionSet(
                resume_id=resume.id,
                technical_questions="\n".join(generated["technical"]),
                project_questions="\n".join(generated["project"]),
                hr_questions="\n".join(generated["hr"]),
            )
            db.session.add(question_set)
            db.session.commit()
            flash("Interview questions generated successfully.", "success")
        except Exception:
            db.session.rollback()
            flash("Unable to save the generated interview questions at the moment.", "danger")

    question_set = (
        InterviewQuestionSet.query.filter_by(resume_id=resume.id)
        .order_by(InterviewQuestionSet.created_at.desc())
        .first()
    )

    if not question_set and ats_analysis is None:
        ats_service = ATSScoringService()
        ats_analysis = ats_service.analyze(resume.extracted_text)

    if question_set:
        generated = {
            "technical": question_set.technical_questions.splitlines(),
            "project": question_set.project_questions.splitlines(),
            "hr": question_set.hr_questions.splitlines(),
        }
    else:
        service = InterviewQuestionService()
        generated = service.generate_questions(resume.extracted_text, ats_analysis or {}, latest_match)

    return render_template(
        "resume/interview_questions.html",
        resume=resume,
        generated=generated,
        question_set=question_set,
        form=form,
    )
