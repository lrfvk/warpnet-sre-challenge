"""
Example Flask application with improvements:
  - Single import of bcrypt
  - Environment variable–based secret key (no debug in production!)
  - Secure session cookie configuration
  - Using 'with' statements for database access
  - Optional session timeout
  - Re-rendering the login form with a generic error message (no 401 abort)
"""

import os
import sqlite3
import logging
from datetime import timedelta

from flask import (
    Flask, session, redirect, url_for, request, render_template, flash
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import bcrypt


app = Flask(__name__)

# ------------------------------------------------------------------------------
# 1. Environment Variable for Secret Key
#    - Avoid storing secret keys directly in version control.
#    - 'dev_key' is just a fallback for local testing; never use it in production!
# ------------------------------------------------------------------------------
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev_key')

# ------------------------------------------------------------------------------
# 2. Secure Session Cookies
#    - These settings help protect your session cookies from interception
#      and prevent JavaScript from reading them.
#    - Consider 'Strict' for SESSION_COOKIE_SAMESITE if you do not need any cross-site usage.
# ------------------------------------------------------------------------------
app.config.update(
    SESSION_COOKIE_SECURE=True,    # Only transmit cookies over HTTPS
    SESSION_COOKIE_HTTPONLY=True,  # Disallow JavaScript access to the cookies
    SESSION_COOKIE_SAMESITE='Strict', # Mitigate CSRF attacks; 'Lax' can also be used
)

# ------------------------------------------------------------------------------
# 3. Logging Configuration
#    - We log events without exposing passwords or other secrets.
# ------------------------------------------------------------------------------
app.logger.setLevel(logging.INFO)

# ------------------------------------------------------------------------------
# 4. (Optional) Session Timeout
#    - This config will make sessions expire after a period.
#    - If you want an idle timeout, you need custom logic tracking last activity.
# ------------------------------------------------------------------------------
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

# ------------------------------------------------------------------------------
# 5. Rate Limiting
#    - Helps prevent brute-force password attacks by limiting login attempts.
# ------------------------------------------------------------------------------
limiter = Limiter(
    get_remote_address,
    app=app,  # Must be passed as named argument
    default_limits=["10 per minute"]
)

# ------------------------------------------------------------------------------
# Database Helper
# ------------------------------------------------------------------------------
def get_db_connection():
    """
    Returns a SQLite connection object.
    Ensures rows behave like dictionaries rather than tuples.
    """
    connection = sqlite3.connect("database.db", isolation_level=None)
    connection.row_factory = sqlite3.Row
    return connection

# ------------------------------------------------------------------------------
# Helper: Check if a user is already authenticated
# ------------------------------------------------------------------------------
def is_authenticated():
    """
    Checks if the user is logged in by looking for 'username' in the session.
    """
    return "username" in session

# ------------------------------------------------------------------------------
# Authentication Logic
# ------------------------------------------------------------------------------
def authenticate(username, password):
    """
    Authenticates a user by:
      1. Retrieving the user record from the database via parameterized query
      2. Comparing the hashed password in the DB with the hash of the provided password
      3. Logging the user in if valid, or returning False if invalid
    """
    # Use a context manager to ensure the connection closes automatically
    with get_db_connection() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

    if user:
        stored_hashed_pw = user["password"]
        # If the stored hash is a string in the DB, convert to bytes
        if isinstance(stored_hashed_pw, str):
            stored_hashed_pw = stored_hashed_pw.encode('utf-8')

        # Compare the stored hashed password with the user-supplied password
        if bcrypt.checkpw(password.encode('utf-8'), stored_hashed_pw):
            # Only log the username; never log raw passwords
            app.logger.info(f"User '{username}' logged in successfully.")
            # Mark session as permanent to enforce PERMANENT_SESSION_LIFETIME
            session.permanent = True
            session["username"] = username
            return True

    # If we get here, authentication failed
    app.logger.warning(f"Login failed for user '{username}'.")
    return False

# ------------------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------------------
@app.route("/")
def index():
    """
    Home page route.
    Renders index.html and passes along the authentication status.
    """
    return render_template("index.html", is_authenticated=is_authenticated())

@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5/minute")  # Additional rate limit for the login route
def login():
    """
    Login route:
      - If method is GET, render a login form.
      - If method is POST, attempt to authenticate the user.
      - On successful authentication, redirect to the home page.
      - On failure, re-render the login form with an error message.
    """
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username and password and authenticate(username, password):
            return redirect(url_for("index"))
        else:
            # Provide user-friendly error message without revealing details
            flash("Invalid username or password. Please try again.", "error")
            return render_template("login.html")

    return render_template("login.html")

@app.route("/logout")
def logout():
    """
    Logout route:
      - Pop 'username' from the session, if present.
      - Redirect to the home page afterwards.
    """
    session.pop("username", None)
    return redirect(url_for("index"))


if __name__ == "__main__":
    """
    Runs the Flask development server for local testing.
    For production, use a proper WSGI server (e.g., Gunicorn or uWSGI),
    and do NOT enable debug mode in production!
    """
    # Use an environment variable or config to control debug mode:
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=5050, debug=debug_mode)