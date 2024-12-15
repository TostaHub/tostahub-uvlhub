from datetime import datetime
from flask import app
import pytest
from flask.testing import FlaskClient
from app import create_app, db
from app.modules.auth.models import User
from app.modules.dataset.models import DataSet, DSMetaData, PublicationType
from app.modules.profile.models import UserProfile
from app.modules.conftest import login
import unittest
from unittest.mock import patch, MagicMock
import os


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


class TestDownloadAllFormats(unittest.TestCase):
    def setUp(self):
        # Configura una instancia de la aplicación para pruebas
        self.app = app.test_client()
        self.app.testing = True

    @patch('app.modules.dataset.routes.generate_uvl_file')
    @patch('app.modules.dataset.routes.generate_glencoe_file')
    @patch('app.modules.dataset.routes.generate_cnf_file')
    @patch('app.modules.dataset.routes.generate_splot_file')
    @patch('app.modules.dataset.routes.send_file')
    def test_download_all_formats_success(
        self,
        mock_send_file,
        mock_generate_splot,
        mock_generate_cnf,
        mock_generate_glencoe,
        mock_generate_uvl
    ):
        # Mockear las rutas de los archivos generados
        mock_generate_uvl.return_value = '/tmp/file.uvl'
        mock_generate_glencoe.return_value = '/tmp/file_glencoe.json'
        mock_generate_cnf.return_value = '/tmp/file.cnf'
        mock_generate_splot.return_value = '/tmp/file.splx'

        # Mockear el comportamiento de send_file
        mock_send_file.return_value = MagicMock()

        # Simular la existencia de los archivos
        for path in [
            mock_generate_uvl.return_value,
            mock_generate_glencoe.return_value,
            mock_generate_cnf.return_value,
            mock_generate_splot.return_value
        ]:
            with open(path, 'w') as f:
                f.write('mock content')

        # Hacer la solicitud a la ruta
        response = self.app.get('/download_all/123')

        # Validar que la respuesta sea exitosa
        self.assertEqual(response.status_code, 200)
        mock_send_file.assert_called_once()

        # Verificar que los métodos de generación se llamaron con el ID correcto
        mock_generate_uvl.assert_called_once_with(123)
        mock_generate_glencoe.assert_called_once_with(123)
        mock_generate_cnf.assert_called_once_with(123)
        mock_generate_splot.assert_called_once_with(123)

        # Limpiar los archivos temporales
        for path in [
            mock_generate_uvl.return_value,
            mock_generate_glencoe.return_value,
            mock_generate_cnf.return_value,
            mock_generate_splot.return_value
        ]:
            if os.path.exists(path):
                os.remove(path)

    @patch('app.modules.dataset.routes.generate_uvl_file')
    @patch('app.modules.dataset.routes.generate_glencoe_file')
    @patch('app.modules.dataset.routes.generate_cnf_file')
    @patch('app.modules.dataset.routes.generate_splot_file')
    def test_download_all_formats_file_generation_failure(
        self,
        mock_generate_splot,
        mock_generate_cnf,
        mock_generate_glencoe,
        mock_generate_uvl
    ):
        # Simular que una de las funciones de generación lanza un error
        mock_generate_uvl.side_effect = RuntimeError("UVL generation failed")
        mock_generate_glencoe.return_value = '/tmp/file_glencoe.json'
        mock_generate_cnf.return_value = '/tmp/file.cnf'
        mock_generate_splot.return_value = '/tmp/file.splx'

        # Hacer la solicitud a la ruta
        response = self.app.get('/download_all/123')

        # Validar que la respuesta indique un error
        self.assertEqual(response.status_code, 500)
        self.assertIn(b'"error": "UVL generation failed"', response.data)

        # Verificar que las funciones se llamaron
        mock_generate_uvl.assert_called_once_with(123)
        mock_generate_glencoe.assert_not_called()
        mock_generate_cnf.assert_not_called()
        mock_generate_splot.assert_not_called()


if __name__ == '__main__':
    unittest.main()
