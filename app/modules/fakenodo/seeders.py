# app/modules/fakenodo/seeders/fakenodo_seeder.py

from core.seeders.BaseSeeder import BaseSeeder
from app.modules.fakenodo.models import Fakenodo


class FakenodoSeeder(BaseSeeder):
    
    def run(self):
        # Datos a insertar en la base de datos
        data = [
            {
                "dep_metadata": {
                    "title": "Dataset 1",
                    "description": "Este es el primer dataset.",
                    "creators": [{"name": "Autor 1", "affiliation": "Universidad X"}],
                    "keywords": ["flask", "fakenodo"],
                    "license": "CC-BY-4.0"
                }
            },
            {
                "dep_metadata": {
                    "title": "Dataset 2",
                    "description": "Este es el segundo dataset.",
                    "creators": [{"name": "Autor 2", "affiliation": "Universidad Y"}],
                    "keywords": ["python", "fakenodo"],
                    "license": "CC-BY-4.0"
                }
            }
        ]
        
        # Insertar los datos en la base de datos
        for item in data:
            fakenodo = Fakenodo(**item)  # Crear una instancia del modelo Fakenodo
            self.db.session.add(fakenodo)  # Añadirlo a la sesión
        self.db.session.commit()  # Confirmar los cambios en la base de datos

