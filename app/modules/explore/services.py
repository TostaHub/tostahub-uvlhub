from app.modules.explore.repositories import ExploreRepository


class ExploreService:
    def __init__(self):
        self.repository = ExploreRepository()

    def filter(self, query_string: str, sorting="newest", tags=[], publication_type="any"):
        """Filtra los datasets a partir de una cadena de consulta."""
        # Pasa los parámetros adicionales al repositorio
        return self.repository.filter_datasets(query_string, sorting, tags, publication_type)
