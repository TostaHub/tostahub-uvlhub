from locust import HttpUser, TaskSet, task
from core.environment.host import get_host_for_locust_testing


class ExploreBehavior(TaskSet):
    def on_start(self):
        """Se ejecuta una vez al inicio de cada usuario."""
        self.index()

    @task(1)
    def index(self):
        """Tarea principal para acceder a /explore."""
        with self.client.get("/explore", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Explore index failed: {response.status_code}")
            else:
                response.success()

    @task(2)
    def explore_with_query(self):
        """Accede a /explore con parámetros de consulta."""
        params = {"query": "author:1;min_size:500;tags:tag2"}
        with self.client.get("/explore", params=params, catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Explore with query failed: {response.status_code}")
            else:
                response.success()

    @task(1)
    def explore_with_sorting(self):
        """Accede a /explore con parámetro de ordenación."""
        params = {"sorting": "oldest"}
        with self.client.get("/explore", params=params, catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Explore with sorting failed: {response.status_code}")
            else:
                response.success()


class ExploreUser(HttpUser):
    tasks = [ExploreBehavior]
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()
