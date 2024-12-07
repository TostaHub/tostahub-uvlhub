from locust import HttpUser, TaskSet, task
from core.environment.host import get_host_for_locust_testing


class DatasetBehavior(TaskSet):
    def on_start(self):
        """Realiza el login antes de iniciar las tareas de la prueba."""
        response = self.client.post('/login', json={
            'email': 'user5@example.com',
            'password': '1234'
        })
        if response.status_code == 200:
            print("Login exitoso.")
        else:
            print("Error en el login:", response.status_code)

    @task(1)
    def rate_dataset_success(self):
        """Simula un usuario calificando un dataset exitosamente."""
        response = self.client.post('/datasets/10/rate', json={"rating": 4})
        if response.status_code == 200:
            print("Rating agregado exitosamente.")
        else:
            print("Error al agregar el rating:", response.status_code, response.text)

    @task(2)
    def rate_dataset_invalid_rating(self):
        """Simula un usuario enviando un rating inválido mayor a 5."""
        response = self.client.post('/datasets/10/rate', json={"rating": 12})
        if response.status_code == 400:
            print("Error esperado: Rating inválido.")
        else:
            print("Error inesperado:", response.status_code, response.text)

    @task(1)
    def rate_dataset_not_found(self):
        """Simula un usuario intentando calificar un dataset que no existe."""
        response = self.client.post("/datasets/100/rate", json={"rating": 3})
        if response.status_code == 404:
            print("Error esperado: Dataset no encontrado.")
        else:
            print("Error inesperado:", response.status_code, response.text)

    @task(1)
    def rate_dataset_unauthorized(self):
        """Simula un usuario no autenticado intentando calificar un dataset."""
        response = self.client.post('/datasets/17/rate', json={"rating": 4})
        if response.status_code == 302 or response.status_code == 401:
            print("Error esperado: No autorizado.")
        else:
            print("Error inesperado:", response.status_code, response.text)


class DatasetUser(HttpUser):
    tasks = [DatasetBehavior]
    min_wait = 5000  # Tiempo de espera mínimo en milisegundos (5 segundos)
    max_wait = 9000  # Tiempo de espera máximo en milisegundos (9 segundos)
    host = get_host_for_locust_testing()
