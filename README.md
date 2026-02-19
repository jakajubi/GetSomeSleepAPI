# 1. Open The Project in VS Code
# ------------------------------
# Open VS Code.
# Open the project folder (the folder containing: Dockerfile, docker-compose.yml, requirements.txt, and app/).
# Make sure Python extension is installed in VS Code.
# Optional: Install Docker extension for easier container management.

# 2. Configure VS Code environment
# --------------------------------
# Since we’re using Docker, you don’t need to install Python packages on your host, 
# but VS Code can still use a virtual environment for IntelliSense:
# Create a Python virtual environment (optional for editor features):

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# In VS Code:
Press Ctrl+Shift+P ==> Python: Select Interpreter → choose .venv/bin/python

# This ensures linting, autocomplete, and Pylance work correctly.
# First time:
pip3 install flask celery redis psutil requests flasgger

# 3. Launch Docker containers
# ---------------------------
# From the VS Code terminal (or any terminal in the project folder):

# To stop everything
sudo usermod -aG docker $USER
newgrp docker
docker ps

# Clean start (optional first time) - do not use --volumes if you want to save the PostGIS database
docker-compose down --rmi all --volumes --remove-orphans
docker-compose down --rmi all --remove-orphans

# removes all unused containers, networks, images, and build cache (By default it does not remove volumes)
docker system prune -af

# Build images
docker-compose build --no-cache

# Start containers
docker-compose up

# flask_api --> runs on http://localhost:5000
# celery_worker --> handles async tasks
# redis --> task broker / backend
# You’ll see logs for Flask and Celery in the terminal. Keep this terminal open to watch the tasks.

# 4. Test the Flask API
# ---------------------
# Endpoint 1: GetAPIStatus
curl http://localhost:5000/GetAPIStatus

# Example response:
# {
#   "tasks_in_queue": 0,
#   "total_tasks_executed": 3,
#   "ram_used_mb": 120,
#   "storage_used_mb": 50
# }

# Endpoint 2: GetSomeSleep
curl -X POST http://localhost:5000/GetSomeSleep \
     -H "Content-Type: application/json" \
     -d '{"inNumberOfSleepSeconds":5}'

# Example response:
# {
#   "sleep_seconds": 5,
#  "quality": 7
# }

# This runs a Celery task asynchronously and returns the “quality of sleep” as a random number between 1 and 10.

# 5. Run the test Python program
# ------------------------------
# If you have a test program (e.g., launch_tasks.py) that submits multiple sleep tasks and saves results:
python test_client/launch_tasks.py

# It will push N GetSomeSleep jobs to Celery.
# Fetch results from Redis.
# Save all results into a text file (e.g., sleep_results.txt).

# 6. Optional: View logs in VS Code
---------------------------------
# Open Docker extension ==> see containers ==> view logs.
# Or use CLI:
docker-compose logs -f flask_api
docker-compose logs -f celery_worker

# 7. Stop the app cleanly
# -----------------------
docker-compose down
# Stops all containers but keeps images unless you add --rmi all.

# 8. Swagger documentation
# ------------------------
http://localhost:5000/apidocs

# 9. Connect to the PostGIS database
# ----------------------------------
docker exec -it postgis_data_dev psql -U sleepuser -d sleepdb
# display all entries
SELECT * FROM sleep_results;
