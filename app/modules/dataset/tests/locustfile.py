import random
from locust import HttpUser, TaskSet, task
from core.locust.common import get_csrf_token
from core.environment.host import get_host_for_locust_testing


class DatasetBehavior(TaskSet):
    def on_start(self):
        self.dataset()
        self.login()
        self.create_dataset()
        self.view_user_datasets()

    @task
    def dataset(self):
        response = self.client.get("/dataset/upload")
        get_csrf_token(response)

    def login(self):
        """Simula el inicio de sesión del usuario."""
        response = self.client.post(
            "/login",
            {
                "username": "test_user",
                "password": "test_password"
            },
            name="User Login"
        )
        self.csrf_token = get_csrf_token(response)

    @task
    def create_dataset(self):
        """Simula la creación de un nuevo dataset."""
        dataset_payload = {
            "title": f"Test Dataset {random.randint(1, 10000)}",
            "description": "This is a test dataset created during load testing.",
            "publication_type": "Open Access",
            "_csrf_token": self.csrf_token

        }
        with self.client.post(
            "/dataset/upload",
            data=dataset_payload,
            name="Create Dataset",
            catch_response=True
        ) as response:
            if response.status_code != 200 or "error" in response.text.lower():
                response.failure("Dataset creation failed")

    @task
    def view_user_datasets(self):
        """Simula la visualización de la página de datasets del usuario."""
        user_id = 7  # Cambiar según el ID del usuario deseado
        with self.client.get(
            f"/api/v1/datasets/user/{user_id}",
            name="View User Datasets",
            catch_response=True
        ) as response:
            if response.status_code != 200 or "No datasets found" in response.text:
                response.failure("Failed to load datasets page")


class DatasetUser(HttpUser):
    tasks = [DatasetBehavior]
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()
