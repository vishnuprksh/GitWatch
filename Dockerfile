FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py config.py db.py git_utils.py ./

# Create data directory
RUN mkdir -p /data/gitwatch/repos

# Expose Dash default port
EXPOSE 8050

# Set environment variables
ENV GITWATCH_DATA_DIR=/data/gitwatch
ENV GITWATCH_REPOS_PATH=/data/gitwatch/repos
ENV FLASK_ENV=production

# Run the application
CMD ["python", "app.py"]
