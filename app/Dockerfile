# Start from a lightweight Python base image
FROM python:3.10-slim

# Set environment variables
ENV FLASK_SECRET_KEY="192b9bdd22ab9ed4d12e236c78afcb9a393ec15f71bbf5dc987d54727823bcbf" \
    FLASK_DEBUG="false" \
    PYTHONUNBUFFERED=1

# Create a non-root user (optional but recommended)
RUN useradd -m -u 1000 flaskuser

# Set the working directory
WORKDIR /app

# Copy requirement specs first for efficient layer caching
COPY requirements.txt .

# Install necessary Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Switch to non-root user
USER flaskuser

# Expose port 5050 (the port your app runs on)
EXPOSE 5050

# Use Gunicorn to run the Flask app in production
#   - "app:app" means "import 'app' and run the 'app' object"
#   - "-b 0.0.0.0:5050" binds to all interfaces on port 5050
#   - The access-logfile and error-logfile arguments make logs visible in Docker logs
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:5050", "--access-logfile", "-", "--error-logfile", "-"]