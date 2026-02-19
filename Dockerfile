FROM python:3.12-slim

WORKDIR /app
COPY . /app

# Copy all code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set environment variables for Flask
ENV FLASK_APP=main
ENV FLASK_ENV=development

# Default command for Flask API
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
