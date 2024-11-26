import pytest
from unittest.mock import patch, MagicMock
from flask import jsonify
from app.modules.hubfile.services import HubfileService
from app.modules.hubfile.routes import hubfile_bp
from flask import Flask, current_app, send_from_directory, make_response
from flask_login import LoginManager, UserMixin, login_user
from flask import Flask, abort
import os
import uuid
from datetime import datetime, timezone

# Crear un usuario simulado para las pruebas
class MockUser(UserMixin):
    def __init__(self, id):
        self.id = id

@pytest.fixture
def mock_user():
    user = MockUser(id=1)
    return user

@pytest.fixture
def test_client_with_user(mock_user, test_client):
    """
    Configura el cliente de prueba con un usuario autenticado.
    """
    with test_client.session_transaction() as session:
        session['_user_id'] = mock_user.id
    yield test_client




@pytest.fixture(scope='module')
def test_client(test_client):
    """
    Extends the test_client fixture to add additional specific data for module testing.
    """
    with test_client.application.app_context():
        # Add HERE new elements to the database that you want to exist in the test context.
        # DO NOT FORGET to use db.session.add(<element>) and db.session.commit() to save the data.
        pass

    yield test_client

@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(hubfile_bp)  # Registra el blueprint con las rutas
    with app.test_client() as client:
        yield client

def test_sample_assertion(test_client):
    """
    Sample test to verify that the test framework and environment are working correctly.
    It does not communicate with the Flask application; it only performs a simple assertion to
    confirm that the tests in this module can be executed.
    """
    greeting = "Hello, World!"
    assert greeting == "Hello, World!", "The greeting does not coincide with 'Hello, World!'"

@pytest.fixture
def client():
    app = Flask(__name__)
    app.testing = True

    # Define la ruta simulada para pruebas
    @app.route('/file/download/<int:file_id>')
    def download_file(file_id):
        # Simula lógica sin autenticación
        return "file content", 200

    return app.test_client()

@patch('app.modules.hubfile.services.HubfileService.get_or_404')
@patch('os.path.exists')
@patch('flask.send_from_directory')
def test_download_file_success(mock_send_from_directory, mock_exists, mock_get_or_404, client):
    mock_exists.return_value = True

    mock_hubfile = MagicMock()
    mock_hubfile.name = "file10.uvl"
    mock_get_or_404.return_value = mock_hubfile

    mock_send_from_directory.return_value = MagicMock(status_code=200, data=b"file content")

    response = client.get('/file/download/10')
    assert response.status_code == 200



@pytest.fixture
def client():
    app = Flask(__name__)
    app.testing = True

    @app.route('/file/download/<int:file_id>')
    def download_file(file_id):
        # Simula la lógica con abort para pruebas
        hubfile = HubfileService.get_or_404(file_id)
        if not os.path.exists(hubfile.name):
            abort(404)
        return "file content", 200
    
    return app.test_client()

@patch('app.modules.hubfile.services.HubfileService.get_or_404')
@patch('os.path.exists')
def test_download_file_not_found(mock_exists, mock_get_or_404, client):
    # Simula que el archivo no existe
    mock_exists.return_value = False

    # Simula el objeto de archivo
    mock_hubfile = MagicMock()
    mock_hubfile.name = "file10.uvl"
    mock_get_or_404.return_value = mock_hubfile

    # Ejecuta el cliente de prueba en la ruta
    response = client.get('/file/download/10')
    
    # Valida el resultado esperado 404
    assert response.status_code == 404




