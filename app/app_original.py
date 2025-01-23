import sqlite3
import logging
from flask import Flask, session, redirect, url_for, request, render_template, abort

app = Flask(__name__)
app.secret_key = b"192b9bdd22ab9ed4d12e236c78afcb9a393ec15f71bbf5dc987d54727823bcbf"
# ^ Storing a secret key directly in the source code is dangerous (it should be set via environment variable or config).
#   Also, keys should not be publicly exposed in a repository.

app.logger.setLevel(logging.INFO)


def get_db_connection():
    connection = sqlite3.connect("database.db")
    # ^ The database filename is hard-coded, which can be problematic if you want different environments (dev, test, prod).
    connection.row_factory = sqlite3.Row
    return connection


def is_authenticated():
    if "username" in session:
        return True
    return False


def authenticate(username, password):
    connection = get_db_connection()
    # ^ There's no error handling around the database connection or query execution.
    users = connection.execute("SELECT * FROM users").fetchall()
    # ^ Selecting ALL user rows instead of filtering by username in the query can be inefficient and potentially insecure.
    # ^ Also, this code does not use parameterized queries. Though it’s not directly using untrusted input here,
    #   in general you should use parameterized queries to prevent SQL injection.
    connection.close()

    for user in users:
        if user["username"] == username and user["password"] == password:
            # ^ Passwords are stored in plaintext in the database, which is highly insecure.
            #   They should be hashed (e.g., using bcrypt or similar).
            app.logger.info(f"the user '{username}' logged in successfully with password '{password}'")
            # ^ Logging sensitive information (the password) is a security risk. Avoid logging passwords.
            session["username"] = username
            return True

    app.logger.warning(f"the user '{ username }' failed to log in '{ password }'")
    # ^ Logging the password on failed login attempts is also a security risk.
    abort(401)
    # ^ abort(401) triggers a 401 Unauthorized response, but it might not provide a user-friendly message.
    #   Also, returning a 401 might cause the browser to prompt for HTTP Basic Auth, which you may not want.
    #   Typically, you might return 403 or redirect back to a login page with an error message.


@app.route("/")
def index():
    return render_template("index.html", is_authenticated=is_authenticated())
    # ^ The template may need protection against CSRF or other checks if it has forms.


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if authenticate(username, password):
            # ^ The authenticate function aborts on failure, so there's no separate failure handling or feedback
            #   to the user (like “incorrect username or password”).
            return redirect(url_for("index"))
    # ^ There's no CSRF protection on this login form.
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("username", None)
    # ^ This simply removes the username but no other session security measures are taken.
    #   Consider regenerating the session if security is critical.
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
    # ^ Running the Flask app in production this way (with debug server) is not recommended.
    #   Use a production server (e.g., gunicorn or uwsgi) and consider HTTPS.