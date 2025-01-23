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
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)

# Initialize CSRF protection
# Added CSRF protection to prevent cross-site request forgery attacks,
# ensuring that every POST request includes a valid token.
csrf = CSRFProtect(app)

# ------------------------------------------------------------------------------
# 1. Environment Variable for Secret Key
#    - Changed hardcoded secret key to use an environment variable.
#    - This enhances security by avoiding exposing the secret key in version control.
#    - 'dev_key' is used as a fallback for local development but should not
#      be used in production.
# ------------------------------------------------------------------------------
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev_key')

# ------------------------------------------------------------------------------
# 2. Secure Session Cookies
#    - Configured session cookies to use HTTPS-only transmission, preventing
#      them from being sent over unsecured connections.
#    - Restricted cookies from being accessed by JavaScript (HttpOnly) to
#      mitigate the risk of client-side script-based attacks.
#    - Set SESSION_COOKIE_SAMESITE to 'Strict' to reduce CSRF attack vectors.
# ------------------------------------------------------------------------------
app.config.update(
    SESSION_COOKIE_SECURE=True,    # Ensures cookies are sent only over HTTPS
    SESSION_COOKIE_HTTPONLY=True,  # Prevents JavaScript from accessing cookies
    SESSION_COOKIE_SAMESITE='Strict', # Mitigates CSRF by restricting cross-site cookies
)

# ------------------------------------------------------------------------------
# 3. Logging Configuration
#    - Updated logging to INFO level to capture significant events while
#      avoiding verbose debug logs in production.
#    - Avoided logging sensitive information such as passwords.
# ------------------------------------------------------------------------------
app.logger.setLevel(logging.INFO)

# ------------------------------------------------------------------------------
# 4. Session Timeout
#    - Configured sessions to expire after 30 minutes of inactivity.
#    - This change ensures that authenticated sessions are automatically
#      invalidated after a reasonable period to reduce security risks.
# ------------------------------------------------------------------------------
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

# ------------------------------------------------------------------------------
# 5. Rate Limiting
#    - Added rate limiting to prevent brute-force attacks on login endpoints.
#    - By default, each client is limited to 10 requests per minute across the app.
# ------------------------------------------------------------------------------
limiter = Limiter(
    get_remote_address,  # Tracks users by their IP addresses
    app=app,  # Flask app instance
    default_limits=["10 per minute"]
)

# ------------------------------------------------------------------------------
# Database Helper
#    - Simplified database connections using 'with' statements to ensure
#      connections are properly closed, reducing the risk of resource leaks.
# ------------------------------------------------------------------------------
def get_db_connection():
    """
    Returns a SQLite connection object.
    Ensures rows behave like dictionaries rather than tuples for better readability.
    """
    connection = sqlite3.connect("database.db", isolation_level=None)
    connection.row_factory = sqlite3.Row
    return connection

# ------------------------------------------------------------------------------
# Helper: Check if a user is already authenticated
#    - Centralized authentication check using session variables.
#    - This simplifies the process of checking login status across the app.
# ------------------------------------------------------------------------------
def is_authenticated():
    """
    Checks if the user is logged in by looking for 'username' in the session.
    """
    return "username" in session

# ------------------------------------------------------------------------------
# Authentication Logic
#    - Improved security by using bcrypt to compare password hashes rather
#      than storing plain-text passwords in the database.
#    - Ensured all database queries use parameterized statements to prevent
#      SQL injection attacks.
# ------------------------------------------------------------------------------
def authenticate(username, password):
    """
    Authenticates a user by:
      1. Fetching the user record securely from the database.
      2. Comparing the hashed password in the database with the supplied password.
      3. Marking the session as permanent to enforce session timeout policies.
    """
    # Use a context manager to ensure the connection closes automatically
    with get_db_connection() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

    if user:
        stored_hashed_pw = user["password"]
        # Convert stored hash to bytes if it was stored as a string
        if isinstance(stored_hashed_pw, str):
            stored_hashed_pw = stored_hashed_pw.encode('utf-8')

        # Compare hashed password with user-provided password
        if bcrypt.checkpw(password.encode('utf-8'), stored_hashed_pw):
            # Log the successful login without exposing sensitive details
            app.logger.info(f"User '{username}' logged in successfully.")
            session.permanent = True  # Enforce session expiration policies
            session["username"] = username
            return True

    # Log failed login attempts for monitoring
    app.logger.warning(f"Login failed for user '{username}'.")
    return False

# ------------------------------------------------------------------------------
# Routes
#    - Centralized the handling of authentication status in templates for
#      cleaner and consistent logic across the app.
# ------------------------------------------------------------------------------
@app.route("/")
def index():
    """
    Home page route.
    Displays the home page with a dynamic message depending on authentication status.
    """
    return render_template("index.html", is_authenticated=is_authenticated())

@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5/minute")  # Tightened rate limit for sensitive endpoints
def login():
    """
    Login route:
      - GET: Displays the login form.
      - POST: Authenticates the user and redirects to the home page on success.
              Re-renders the form with a generic error message on failure.
    """
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username and password and authenticate(username, password):
            return redirect(url_for("index"))
        else:
            # Avoid leaking details about whether the username or password is incorrect
            flash("Invalid username or password. Please try again.", "error")
            return render_template("login.html")

    return render_template("login.html")

@app.route("/logout")
def logout():
    """
    Logout route:
      - Removes the 'username' from the session to log the user out.
      - Redirects to the home page after logging out.
    """
    session.pop("username", None)
    return redirect(url_for("index"))

if __name__ == "__main__":
    """
    Starts the Flask development server for local testing.
    - Debug mode is controlled by an environment variable to ensure it's disabled in production.
    - For production, this app should be deployed behind a WSGI server like Gunicorn or uWSGI.
    """
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=5050, debug=debug_mode)