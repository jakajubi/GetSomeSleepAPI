from flask import Flask, jsonify, request
from tasks import celery_app, get_some_sleep
from utils import get_ram_usage_mb, get_storage_usage_mb
from flasgger import Swagger
from tasks import get_some_sleep
import redis
from celery.result import AsyncResult

app = Flask(__name__)
#celery_app = Celery('main', broker='redis://redis:6379/0', backend='redis://redis:6379/1')

# Optional configuration (must be set BEFORE Swagger(app))
app.config['SWAGGER'] = {
    'title': 'GetSomeSleep API',
    'uiversion': 3
}

# Initialize Swagger
swagger = Swagger(app)

# --------------------------------------------------
# --- API endpoint GetAPIStatus() - a GET method ---
# --------------------------------------------------
@app.route("/GetAPIStatus", methods=["GET"])
def get_api_status():
    """
    Get API status
    ---
    tags:
      - Status
    responses:
      200:
        description: API statistics including queue, workers, and finished tasks
    """
    # --- Inspect running tasks ---
    inspector = celery_app.control.inspect()
    active = inspector.active() or {}
    scheduled = inspector.scheduled() or {}
    reserved = inspector.reserved() or {}

    num_active_tasks = sum(len(active.get(worker, [])) for worker in active)
    num_scheduled_tasks = sum(len(scheduled.get(worker, [])) for worker in scheduled)
    num_reserved_tasks = sum(len(reserved.get(worker, [])) for worker in reserved)

    # --- Count tasks in Redis queue (db=0) ---
    r_queue = redis.Redis(host="redis", port=6379, db=0)
    num_tasks_in_queue = r_queue.llen("celery")

    # --- Count finished tasks in result backend (db=1) ---
    r_backend = redis.Redis(host="redis", port=6379, db=1)
    finished_keys = r_backend.keys("celery-task-meta-*")
    num_tasks_finished = len(finished_keys)

    # --- Resource usage ---
    ram_used_mb = get_ram_usage_mb()
    storage_used_mb = get_storage_usage_mb()

    return jsonify({
        "tasks": {
            "in_queue": num_tasks_in_queue,
            "active": num_active_tasks,
            "scheduled": num_scheduled_tasks,
            "reserved": num_reserved_tasks,
            "finished": num_tasks_finished
        },
        "resources": {
            "ram_used_mb": ram_used_mb,
            "storage_used_mb": storage_used_mb
        }
    })

# ---------------------------------------------------
# --- API endpoint GetSomeSleep() - a POST method ---
# ---------------------------------------------------
@app.route("/GetSomeSleep", methods=["POST"])
def get_some_sleep_endpoint():
    """
    Trigger a sleep task
    ---
    tags:
      - Sleep
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            inNumberOfSleepSeconds:
              type: integer
              example: 5
    responses:
      200:
        description: Task result
        schema:
          type: object
          properties:
            sleep_seconds:
              type: integer
            quality:
              type: integer
    """
    data = request.get_json(force=True)  # ensures JSON is parsed
    if "sleep_seconds" not in data:
        return jsonify({"error": "sleep_seconds is required"}), 400
    sleep_seconds = int(data["sleep_seconds"])
    task = get_some_sleep.delay(sleep_seconds)
    return jsonify({"task_id": task.id})

# ---------------------------------------------------
# --- API endpoint GetTaskResult() - a GET method ---
# ---------------------------------------------------
@app.route("/GetTaskResult/<task_id>", methods=["GET"])
def get_task_result(task_id):
    """
    Get task result by task ID
    ---
    tags:
      - Tasks
    parameters:
      - name: task_id
        in: path
        required: true
        schema:
          type: string
        description: The Celery task ID returned when the task was created
    responses:
      200:
        description: Task completed successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                state:
                  type: string
                  example: SUCCESS
                result:
                  type: object
                  properties:
                    sleep_seconds:
                      type: integer
                      example: 3
                    quality:
                      type: integer
                      example: 8
      202:
        description: Task not finished yet
        content:
          application/json:
            schema:
              type: object
              properties:
                state:
                  type: string
                  example: PENDING
    """
    from celery.result import AsyncResult
    from tasks import celery_app

    result = AsyncResult(task_id, app=celery_app)

    if result.state == "PENDING":
        return jsonify({"state": result.state}), 202

    if result.state == "SUCCESS":
        return jsonify({
            "state": result.state,
            "result": result.result
        })

    return jsonify({"state": result.state}), 202


if __name__ == "__main__":
    # By default, Flask listens on 127.0.0.1 (localhost). 
    # For other devices to access it, bind to 0.0.0.0
    # If using Docker, the ports: "5000:5000" mapping handles this for you, 
    # so the container listens externally on port 5000
    app.run(host="0.0.0.0", port=5000)
