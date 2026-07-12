#!/usr/bin/env python3
"""Create the initial admin user for the AI Resume Analyzer.

Usage: python create_admin.py

The script requests admin name, email and password interactively, hashes
the password and stores it in the `admin_users` table. It will not create
duplicate admins for the same email.
"""
import getpass
import sys

from app import create_app, db
from app.models import AdminUser


def main():
    app = create_app()
    with app.app_context():
        print("Create first admin user for AI Resume Analyzer")
        full_name = input("Admin name: ").strip()
        email = input("Admin email: ").strip().lower()
        if not email:
            print("Email is required. Exiting.")
            sys.exit(1)

        existing = AdminUser.query.filter_by(email=email).first()
        if existing:
            print(f"An admin with email {email} already exists. Exiting.")
            sys.exit(1)

        while True:
            password = getpass.getpass("Password: ")
            password2 = getpass.getpass("Confirm Password: ")
            if password != password2:
                print("Passwords do not match. Try again.")
                continue
            if len(password) < 8:
                print("Choose a stronger password (at least 8 characters).")
                continue
            break

        username = email.split("@")[0]
        admin = AdminUser(username=username, email=email, full_name=full_name)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()

        print(f"Admin user {email} created successfully.")


if __name__ == "__main__":
    main()
