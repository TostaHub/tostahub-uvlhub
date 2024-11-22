from sqlalchemy import or_, func
from sqlalchemy.orm import aliased
from app import db
from app.modules.dataset.models import Author, DSMetaData, DataSet, PublicationType
from app.modules.featuremodel.models import FeatureModel
from app.modules.hubfile.models import Hubfile
from core.repositories.BaseRepository import BaseRepository
from datetime import datetime


def safe_parse_date(date, date_format, default_date=None):
    try:
        return datetime.strptime(date, date_format)
    except ValueError:
        return default_date


class ExploreRepository(BaseRepository):
    def __init__(self):
        super().__init__(DataSet)

    def filter(self, query_string, sorting="newest", publication_type="any",
               start_date="", end_date="", min_uvl="", max_uvl="", **kwargs):

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

        date_format = '%Y-%m-%d'
        if start_date:
            date_obj = safe_parse_date(start_date, date_format)
            query = query.filter(func.date(DataSet.created_at) >= date_obj)

        if end_date:
            date_obj = safe_parse_date(end_date, date_format)
            query = query.filter(func.date(DataSet.created_at) <= date_obj)

        # Realizamos la unión con Hubfile a través de FeatureModel
        query = query.join(FeatureModel, FeatureModel.data_set_id == DataSet.id)  # Unión con FeatureModel
        query = query.join(Hubfile, Hubfile.feature_model_id == FeatureModel.id)  # Unión con Hubfile

        if min_uvl.isdigit():
            query = query.group_by(DataSet.id).having(func.count(Hubfile.id) >= int(min_uvl))

        if max_uvl.isdigit():
            query = query.group_by(DataSet.id).having(func.count(Hubfile.id) <= int(max_uvl))

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
