import requests
import random
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

API_URL = "http://localhost:5000/GetSomeSleep"
RESULT_URL = "http://localhost:5000/GetTaskResult"
RESULTS_FILE = "sleep_results.txt"

POLL_INTERVAL = 0.5  # seconds interval


def launch_tasks(n):
    task_ids = []

    print(f"\nLaunching {n} tasks...\n")

    for i in range(n):
        seconds = random.randint(10, 20)

        response = requests.post(
            API_URL,
            json={"sleep_seconds": seconds}
        )

        response.raise_for_status()
        task_id = response.json()["task_id"]

        print(f"[{i+1}/{n}] Launched task {task_id} ({seconds}s)")
        task_ids.append(task_id)

    return task_ids


def poll_single_task(task_id):
    """Poll a single task until it finishes safely."""
    while True:
        try:
            r = requests.get(f"{RESULT_URL}/{task_id}")
            # print("DEBUG STATUS:", r.status_code, r.text)

            # If server error → retry
            if r.status_code >= 500:
                time.sleep(POLL_INTERVAL)
                continue

            # If task not ready yet (202)
            if r.status_code == 202:
                time.sleep(POLL_INTERVAL)
                continue

            # If not OK → print and stop
            if r.status_code != 200:
                return {
                    "task_id": task_id,
                    "error": f"Unexpected status {r.status_code}"
                }

            # Now safe to parse JSON
            data = r.json()

            if data["state"] == "SUCCESS":
                return {
                    "task_id": task_id,
                    "sleep_seconds": data["result"]["sleep_seconds"],
                    "quality": data["result"]["quality"]
                }

        except requests.exceptions.JSONDecodeError:
            # Response was not JSON (e.g., HTML error page)
            time.sleep(POLL_INTERVAL)

        except requests.exceptions.RequestException as e:
            # Network or connection error
            print(f"Network error for {task_id}: {e}")
            time.sleep(POLL_INTERVAL)


def fetch_results_concurrently(task_ids):
    results = []
    total = len(task_ids)
    completed = 0

    print("\nPolling results concurrently...\n")

    with ThreadPoolExecutor(max_workers=len(task_ids)) as executor:
        future_to_task = {
            executor.submit(poll_single_task, task_id): task_id
            for task_id in task_ids
        }

        for future in as_completed(future_to_task):
            result = future.result()
            results.append(result)

            completed += 1
            if "error" in result:
                print(
                    f"✖ Completed {completed}/{total} "
                    f"(Task {result['task_id']} → ERROR: {result['error']})"
                )
            else:
                print(
                    f"✔ Completed {completed}/{total} "
                    f"(Task {result['task_id']} → "
                    f"{result['sleep_seconds']}s, quality {result['quality']})"
                )

    return results


if __name__ == "__main__":
    N = 10

    start_time = time.time()

    task_ids = launch_tasks(N)
    results = fetch_results_concurrently(task_ids)

    with open(RESULTS_FILE, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    duration = time.time() - start_time

    print(f"\nAll tasks finished in {duration:.2f} seconds")
    print(f"Results saved to {RESULTS_FILE}\n")
