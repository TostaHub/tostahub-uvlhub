import pytest
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


def test_to_glencoe_get(test_client):
    valid_uvl_file_id = 1
    uvl_transformations_test(test_client, "to_glencoe", valid_uvl_file_id, 200)
    file_id_not_exists = 10
    uvl_transformations_test(test_client, "to_glencoe", file_id_not_exists, 404)
    invalid_uvl_file_id = 2
    uvl_transformations_test(test_client, "to_glencoe", invalid_uvl_file_id, 500)
    file_doesnt_exist = 3
    uvl_transformations_test(test_client, "to_glencoe", file_doesnt_exist, 404)


def test_to_splot_get(test_client):
    valid_uvl_file_id = 1
    uvl_transformations_test(test_client, "to_splot", valid_uvl_file_id, 200)
    file_id_not_exists = 10
    uvl_transformations_test(test_client, "to_splot", file_id_not_exists, 500)
    invalid_uvl_file_id = 2
    uvl_transformations_test(test_client, "to_splot", invalid_uvl_file_id, 500)
    file_doesnt_exist = 3
    uvl_transformations_test(test_client, "to_splot", file_doesnt_exist, 500)


def test_to_cnf_get(test_client):
    valid_uvl_file_id = 1
    uvl_transformations_test(test_client, "to_cnf", valid_uvl_file_id, 200)
    file_id_not_exists = 10
    uvl_transformations_test(test_client, "to_cnf", file_id_not_exists, 500)
    invalid_uvl_file_id = 2
    uvl_transformations_test(test_client, "to_cnf", invalid_uvl_file_id, 500)
    file_doesnt_exist = 3
    uvl_transformations_test(test_client, "to_cnf", file_doesnt_exist, 500)


def uvl_transformations_test(client, to_format, file_id, expected_code):
    response = client.get("/flamapy/" + to_format + "/" + str(file_id))
    msg = "Transform uvl file: " + str(file_id) + to_format + " responded " \
        + str(response.status_code) + " but expected " + str(expected_code)
    print(response.get_json())
    assert response.status_code == expected_code, msg


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
