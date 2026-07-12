from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import SubmitField, TextAreaField
from wtforms.validators import DataRequired


class ResumeUploadForm(FlaskForm):
    """Form for uploading a resume file."""

    resume_file = FileField(
        "Resume File",
        validators=[
            FileRequired(message="Please select a file to upload."),
            FileAllowed(["pdf", "docx"], "Only PDF and DOCX files are supported."),
        ],
    )
    submit = SubmitField("Upload Resume")


class InterviewQuestionForm(FlaskForm):
    """Form for regenerating interview questions with CSRF protection."""

    submit = SubmitField("Regenerate")


class JobDescriptionForm(FlaskForm):
    """Form for comparing a job description against a resume."""

    job_description = TextAreaField(
        "Job Description",
        validators=[DataRequired(message="Please paste a job description before submitting.")],
    )
    submit = SubmitField("Compare")
