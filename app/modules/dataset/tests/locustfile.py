from locust import HttpUser, TaskSet, task
from core.environment.host import get_host_for_locust_testing
import time

class DatasetBehavior(TaskSet):
    def on_start(self):
        """Realiza el login antes de iniciar las tareas de la prueba."""
        response = self.client.post('/login', json={
            'email': 'user1@example.com',
            'password': '1234'
        })
        if response.status_code == 200:
            print("Login exitoso.")
            self.token = response.json().get("token", None)
        else:
            self.token = None
            print("Error en el login:", response.status_code)

    @task(2)
    def edit_dataset_success(self):
        """Simula un usuario editando un dataset exitosamente."""
        # Agregar un retraso para permitir que los valores se actualicen
        time.sleep(5)  # Espera 5 segundos
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        response = self.client.post('/dataset/1/edit', json={
            "description": "Updated description from Locust",
            "publication_type": "RESEARCH_PAPER",
            "tags": "locust, test"
        }, headers=headers)
        if response.status_code == 200:
            print("Dataset editado exitosamente.")
        else:
            print("Error al editar el dataset:", response.status_code, response.text)

    @task(1)
    def edit_dataset_unauthorized(self):
        """Simula un usuario no autenticado intentando editar un dataset."""
        response = self.client.post('/dataset/1/edit', json={
            "description": "Unauthorized edit attempt",
            "publication_type": "RESEARCH_PAPER",
            "tags": "unauthorized"
        })
        if response.status_code == 401 or response.status_code == 403:
            print("Error esperado: No autorizado.")
        else:
            print("Error inesperado:", response.status_code, response.text)

    @task(1)
    def view_dataset(self):
        """Simula un usuario viendo un dataset."""
        response = self.client.get('/dataset/1')
        if response.status_code == 200:
            print("Dataset visto exitosamente.")
        else:
            print("Error al ver el dataset:", response.status_code, response.text)

    @task(1)
    def view_nonexistent_dataset(self):
        """Simula un usuario intentando ver un dataset inexistente."""
        response = self.client.get('/dataset/9999')
        if response.status_code == 404:
            print("Error esperado: Dataset no encontrado.")
        else:
            print("Error inesperado:", response.status_code, response.text)

class DatasetUser(HttpUser):
    tasks = [DatasetBehavior]
    min_wait = 5000  # Tiempo de espera mínimo en milisegundos (5 segundos)
    max_wait = 9000  # Tiempo de espera máximo en milisegundos (9 segundos)
    host = get_host_for_locust_testing()
