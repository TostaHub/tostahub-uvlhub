from sqlalchemy import or_
from sqlalchemy.orm import aliased
from app import db
from app.modules.dataset.models import DSMetaData, DataSet, Author, PublicationType
from core.repositories.BaseRepository import BaseRepository


class ExploreRepository(BaseRepository):
    def __init__(self):
        super().__init__(DataSet)

    def filter_datasets(self, query_string, sorting="newest", tags=[], publication_type="any"):
        # Crear un alias para `ds_meta_data` para evitar conflictos de alias.
        ds_meta_data_alias = aliased(DSMetaData)
        author_meta_data_alias = aliased(DSMetaData)  # Nuevo alias para la segunda unión
        min_size_filter = None
        max_size_filter = None

        # Inicia la consulta, usando el alias en la unión
        query = db.session.query(DataSet).join(ds_meta_data_alias, DataSet.ds_meta_data)

        # Filtrar por tipo de publicación
        if publication_type != "any":
            matching_type = None
            for member in PublicationType:
                if member.value.lower() == publication_type:
                    matching_type = member
                    break
            if matching_type is not None:
                query = query.filter(ds_meta_data_alias.publication_type == matching_type.name)

        # Procesar el filtro de `query_string`
        query_filter = query_string.strip()

        # Filtrar por autor
        if query_filter.startswith('author:'):
            author_filter = query_filter[7:].strip()
            query = query.join(author_meta_data_alias).join(Author).filter(Author.name.ilike(f'%{author_filter}%'))

        # Filtrar por tamaño mínimo
        elif query_filter.startswith('min_size:'):
            try:
                min_size_filter = int(query_filter[9:].strip())
            except ValueError:
                min_size_filter = None

        # Filtrar por tamaño máximo
        elif query_filter.startswith('max_size:'):
            try:
                max_size_filter = int(query_filter[9:].strip())
            except ValueError:
                max_size_filter = None

        # Filtrar por etiquetas
        elif query_filter.startswith('tags:'):
            tags_filter = query_filter[5:].strip()
            query = query.filter(ds_meta_data_alias.tags.ilike(f'%{tags_filter}%'))

        # Filtrar por título o tag(consulta general)
        else:
            query = query.filter(
                or_(
                    ds_meta_data_alias.title.ilike(f"%{query_filter}%"),
                    ds_meta_data_alias.tags.ilike(f"%{query_filter}%")
                )
            )

        # Ordenar resultados
        if sorting == "oldest":
            query = query.order_by(DataSet.created_at.asc())
        else:
            query = query.order_by(DataSet.created_at.desc())

        # Ejecutar la consulta y obtener todos los resultados
        results = query.all()

        # Filtrar por tamaño mínimo después de obtener los resultados
        if min_size_filter is not None:
            results = [ds for ds in results if ds.get_file_total_size() >= min_size_filter]

        # Filtrar por tamaño máximo después de obtener los resultados
        if max_size_filter is not None:
            results = [ds for ds in results if ds.get_file_total_size() <= max_size_filter]

        return results
