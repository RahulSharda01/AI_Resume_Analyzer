import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

from config import config

# Initialize extensions
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"

csrf = CSRFProtect()
db = SQLAlchemy()


def create_app(config_name: str | None = None) -> Flask:
    """Application factory for creating Flask app instances."""
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config[config_name])
    app.config.setdefault("SESSION_COOKIE_HTTPONLY", True)
    app.config.setdefault("SESSION_COOKIE_SAMESITE", "Lax")
    app.config.setdefault("SESSION_COOKIE_SECURE", not (app.debug or app.testing))

    if not app.config.get("SECRET_KEY") or app.config.get("SECRET_KEY") == "change-me-in-production":
        app.logger.warning("Using the default SECRET_KEY; set SECRET_KEY for production deployments.")

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Configure logging
    if not os.path.exists(app.config["UPLOAD_FOLDER"]):
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    if not app.debug and not app.testing:
        if not os.path.exists("logs"):
            os.makedirs("logs")
        file_handler = RotatingFileHandler(
            "logs/app.log",
            maxBytes=1024 * 1024 * 10,
            backupCount=10,
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
            )
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info("Application startup")

    # Register blueprints
    from app.auth.routes import auth_bp
    from app.dashboard.routes import dashboard_bp
    from app.resume.routes import resume_bp
    from app.admin.routes import admin_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(resume_bp, url_prefix="/resume")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    with app.app_context():
        try:
            db.create_all()
            app.logger.info("Database tables created successfully.")
        except Exception as exc:  # pragma: no cover - defensive startup behavior
            app.logger.warning("Database initialization skipped: %s", exc)

    # Register shell context for Flask CLI
    @app.shell_context_processor
    def shell_context():
        return {"db": db}

    # Root redirect
    @app.route("/")
    def root():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard.index"))
        return redirect(url_for("auth.login"))

    # Template helpers for admin session state
    @app.context_processor
    def inject_admin_state():
        from flask import session

        return {
            "admin_logged_in": bool(session.get("admin_user_id")),
            "admin_username": session.get("admin_username"),
        }

    # Expose CSRF token generator to templates as `csrf_token()`
    try:
        from flask_wtf.csrf import generate_csrf

        @app.context_processor
        def expose_csrf_token():
            return {"csrf_token": generate_csrf}
    except Exception:
        # If Flask-WTF not available, skip exposing
        pass

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.warning("404 error for %s", request.path)
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.exception("Unhandled server error for %s", request.path)
        return render_template("errors/500.html"), 500

    # User loader for Flask-Login
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app
