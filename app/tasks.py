from celery import Celery
import random
import time
from time import sleep

# Broker role: Queue tasks.
#     When you call get_some_sleep.delay(5), Celery does not run the task immediately.
#     Instead, it serializes the task message (function name + arguments) and pushes it into Redis.

# Workers role: 
#     Celery workers subscribe to Redis and pull tasks from the queue.

# Workflow:
#     1. Flask receives POST /GetSomeSleep → calls get_some_sleep.delay(5)
#     2. Celery pushes the task message to Redis (broker)
#     3. One of your Celery workers pulls the task from Redis
#     4. Worker executes time.sleep(5) and computes a random quality
#     5. Result is stored in Redis (result backend)
#     6. Flask /GetTaskResult/<task_id> can fetch it via AsyncResult(task_id).result ==> returns JSON

celery_app = Celery(
    "tasks",
    broker="redis://redis:6379/0", # Redis as the message broker, Task messages go to DB 0
    backend="redis://redis:6379/1" # Redis also as the result backend (optional), Task results go to DB 1
)

from database import SessionLocal, SleepResult

@celery_app.task(bind=True)
def get_some_sleep(self, sleep_seconds: int):
    time.sleep(sleep_seconds)
    quality = random.randint(1, 10)

    db = SessionLocal()
    result = SleepResult(
        sleep_seconds=sleep_seconds,
        quality=quality
    )
    db.add(result)
    db.commit()
    db.close()

    return {"sleep_seconds": sleep_seconds, "quality": quality}

