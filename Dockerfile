FROM python:3.12-slim

# Install PostgreSQL client for wait script
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ /app/

# Copy wait script to a separate location (not in /app)
# This is the path in your docker container
# This is a great example of Docker's "build once, run anywhere" principle: everything your 
# application needs (code, dependencies, scripts) is packaged into the image, making 
# deployment truly portable.
COPY wait-for-postgis.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/wait-for-postgis.sh

# Set environment variables for Flask
ENV FLASK_APP=main
ENV FLASK_ENV=development

# Use the script from /usr/local/bin
CMD ["wait-for-postgis.sh", "postgis", "flask", "run", "--host=0.0.0.0", "--port=5000"]
