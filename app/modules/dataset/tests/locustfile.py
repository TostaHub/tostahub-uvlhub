import random
from locust import HttpUser, TaskSet, task
from core.environment.host import get_host_for_locust_testing


class DatasetBehavior(TaskSet):
    def on_start(self):

        """Realiza el login antes de iniciar las tareas de la prueba."""
        response = self.client.post('/login', json={
            'email': 'user1@example.com',
            'password': '1234'
        })
        if response.status_code == 200:
            print("Login exitoso.")

            self.session_cookies = response.cookies
        else:
            print("Error en el login:", response.status_code, response.text)
            self.session_cookies = None

        self.dataset()
        self.login()
        self.create_dataset()
        self.view_user_datasets()


    def is_authenticated(self):
        """Comprueba si el login fue exitoso."""
        return self.session_cookies is not None

    def post_with_auth(self, url, json=None):
        """Realiza una solicitud POST autenticada."""
        if not self.is_authenticated():
            print("Usuario no autenticado. No se puede realizar la solicitud.")
            return None

        # Añade cookies al realizar solicitudes
        return self.client.post(url, json=json, cookies=self.session_cookies)

    @task(1)
    def rate_dataset_success(self):
        """Simula un usuario calificando un dataset exitosamente."""
        response = self.post_with_auth('/datasets/10/rate', json={"rating": 4})
        if response and response.status_code == 200:
            print("Rating agregado exitosamente.")
        elif response:
            print("Error al agregar el rating:", response.status_code, response.text)

    @task(2)
    def rate_dataset_invalid_rating(self):
        """Simula un usuario enviando un rating inválido mayor a 5."""
        response = self.post_with_auth('/datasets/10/rate', json={"rating": 12})
        if response and response.status_code == 400:
            print("Error esperado: Rating inválido.")
        elif response:
            print("Error inesperado:", response.status_code, response.text)

    @task(1)
    def rate_dataset_not_found(self):
        """Simula un usuario intentando calificar un dataset que no existe."""
        response = self.post_with_auth("/datasets/100/rate", json={"rating": 3})
        if response and response.status_code == 404:
            print("Error esperado: Dataset no encontrado.")
        elif response:
            print("Error inesperado:", response.status_code, response.text)

    @task(1)
    def rate_dataset_unauthorized(self):
        """Simula un usuario no autenticado intentando calificar un dataset."""
        response = self.client.post('/datasets/17/rate', json={"rating": 4})
        if response.status_code == 302 or response.status_code == 401:
            print("Error esperado: No autorizado.")
        else:
            print("Error inesperado:", response.status_code, response.text)

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
    min_wait = 5000  # Tiempo de espera mínimo en milisegundos (5 segundos)
    max_wait = 9000  # Tiempo de espera máximo en milisegundos (9 segundos)
    host = get_host_for_locust_testing()
