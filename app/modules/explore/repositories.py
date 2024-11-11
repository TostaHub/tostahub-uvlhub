from app import db
from app.modules.dataset.models import DSMetaData, DataSet, Author
from core.repositories.BaseRepository import BaseRepository


class ExploreRepository(BaseRepository):
    def __init__(self):
        super().__init__(DataSet)

    def filter_datasets(self, query_string):
        """Aplica filtros a los datasets según los parámetros en la cadena de consulta"""
        query = db.session.query(DataSet)

        # Extraer filtros de la cadena de consulta
        query_filter = query_string.strip()

        # Filtrar por autor, solo si la cadena empieza con 'author:'
        if query_filter.startswith('author:'):
            author_filter = query_filter[7:].strip()
            query = query.join(DSMetaData).join(Author).filter(Author.name.ilike(f'%{author_filter}%'))

        # Filtrar por tamaño mínimo de archivo, solo si la cadena empieza con 'min_size:'
        elif query_filter.startswith('min_size:'):
            try:
                min_size = int(query_filter[9:].strip())  # Extrayendo el valor después de 'min_size:'
                query = query.filter(DataSet.get_file_total_size() >= min_size)
            except ValueError:
                pass  # Si el valor no es un número válido, no se aplica el filtro

        # Filtrar por tamaño máximo de archivo, solo si la cadena empieza con 'max_size:'
        elif query_filter.startswith('max_size:'):
            try:
                max_size = int(query_filter[9:].strip())  # Extrayendo el valor después de 'max_size:'
                query = query.filter(DataSet.get_file_total_size() <= max_size)
            except ValueError:
                pass  # Si el valor no es un número válido, no se aplica el filtro

        # Filtrar por etiquetas, solo si la cadena empieza con 'tags:'
        elif query_filter.startswith('tags:'):
            tags_filter = query_filter[5:].strip()
            query = query.filter(DataSet.ds_meta_data.has(DSMetaData.tags.ilike(f'%{tags_filter}%')))

        # Filtrar por título, si la cadena no es un filtro específico
        else:
            # Si no es un filtro específico, buscar en el título
            query = (db.session.query(DataSet).join(DSMetaData).filter(DSMetaData.title.ilike(f'%{query_filter}%')))

        # Asegurarse de que los datasets devueltos solo incluyan los que tienen el filtro aplicado correctamente
        query = query.order_by(DataSet.created_at.desc())

        # Devolver los datasets filtrados
        return query.all()
