from datetime import datetime
import os
import pytest
from flask.testing import FlaskClient
from app import create_app, db
from app.modules.auth.models import User
from app.modules.conftest import login
from app.modules.dataset.models import DSMetaData, DSRating, DataSet, PublicationType
from app.modules.featuremodel.models import FMMetaData, FeatureModel
from app.modules.profile.models import UserProfile


@pytest.fixture
def client():
    app = create_app('testing')
    with app.test_client() as client:
        with app.app_context():
            # Configuración de la base de datos en modo de prueba
            db.drop_all()
            db.create_all()

            user = User(
                id=5,
                email="user5@example.com",
                password="1234",
                created_at=datetime(2022, 3, 13)
            )
            db.session.add(user)
            db.session.commit()

            profile = UserProfile(
                user_id=user.id,
                surname="TestSurname",
                name="TestName",
                affiliation="TestAffiliation",
                orcid="0000-0001-2345-6789"
            )
            db.session.add(profile)
            db.session.commit()

            dsmetadata = DSMetaData(
                id=10,
                title="Sample Dataset 11",
                rating=0,
                description="Description for dataset 11",
                publication_type=PublicationType.DATA_MANAGEMENT_PLAN.name
            )
            db.session.add(dsmetadata)
            dataset = DataSet(
                id=10,
                user_id=user.id,
                ds_meta_data_id=dsmetadata.id
            )
            db.session.add(dataset)
            db.session.commit()

            dsrating = DSRating(
                id=10,
                user_id=user.id,
                ds_meta_data_id=dsmetadata.id,
                rating=dsmetadata.rating,
                rated_date=datetime(2022, 3, 13)
            )
            db.session.add(dsrating)
            db.session.commit()

            # Crear un dataset en el staging area
            dsmetadata_sa = DSMetaData(
                id=11,
                title="Staging area Dataset",
                description="Description for unique dataset",
                publication_type=PublicationType.DATA_MANAGEMENT_PLAN.name
            )
            db.session.add(dsmetadata_sa)
            dataset_staging_area = DataSet(
                id=11,
                user_id=user.id,
                ds_meta_data_id=dsmetadata_sa.id
            )
            db.session.add(dataset_staging_area)
            db.session.commit()

            user1 = User(
                id=6,
                email="user6@example.com",
                password="1234",
                created_at=datetime(2022, 3, 13)
            )
            db.session.add(user1)
            db.session.commit()

            fm_metadata = FMMetaData(
                uvl_filename="test_model.uvl",
                title="Test Feature Model",
                description="A feature model for testing purposes",
                publication_type=PublicationType.DATA_MANAGEMENT_PLAN.name,
                publication_doi="",
                tags="test,feature,model",
                uvl_version="1.0"
            )
            db.session.add(fm_metadata)
            db.session.commit()

            # Crear un FeatureModel relacionado con un DataSet
            feature_model = FeatureModel(
                data_set_id=dataset.id,
                fm_meta_data_id=fm_metadata.id
            )
            db.session.add(feature_model)
            db.session.commit()
            # Crear el archivo temporal en la ruta esperada
            temp_folder = os.path.join('uploads', 'temp', str(user.id))
            os.makedirs(temp_folder, exist_ok=True)
            with open(os.path.join(temp_folder, 'file9.uvl'), 'w') as f:
                f.write('Temporary file content')
            yield client

            # Limpiar el archivo temporal después de la prueba
            if os.path.exists(os.path.join(temp_folder, 'file9.uvl')):
                os.remove(os.path.join(temp_folder, 'file9.uvl'))
            if os.path.exists(temp_folder):
                os.rmdir(temp_folder)

            db.session.remove()
            db.drop_all()


def test_rate_dataset_success(client: FlaskClient):
    login_response = login(client, "user5@example.com", "1234")
    assert login_response.status_code == 200, "Login was unsuccessful."
    print("Login Response:", login_response.data)  # Para ver el contenido de la respuesta
    response = client.post('/datasets/10/rate', json={"rating": 4})
    assert response.status_code == 200


def test_rate_dataset_invalid_rating(client: FlaskClient):
    login_response = login(client, "user5@example.com", "1234")
    assert login_response.status_code == 200, "Login was unsuccessful."
    print("Login Response:", login_response.data)  # Para ver el contenido de la respuesta
    response = client.post('/datasets/10/rate', json={"rating": 12})
    assert response.status_code == 400
    assert response.json["error"] == "Rating must be between 1 and 5."


def test_rate_dataset_not_found(client: FlaskClient):
    login_response = login(client, "user5@example.com", "1234")
    assert login_response.status_code == 200, "Login was unsuccessful."
    """Prueba para un dataset inexistente."""
    response = client.post("/datasets/100/rate", json={"rating": 3})
    assert response.status_code == 404
    assert response.json["error"] == "Dataset not found."


def test_rate_dataset_unauthorized(client):
    """Prueba enviar un rating sin estar autenticado."""
    # Enviar una calificación sin autenticación
    rating_data = {'rating': 4}
    response = client.post('/datasets/10/rate', json=rating_data)

    assert response.status_code == 401, "El código de estado debería ser 401 para usuarios no autenticados."
    data = response.get_json()
    assert 'error' in data, "La respuesta debería contener un mensaje de error."
