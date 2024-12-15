from datetime import datetime
import time
from flask import current_app
import pytest
from flask.testing import FlaskClient
from app import create_app, db
from app.modules.auth.models import User
from app.modules.dataset.models import DataSet, DSMetaData, PublicationType
from app.modules.profile.models import UserProfile
from app.modules.conftest import login
import pdb


@pytest.fixture
def client():
    app = create_app('testing')
    with app.test_client() as client:
        with app.app_context():
            # Configuración de la base de datos en modo de prueba
            db.drop_all()
            db.create_all()

            # Crear usuario principal y perfil asociado
            user = User(
                id=1,
                email="user1@example.com",
                password="1234",
                created_at=datetime(2022, 3, 13)
            )
            db.session.add(user)
            db.session.commit()

            profile = UserProfile(
                user_id=user.id,
                surname="UserSurname",
                name="UserName",
                affiliation="TestAffiliation",
                orcid="0000-0001-2345-6789"
            )
            db.session.add(profile)
            db.session.commit()

            # Crear dataset con metadata
            dsmetadata = DSMetaData(
                id=1,
                title="Editable Dataset",
                description="Initial description",
                publication_type=PublicationType.DATA_MANAGEMENT_PLAN.name,
                tags="sample, dataset"
            )
            db.session.add(dsmetadata)
            dataset = DataSet(
                id=1,
                user_id=user.id,
                ds_meta_data_id=dsmetadata.id
            )
            db.session.add(dataset)
            db.session.commit()

            # Crear otro usuario sin acceso al dataset
            other_user = User(
                id=2,
                email="user2@example.com",
                password="1234",
                created_at=datetime(2022, 3, 13)
            )
            db.session.add(other_user)
            db.session.commit()

            yield client

            db.session.remove()
            db.drop_all()



def test_edit_dataset_access_denied(client: FlaskClient):
    """Prueba para asegurar que un usuario no propietario no pueda editar un dataset."""
    # Iniciar sesión como otro usuario (no propietario del dataset)
    login_response = login(client, "user2@example.com", "1234")
    assert login_response.status_code == 200, "Login was unsuccessful."

    # Intentar editar el dataset
    response = client.post(
        '/dataset/1/edit',
        data={
            "description": "Another description",
            "publication_type": "RESEARCH_PAPER",
            "tags": "unauthorized, edit"
        }
    )
    assert response.status_code == 403, "El código de estado debería ser 403 para usuarios no autorizados."


def test_edit_dataset_invalid_form(client: FlaskClient):
    """Prueba para un formulario inválido."""
    # Iniciar sesión como propietario del dataset
    login_response = login(client, "user1@example.com", "1234")
    assert login_response.status_code == 200, "Login was unsuccessful."

    # Intentar enviar un formulario con datos inválidos
    response = client.post(
        '/dataset/1/edit',
        data={
            "description": "",  # Campo requerido vacío
            "publication_type": "INVALID_TYPE",  # Tipo de publicación inválido
            "tags": ""
        }
    )
    assert response.status_code == 200, "El código de estado debería ser 200 al mostrar los errores del formulario."


def test_edit_dataset_not_found(client: FlaskClient):
    """Prueba para intentar editar un dataset inexistente."""
    # Iniciar sesión como usuario válido
    login_response = login(client, "user1@example.com", "1234")
    assert login_response.status_code == 200, "Login was unsuccessful."

    # Intentar acceder a un dataset inexistente
    response = client.get('/dataset/999/edit')
    assert response.status_code == 404, "El código de estado debería ser 404 para un dataset inexistente."
