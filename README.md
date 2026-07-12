# AI Resume Analyzer & Interview Assistant

A modular Flask application for uploading resumes, extracting resume text, scoring ATS readiness, comparing against job descriptions, and generating interview questions.

## Features
- Secure authentication and user management
- Resume upload for PDF and DOCX files
- Resume text extraction and ATS scoring heuristics
- Job description matching with skill gap suggestions
- Interview question generation tailored to the resume and match context
- Simple admin dashboard with usage statistics

## Project Structure
- app/: Flask application package with blueprints, templates, static assets, models, and services
- tests/: Regression tests for core services
- uploads/: Local storage for uploaded resume files

## Installation
1. Create and activate a virtual environment.
2. Install dependencies: `pip install -r requirements.txt`
3. Set environment variables such as `FLASK_ENV=development`, `SECRET_KEY=<strong-random-value>`, and optionally `DATABASE_URL` or `USE_MYSQL`.
4. Run the app: `python run.py`

For production deployments, make sure `SECRET_KEY` is set and the upload directory is writable.

## Creating the first Admin

To create the initial administrator account (stored separately from normal users), run the included script:

```bash
python create_admin.py
```

The script will prompt for admin name, email and password and will store the admin in the `admin_users` table. It will not create a duplicate admin for the same email.

## Architecture Notes
The application uses a Flask factory pattern with modular blueprints for authentication, dashboard, resume management, and admin views. Business logic is separated into service modules to keep routes focused on user flow.

## Screenshots
Screenshots will be added in a future release.
