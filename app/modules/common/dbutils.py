import os
import shutil
from app import db
from app.modules.auth.models import User
from app.modules.dataset.models import (
    Author,
    DataSet,
    DSMetaData,
    PublicationType,
    DSMetrics)
from app.modules.hubfile.models import Hubfile
from app.modules.featuremodel.models import FMMetaData, FeatureModel
from datetime import datetime, timezone
from dotenv import load_dotenv


def create_dataset_db(id, publication_type=PublicationType.DATA_MANAGEMENT_PLAN, tags="",
                      date="", valid=True, should_file_exist=True, authors=None, total_file_size=None, num_files=None):
    # Si no se proporcionan autores, usa un autor por defecto
    if authors is None:
        authors = [{"name": f"Author {id}", "affiliation": "Affiliation", "orcid": f"orcid{id}"}]

    user_test = User(email=f'user{id}@example.com', password='test1234')
    db.session.add(user_test)
    db.session.commit()

    ds_metrics = DSMetrics(number_of_models='1', number_of_features='5')
    db.session.add(ds_metrics)
    db.session.commit()

    ds_meta_data = DSMetaData(
            deposition_id=id,
            title=f'Sample dataset {id}',
            description=f'Description for dataset {id}',
            publication_type=publication_type,
            publication_doi=f'10.1234/dataset{id}',
            dataset_doi=f'10.1234/dataset{id}',
            tags=tags,
            ds_metrics_id=ds_metrics.id
        )
    db.session.add(ds_meta_data)
    db.session.commit()

    # Agregar autores al dataset
    for author in authors:
        author_obj = Author(name=author['name'], affiliation=author.get('affiliation', ''),
                            orcid=author.get('orcid', ''), ds_meta_data_id=ds_meta_data.id)
        db.session.add(author_obj)
    db.session.commit()

    created_at = datetime.now(timezone.utc) if date == "" else datetime.strptime(date, '%Y-%m-%d')
    dataset = DataSet(
            user_id=user_test.id,
            ds_meta_data_id=ds_meta_data.id,
            created_at=created_at
        )
    db.session.add(dataset)
    db.session.commit()

    fm_meta_data = FMMetaData(
            uvl_filename=f'file{id}.uvl',
            title=f'Feature Model {id}',
            description=f'Description for feature model {id}',
            publication_type=publication_type,
            publication_doi='10.1234/fm1',
            tags=tags,
            uvl_version='1.0'
        )
    db.session.add(fm_meta_data)
    db.session.commit()

    feature_model = FeatureModel(
            data_set_id=dataset.id,
            fm_meta_data_id=fm_meta_data.id
        )
    db.session.add(feature_model)
    db.session.commit()

    # Asignar archivos
    if should_file_exist:
        load_dotenv()
        working_dir = os.getenv('WORKING_DIR', '')
        file_name = f'file{id % 12}.uvl' if valid else 'invalidfile.uvl'
        src_folder = os.path.join(working_dir, 'app', 'modules', 'dataset', 'uvl_examples')

        dest_folder = os.path.join(working_dir, 'uploads', f'user_{user_test.id}', f'dataset_{dataset.id}')
        os.makedirs(dest_folder, exist_ok=True)
        shutil.copy(os.path.join(src_folder, file_name), dest_folder)

        file_path = os.path.join(dest_folder, file_name)

        uvl_file = Hubfile(
            name=file_name,
            checksum=f'checksum{id}',
            size=os.path.getsize(file_path),
            feature_model_id=feature_model.id
        )
        db.session.add(uvl_file)
        db.session.commit()

        # Si se especifica un tamaño total de archivos, ajustamos la lógica
        if total_file_size is not None:
            uvl_file.size = total_file_size
            db.session.commit()

        # Si se especifica el número de archivos, lo usamos
        if num_files is not None:
            for i in range(1, num_files):
                additional_file_name = f'file{id % 12 + i}.uvl'
                shutil.copy(os.path.join(src_folder, additional_file_name), dest_folder)

                additional_uvl_file = Hubfile(
                    name=additional_file_name,
                    checksum=f'checksum{id + i}',
                    size=os.path.getsize(file_path),
                    feature_model_id=feature_model.id
                )
                db.session.add(additional_uvl_file)
            db.session.commit()
