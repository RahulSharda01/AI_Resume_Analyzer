from datetime import datetime

from flask import flash, redirect, render_template, url_for
from flask_login import login_required, login_user, logout_user
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from app.auth import auth_bp
from app.auth.forms import LoginForm, RegistrationForm
from app.models import User


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, form.password.data):
            try:
                user.last_login_at = datetime.utcnow()
                user.updated_at = datetime.utcnow()
                db.session.commit()
            except Exception:
                db.session.rollback()
                flash("Unable to complete login at the moment. Please try again.", "danger")
                return render_template("auth/login.html", form=form)

            login_user(user, remember=form.remember_me.data)
            flash("Welcome back! You have been logged in successfully.", "success")
            return redirect(url_for("dashboard.index"))

        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        username = form.username.data.strip()

        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "warning")
            return render_template("auth/register.html", form=form)

        if User.query.filter_by(username=username).first():
            flash("That username is already taken. Please choose another one.", "warning")
            return render_template("auth/register.html", form=form)

        user = User(
            full_name=form.full_name.data.strip(),
            username=username,
            email=email,
            phone=form.phone.data.strip(),
            password_hash=generate_password_hash(form.password.data),
        )

        try:
            db.session.add(user)
            db.session.commit()
            flash("Registration successful. Please log in to continue.", "success")
            return redirect(url_for("auth.login"))
        except IntegrityError:
            db.session.rollback()
            flash("The account could not be created because the details already exist.", "danger")
        except Exception:
            db.session.rollback()
            flash("An unexpected error occurred while creating your account.", "danger")

    return render_template("auth/register.html", form=form)
