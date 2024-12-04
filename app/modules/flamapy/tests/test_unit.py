import os
import shutil
from app import db
from app.modules.auth.models import User
from app.modules.dataset.models import (
    DataSet,
    DSMetaData,
    PublicationType,
    DSMetrics)
from app.modules.hubfile.models import Hubfile
from app.modules.featuremodel.models import FMMetaData, FeatureModel
from datetime import datetime, timezone
from dotenv import load_dotenv


import pytest


@pytest.fixture(scope='module')
def test_client(test_client):
    """
    Extends the test_client fixture to add additional specific data for module testing.
    """
    with test_client.application.app_context():
        user_test = User(email='user@example.com', password='test1234')
        db.session.add(user_test)
        db.session.commit()

        ds_metrics = DSMetrics(number_of_models='1', number_of_features='5')
        db.session.add(ds_metrics)
        db.session.commit()

        ds_meta_data = DSMetaData(
                deposition_id=1,
                title='Sample dataset 1',
                description='Description for dataset 1',
                publication_type=PublicationType.DATA_MANAGEMENT_PLAN,
                publication_doi='10.1234/dataset1',
                dataset_doi='10.1234/dataset1',
                tags='tag1, tag2',
                ds_metrics_id=ds_metrics.id
            )
        db.session.add(ds_meta_data)
        db.session.commit()

        dataset = DataSet(
                user_id=user_test.id,
                ds_meta_data_id=ds_meta_data.id,
                created_at=datetime.now(timezone.utc)
            )
        db.session.add(dataset)
        db.session.commit()

        fm_meta_data = FMMetaData(
                uvl_filename='file1.uvl',
                title='Feature Model 1',
                description='Description for feature model 1',
                publication_type=PublicationType.SOFTWARE_DOCUMENTATION,
                publication_doi='10.1234/fm1',
                tags='tag1, tag2',
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

        load_dotenv()
        working_dir = os.getenv('WORKING_DIR', '')
        file_name = 'file1.uvl'
        src_folder = os.path.join(working_dir, 'app', 'modules', 'dataset', 'uvl_examples')

        dest_folder = os.path.join(working_dir, 'uploads', f'user_{user_test.id}', f'dataset_{dataset.id}')
        os.makedirs(dest_folder, exist_ok=True)
        shutil.copy(os.path.join(src_folder, file_name), dest_folder)

        file_path = os.path.join(dest_folder, file_name)

        uvl_file = Hubfile(
            name=file_name,
            checksum='checksum1',
            size=os.path.getsize(file_path),
            feature_model_id=feature_model.id
        )
        db.session.add(uvl_file)
        db.session.commit()

        pass

    yield test_client


def test_sample_assertion(test_client):
    """
    Sample test to verify that the test framework and environment are working correctly.
    It does not communicate with the Flask application; it only performs a simple assertion to
    confirm that the tests in this module can be executed.
    """
    greeting = "Hello, World!"
    assert greeting == "Hello, World!", "The greeting does not coincide with 'Hello, World!'"


def test_num_configurations_get(test_client):
    """
    Tests GET request of num of configurations of given file ids.
    """

    num_configurations(test_client, 1, 200)
    num_configurations(test_client, 2, 404)


def num_configurations(client, file_id, expected_code):
    response = client.get("/flamapy/num_configurations/" + str(file_id))
    msg = "Get num configurations of file " + str(file_id) + " responded " \
        + str(response.status_code) + " but expected " + str(expected_code)
    assert response.status_code == expected_code, msg
