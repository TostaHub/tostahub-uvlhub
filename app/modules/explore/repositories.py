from sqlalchemy import or_, func
from sqlalchemy.orm import aliased
from app import db
from app.modules.dataset.models import Author, DSMetaData, DataSet, PublicationType
from app.modules.featuremodel.models import FeatureModel
from app.modules.hubfile.models import Hubfile
from app.modules.flamapy.routes import check_uvl, get_num_configurations
from core.repositories.BaseRepository import BaseRepository
from datetime import datetime


def safe_parse_date(date, date_format, default_date=None):
    try:
        return datetime.strptime(date, date_format)
    except ValueError:
        print("error")
        return default_date


class ExploreRepository(BaseRepository):
    def __init__(self):
        super().__init__(DataSet)

    def filter(self, query_string, sorting="newest", publication_type="any",
               start_date="", end_date="", min_uvl="", max_uvl="",
               by_valid_uvls="", min_num_configurations="", max_num_configurations="", **kwargs):

        # Crear un alias para `ds_meta_data` para evitar conflictos de alias.
        ds_meta_data_alias = aliased(DSMetaData)
        author_meta_data_alias = aliased(DSMetaData)  # Nuevo alias para la segunda unión
        min_size_filter = None
        max_size_filter = None

        # Inicia la consulta, usando el alias en la unión
        query = db.session.query(DataSet).join(ds_meta_data_alias, DataSet.ds_meta_data)\
            .filter(DSMetaData.dataset_doi.isnot(None))

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

        for filter_item in query_filter.split(';'):
            # Filtrar por autor
            if filter_item.startswith('author:'):
                author_filter = filter_item[7:].strip()
                query = query.join(author_meta_data_alias).join(Author).filter(Author.name.ilike(f'%{author_filter}%'))

            # Filtrar por tamaño mínimo
            elif filter_item.startswith('min_size:'):
                try:
                    min_size_filter = int(filter_item[9:].strip())
                except ValueError:
                    min_size_filter = None

            # Filtrar por tamaño máximo
            elif filter_item.startswith('max_size:'):
                try:
                    max_size_filter = int(filter_item[9:].strip())
                except ValueError:
                    max_size_filter = None

            # Filtrar por etiquetas
            elif filter_item.startswith('tags:'):
                tags_filter = filter_item[5:].strip()
                query = query.filter(ds_meta_data_alias.tags.ilike(f'%{tags_filter}%'))

            # Filtrar por numero maximo de modelos
            elif filter_item.startswith('max_models:'):
                max_model_filter = filter_item[11:].strip()
                max_uvl = max_model_filter

            # Filtrar por numero minimo de modelos
            elif filter_item.startswith('min_models:'):
                min_model_filter = filter_item[11:].strip()
                min_uvl = min_model_filter

            # Filtrar por numero maximo de configuraciones
            elif filter_item.startswith('max_configs:'):
                max_config_filter = filter_item[12:].strip()
                max_num_configurations = max_config_filter

            # Filtrar por numero minimo de configuraciones
            elif filter_item.startswith('min_configs:'):
                min_config_filter = filter_item[12:].strip()
                min_num_configurations = min_config_filter

            # Filtrar por título o tag(consulta general)
            else:
                query = query.filter(
                    or_(
                        ds_meta_data_alias.title.ilike(f"%{filter_item}%"),
                        ds_meta_data_alias.tags.ilike(f"%{filter_item}%")
                    )
                )

        date_format = '%Y-%m-%d'
        if start_date:
            date_obj = safe_parse_date(start_date, date_format)
            if date_obj is not None:
                query = query.filter(func.date(DataSet.created_at) >= date_obj)

        if end_date:
            date_obj = safe_parse_date(end_date, date_format)
            if date_obj is not None:
                query = query.filter(func.date(DataSet.created_at) <= date_obj)

        # Realizamos la unión con Hubfile a través de FeatureModel
        query = query.join(FeatureModel, FeatureModel.data_set_id == DataSet.id)  # Unión con FeatureModel
        query = query.join(Hubfile, Hubfile.feature_model_id == FeatureModel.id)  # Unión con Hubfile

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

        if by_valid_uvls == "on":
            results = [
                ds for ds in results
                if all(
                    all(
                        check_uvl(file.id)[1] == 200
                        for file in fm.files
                    )
                    for fm in ds.feature_models
                )
            ]

        if min_uvl.isdigit() or max_uvl.isdigit():
            results = [
                ds for ds in results
                if num_uvls_between(ds, min_uvl, max_uvl)
            ]

        if min_num_configurations.isdigit() or max_num_configurations.isdigit():
            results = [
                ds for ds in results
                if all(
                    all(
                        num_configurations_between(file.id, min_num_configurations, max_num_configurations)
                        for file in fm.files
                    )
                    for fm in ds.feature_models
                )
            ]

        return results


def num_uvls_between(dataset, min_num, max_num):
    num = dataset.get_files_count()
    valid_min = min_num.isdigit()
    valid_max = max_num.isdigit()
    if valid_min and valid_max:
        return num >= int(min_num) and num <= int(max_num)
    else:
        return (valid_min and num >= int(min_num)
                or valid_max and num <= int(max_num))


def num_configurations_between(file_id, min_num_configurations, max_num_configurations):
    result, status_code = get_num_configurations(file_id)

    if status_code == 200:
        num = int(result.json["result"])
        valid_min = min_num_configurations.isdigit()
        valid_max = max_num_configurations.isdigit()
        if valid_min and valid_max:
            return num >= int(min_num_configurations) and num <= int(max_num_configurations)
        else:
            return (valid_min and num >= int(min_num_configurations)
                    or valid_max and num <= int(max_num_configurations))

    return True
