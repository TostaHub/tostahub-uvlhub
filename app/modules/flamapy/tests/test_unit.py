import pytest
from flask import Flask
from unittest.mock import patch, MagicMock
from app.modules.flamapy.routes import flamapy_bp
from app.modules.common.dbutils import create_dataset_db


@pytest.fixture(scope='module')
def test_client(test_client):
    """
    Extends the test_client fixture to add additional specific data for module testing.
    """
    with test_client.application.app_context():
        create_dataset_db(1)
        create_dataset_db(2, valid=False)
        create_dataset_db(3, should_file_exist=False)
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


def test_valid_uvl_get(test_client):
    valid_uvl_file_id = 1
    valid_uvl_test(test_client, valid_uvl_file_id, 200)
    file_id_not_exists = 10
    valid_uvl_test(test_client, file_id_not_exists, 500)
    invalid_uvl_file_id = 2
    valid_uvl_test(test_client, invalid_uvl_file_id, 400)
    file_doesnt_exist = 3
    valid_uvl_test(test_client, file_doesnt_exist, 500)


def valid_uvl_test(client, file_id, expected_code):
    response = client.get("/flamapy/check_uvl/" + str(file_id))
    msg = "Get valid uvl of file " + str(file_id) + " responded " \
        + str(response.status_code) + " but expected " + str(expected_code)
    print(response.get_json())
    assert response.status_code == expected_code, msg


# TEST DE GLENCOE
@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(flamapy_bp)  # Registra el blueprint con las rutas
    with app.test_client() as client:
        yield client


@patch('app.modules.hubfile.services.HubfileService.get_or_404')
@patch('os.path.isfile')
@patch('flamapy.metamodels.fm_metamodel.transformations.UVLReader')
@patch('flamapy.metamodels.fm_metamodel.transformations.GlencoeWriter')
def test_to_glencoe_success(mock_glencoe_writer, mock_uvl_reader, mock_isfile, mock_get_or_404, client):
    # Simula que el archivo existe
    mock_isfile.return_value = True
    # Mock del HubfileService para devolver un archivo simulado
    mock_hubfile = MagicMock()
    mock_hubfile.name = "file10.uvl"
    mock_get_or_404.return_value = mock_hubfile
    # Mock de UVLReader y GlencoeWriter
    mock_uvl_reader.return_value.transform.return_value = "mocked_feature_model"
    mock_glencoe_writer.return_value.transform.return_value = None

    response = client.get('/flamapy/to_glencoe/10')
    assert response.status_code == 200
    assert response.headers["Content-Disposition"] == "attachment; filename=file10.uvl_glencoe.txt"


@patch('app.modules.hubfile.services.HubfileService.get_or_404')
@patch('os.path.isfile')
def test_to_glencoe_file_not_found(mock_isfile, mock_get_or_404, client):
    # Simula que el archivo no existe en el sistema de archivos
    mock_isfile.return_value = False
    # Mock de HubfileService para devolver un archivo simulado
    mock_hubfile = MagicMock()
    mock_hubfile.name = "file10.uvl"
    mock_get_or_404.return_value = mock_hubfile
    # Realiza la solicitud GET a la ruta
    response = client.get('/flamapy/to_glencoe/10')
    # Verifica que el código de estado es 404
    assert response.status_code == 404
    assert response.json["error"] == "File file10.uvl not found"
# Error inesperado dentro de la lógica del código de servicio


@patch('app.modules.hubfile.services.HubfileService.get_or_404')
@patch('os.path.isfile')
def test_to_glencoe_unexpected(mock_isfile, mock_get_or_404, client):
    # Simula que el archivo existe
    mock_isfile.return_value = False  # No existe en el sistema de archivos
    # Mock de HubfileService para lanzar un error inesperado
    mock_get_or_404.side_effect = ValueError("Unexpected error")  # Simula un error inesperado
    # Realiza la solicitud GET a la ruta
    response = client.get('/flamapy/to_glencoe/5')
    # Verifica que el código de estado es 500
    assert response.status_code == 500
    assert response.json["error"] == "Internal Server Error"
    assert response.json["details"] == "Unexpected error"


# TEST DE SPLOT
@patch('app.modules.hubfile.services.HubfileService.get_by_id')
@patch('os.path.isfile')
@patch('flamapy.metamodels.fm_metamodel.transformations.UVLReader')
@patch('flamapy.metamodels.fm_metamodel.transformations.SPLOTWriter')
def test_to_splot_success(mock_splot_writer, mock_uvl_reader, mock_isfile, mock_get_by_id, client):
    # Simula que el archivo existe
    mock_isfile.return_value = True
    # Mock del HubfileService para devolver un archivo simulado
    mock_hubfile = MagicMock()
    mock_hubfile.name = "file10.uvl"
    mock_get_by_id.return_value = mock_hubfile
    # Mock de UVLReader y SPLOTWriter
    mock_uvl_reader.return_value.transform.return_value = "mocked_feature_model"
    mock_splot_writer.return_value.transform.return_value = None

    # Realiza la solicitud GET a la ruta
    response = client.get('/flamapy/to_splot/10')
    # Verifica que el código de estado es 200
    assert response.status_code == 200
    # Verifica que el archivo se está devolviendo como attachment
    assert response.headers["Content-Disposition"] == "attachment; filename=file10.uvl_splot.txt"


@patch('app.modules.hubfile.services.HubfileService.get_by_id')
@patch('os.path.isfile')
def test_to_splot_file_not_found(mock_isfile, mock_get_by_id, client):
    # Simula que el archivo no existe en el sistema de archivos
    mock_isfile.return_value = False
    # Mock de HubfileService para devolver un archivo simulado
    mock_hubfile = MagicMock()
    mock_hubfile.name = "file10.uvl"
    mock_get_by_id.return_value = mock_hubfile
    # Realiza la solicitud GET a la ruta
    response = client.get('/flamapy/to_splot/10')
    # Verifica que el código de estado es 404
    assert response.status_code == 404
    assert response.json["error"] == "File file10.uvl not found"


@patch('app.modules.hubfile.services.HubfileService.get_by_id')
@patch('os.path.isfile')
def test_to_splot_unexpected(mock_isfile, mock_get_by_id, client):
    # Simula que el archivo existe
    mock_isfile.return_value = True  # El archivo existe en el sistema
    # Mock de HubfileService para lanzar un error inesperado
    mock_get_by_id.side_effect = ValueError("Unexpected error")  # Simula un error inesperado
    # Realiza la solicitud GET a la ruta
    response = client.get('/flamapy/to_splot/5')
    # Verifica que el código de estado es 500
    assert response.status_code == 500
    assert response.json["error"] == "Internal Server Error"
    assert response.json["details"] == "Unexpected error"


# TEST DE CNF
@patch('app.modules.hubfile.services.HubfileService.get_by_id')
@patch('os.path.isfile')
@patch('flamapy.metamodels.fm_metamodel.transformations.UVLReader')
@patch('flamapy.metamodels.pysat_metamodel.transformations.FmToPysat')
@patch('flamapy.metamodels.pysat_metamodel.transformations.DimacsWriter')
def test_to_cnf_success(mock_dimacs_writer, mock_fm_to_pysat, mock_uvl_reader, mock_isfile, mock_get_by_id, client):
    # Simula que el archivo existe
    mock_isfile.return_value = True
    # Mock del HubfileService para devolver un archivo simulado
    mock_hubfile = MagicMock()
    mock_hubfile.name = "file10.uvl"
    mock_get_by_id.return_value = mock_hubfile
    # Mock de UVLReader, FmToPysat y DimacsWriter
    mock_uvl_reader.return_value.transform.return_value = "mocked_feature_model"
    mock_fm_to_pysat.return_value.transform.return_value = "mocked_sat"
    mock_dimacs_writer.return_value.transform.return_value = None
    # Realiza la solicitud GET a la ruta
    response = client.get('/flamapy/to_cnf/10')
    # Verifica que el código de estado es 200
    assert response.status_code == 200
    # Verifica que el archivo se está devolviendo como attachment con el nombre correcto
    assert response.headers["Content-Disposition"] == "attachment; filename=file10.uvl_cnf.txt"


@patch('app.modules.hubfile.services.HubfileService.get_by_id')
@patch('os.path.isfile')
def test_to_cnf_file_not_found(mock_isfile, mock_get_by_id, client):
    # Simula que el archivo no existe
    mock_isfile.return_value = False
    # Mock del HubfileService para devolver un archivo simulado
    mock_hubfile = MagicMock()
    mock_hubfile.name = "file10.uvl"
    mock_get_by_id.return_value = mock_hubfile
    # Realiza la solicitud GET a la ruta
    response = client.get('/flamapy/to_cnf/10')
    # Verifica que el código de estado es 404
    assert response.status_code == 404
    # Verifica el mensaje de error
    assert response.json["error"] == "File file10.uvl not found"


@patch('app.modules.hubfile.services.HubfileService.get_by_id')
@patch('os.path.isfile')
def test_to_cnf_unexpected(mock_isfile, mock_get_by_id, client):
    # Simula que el archivo existe
    mock_isfile.return_value = True  # El archivo "existe"
    # Mock del HubfileService para devolver un archivo simulado
    mock_hubfile = MagicMock()
    mock_hubfile.name = "file10.uvl"
    mock_get_by_id.return_value = mock_hubfile
    # Simula un error inesperado al llamar al servicio
    mock_get_by_id.side_effect = ValueError("Unexpected error")
    # Realiza la solicitud GET a la ruta
    response = client.get('/flamapy/to_cnf/10')
    # Verifica que el código de estado es 500
    assert response.status_code == 500
    # Verifica el mensaje de error y los detalles
    assert response.json["error"] == "Internal Server Error"
    assert response.json["details"] == "Unexpected error"


@patch('app.modules.hubfile.services.HubfileService.get_by_id')
@patch('os.path.isfile')
def test_num_configurations_get(test_client):
    """
    Tests GET request of num of configurations of given file ids.
    """
    file_id_exists = 1
    num_configurations_test(test_client, file_id_exists, 200)
    file_id_not_exists = 10
    num_configurations_test(test_client, file_id_not_exists, 500)
    invalid_uvl_file_id = 2
    num_configurations_test(test_client, invalid_uvl_file_id, 500)
    file_doesnt_exist = 3
    num_configurations_test(test_client, file_doesnt_exist, 500)


def num_configurations_test(client, file_id, expected_code):
    response = client.get("/flamapy/num_configurations/" + str(file_id))
    msg = "Get num configurations of file " + str(file_id) + " responded " \
        + str(response.status_code) + " but expected " + str(expected_code)
    assert response.status_code == expected_code, msg
