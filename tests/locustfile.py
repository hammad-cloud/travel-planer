"""Load/stress test for `adk api_server`. Hits only endpoints that don't call Gemini, so it costs no API quota."""
import os

from locust import HttpUser, between, events, task


class ApiUser(HttpUser):
    wait_time = between(0.5, 2)

    @task(3)
    def list_apps(self):
        self.client.get("/list-apps")

    @task
    def create_session(self):
        self.client.post("/apps/travel_planner/users/load-test/sessions", json={})


@events.quitting.add_listener
def check_thresholds(environment, **_):
    # Fail the CI step when the server is too slow or erroring; limits come from the workflow.
    stats = environment.stats.total
    max_fail = float(os.getenv("MAX_FAIL_RATIO", "0.01"))
    max_p95 = int(os.getenv("MAX_P95_MS", "1000"))
    p95 = stats.get_response_time_percentile(0.95)
    print(f"requests={stats.num_requests} fail_ratio={stats.fail_ratio:.2%} p95={p95}ms")
    if stats.num_requests == 0 or stats.fail_ratio > max_fail or p95 > max_p95:
        print(f"FAILED: limits are fail_ratio<={max_fail:.0%}, p95<={max_p95}ms")
        environment.process_exit_code = 1
