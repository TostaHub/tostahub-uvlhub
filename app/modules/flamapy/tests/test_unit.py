import pytest
from app.modules.common.dbutils import create_dataset_db


@pytest.fixture(scope='module')
def test_client(test_client):
    """
    Extends the test_client fixture to add additional specific data for module testing.
    """
    with test_client.application.app_context():
        create_dataset_db(1)
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
    file_id_exists = 1
    num_configurations_test(test_client, file_id_exists, 200)
    file_id_not_exists = 2
    num_configurations_test(test_client, file_id_not_exists, 404)


def num_configurations_test(client, file_id, expected_code):
    response = client.get("/flamapy/num_configurations/" + str(file_id))
    msg = "Get num configurations of file " + str(file_id) + " responded " \
        + str(response.status_code) + " but expected " + str(expected_code)
    assert response.status_code == expected_code, msg
