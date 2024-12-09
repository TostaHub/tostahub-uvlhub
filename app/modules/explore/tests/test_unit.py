import pytest
from app.modules.dataset.models import PublicationType
from app.modules.common.dbutils import create_dataset_db


@pytest.fixture(scope='module')
def test_client(test_client):
    """
    Extends the test_client fixture to add additional specific data for module testing.
    """
    with test_client.application.app_context():
        create_dataset_db(1, PublicationType.BOOK, "tag1,tag2")
        create_dataset_db(2, PublicationType.ANNOTATION_COLLECTION, "tag2")
        create_dataset_db(3, PublicationType.BOOK, date="2020-1-1")
        create_dataset_db(4, valid=False)

        pass

    yield test_client


def test_explore_get(test_client):
    """
    Tests access to explore GET request.
    """

    response = test_client.get("/explore")
    assert response.status_code == 200, "The explore page could not be accessed."


def test_explore_post(test_client):
    """
    Tests access to explore POST request.
    """

    search_criteria = get_search_criteria()

    response = test_client.post("/explore", json=search_criteria)
    assert response.status_code == 200, "The explore page could not be accessed."
    assert len(response.get_json()) == 4, "Wrong number of datasets"


def test_explore_filter_num_uvls_post(test_client):
    search_criteria = get_search_criteria(min_uvl="1")
    response = test_client.post("/explore", json=search_criteria)
    assert response.status_code == 200, "The explore page could not be accessed."
    num_ds = len(response.get_json())
    assert num_ds == 4, f"Wrong number of datasets: {num_ds}"

    search_criteria = get_search_criteria(max_uvl="0")
    response = test_client.post("/explore", json=search_criteria)
    assert response.status_code == 200, "The explore page could not be accessed."
    num_ds = len(response.get_json())
    assert num_ds == 0, f"Wrong number of datasets: {num_ds}"

    wrong_num = "notanumber"
    search_criteria = get_search_criteria(max_uvl=wrong_num, min_uvl=wrong_num)
    response = test_client.post("/explore", json=search_criteria)
    assert response.status_code == 200, "The explore page could not be accessed."


def test_explore_filter_num_configurations_post(test_client):
    search_criteria = get_search_criteria(min_num_configurations="1")
    response = test_client.post("/explore", json=search_criteria)
    assert response.status_code == 200, "The explore page could not be accessed."
    num_conf = len(response.get_json())
    assert num_conf == 4, f"Wrong number of datasets: {num_conf}"

    search_criteria = get_search_criteria(max_num_configurations="0")
    response = test_client.post("/explore", json=search_criteria)
    assert response.status_code == 200, "The explore page could not be accessed."
    num_conf = len(response.get_json())
    assert num_conf == 1, f"Wrong number of datasets: {num_conf}"

    search_criteria = get_search_criteria(min_num_configurations="1", max_num_configurations="30")
    response = test_client.post("/explore", json=search_criteria)
    assert response.status_code == 200, "The explore page could not be accessed."
    num_conf = len(response.get_json())
    assert num_conf == 4, f"Wrong number of datasets: {num_conf}"

    wrong_num = "notanumber"
    search_criteria = get_search_criteria(min_num_configurations=wrong_num, max_num_configurations=wrong_num)
    response = test_client.post("/explore", json=search_criteria)
    assert response.status_code == 200, "The explore page could not be accessed."


def test_explore_filter_date_post(test_client):
    # Date formate: %Y-%m-%d
    search_criteria = get_search_criteria(start_date="2020-2-2", end_date="2025-1-1")
    response = test_client.post("/explore", json=search_criteria)
    assert response.status_code == 200, "The explore page could not be accessed."
    num = len(response.get_json())
    assert num == 3, f"Wrong number of datasets: {num}"

    search_criteria = get_search_criteria(start_date="2025-1-1")
    response = test_client.post("/explore", json=search_criteria)
    assert response.status_code == 200, "The explore page could not be accessed."
    num = len(response.get_json())
    assert num == 0, f"Wrong number of datasets: {num}"

    search_criteria = get_search_criteria(end_date="2020-2-2")
    response = test_client.post("/explore", json=search_criteria)
    assert response.status_code == 200, "The explore page could not be accessed."
    num = len(response.get_json())
    assert num == 1, f"Wrong number of datasets: {num}"

    wrong_date = "notadate"
    search_criteria = get_search_criteria(start_date=wrong_date, end_date=wrong_date)
    response = test_client.post("/explore", json=search_criteria)
    assert response.status_code == 200, "The explore page could not be accessed."


def test_explore_filter_publication_type_post(test_client):
    search_criteria = get_search_criteria(publication_type="book")
    response = test_client.post("/explore", json=search_criteria)
    assert response.status_code == 200, "The explore page could not be accessed."
    num = len(response.get_json())
    assert num == 2, f"Wrong number of datasets: {num}"

    search_criteria = get_search_criteria(publication_type="any")
    response = test_client.post("/explore", json=search_criteria)
    assert response.status_code == 200, "The explore page could not be accessed."
    num = len(response.get_json())
    assert num == 4, f"Wrong number of datasets: {num}"

    wrong_publication_type = "ERROR"
    search_criteria = get_search_criteria(publication_type=wrong_publication_type)
    response = test_client.post("/explore", json=search_criteria)
    assert response.status_code == 200, "The explore page could not be accessed."
    num = len(response.get_json())
    assert num == 4, f"Wrong number of datasets: {num}"


def test_explore_filter_query_post(test_client):
    search_criteria = get_search_criteria(query="Sample dataset 1")
    response = test_client.post("/explore", json=search_criteria)
    assert response.status_code == 200, "The explore page could not be accessed."
    num = len(response.get_json())
    assert num == 1, f"Wrong number of datasets: {num}"

    dataset_not_exists = "Sample dataset wrong"
    search_criteria = get_search_criteria(query=dataset_not_exists)
    response = test_client.post("/explore", json=search_criteria)
    assert response.status_code == 200, "The explore page could not be accessed."
    num = len(response.get_json())
    assert num == 0, f"Wrong number of datasets: {num}"


def test_explore_mixed_filter_post(test_client):
    search_criteria = get_search_criteria(query="Sample dataset 3", end_date="2020-2-2", publication_type="book")
    response = test_client.post("/explore", json=search_criteria)
    assert response.status_code == 200, "The explore page could not be accessed."
    num = len(response.get_json())
    assert num == 1, f"Wrong number of datasets: {num}"

    search_criteria = get_search_criteria(query="Sample dataset 3", end_date="2020-2-2", publication_type="none")
    response = test_client.post("/explore", json=search_criteria)
    assert response.status_code == 200, "The explore page could not be accessed."
    num = len(response.get_json())
    assert num == 0, f"Wrong number of datasets: {num}"


def test_explore_filter_by_valid_uvl_post(test_client):
    search_criteria = get_search_criteria(by_valid_uvls="on")
    response = test_client.post("/explore", json=search_criteria)
    assert response.status_code == 200, "The explore page could not be accessed."
    num = len(response.get_json())
    assert num == 3, f"Wrong number of datasets: {num}"

    search_criteria = get_search_criteria(by_valid_uvls="off")
    response = test_client.post("/explore", json=search_criteria)
    assert response.status_code == 200, "The explore page could not be accessed."
    num = len(response.get_json())
    assert num == 4, f"Wrong number of datasets: {num}"


def test_explore_soring_post(test_client):
    search_criteria = get_search_criteria(sorting="oldest")
    response = test_client.post("/explore", json=search_criteria)
    assert response.status_code == 200, "The explore page could not be accessed."
    num = len(response.get_json())
    assert num == 4, f"Wrong number of datasets: {num}"


def get_search_criteria(query="", sorting="newest", publication_type="any",
                        start_date="", end_date="", min_uvl="", max_uvl="",
                        by_valid_uvls="off", min_num_configurations="", max_num_configurations=""):
    search_criteria = {
        "by_valid_uvls": by_valid_uvls,
        "end_date": end_date,
        "max_num_configurations": max_num_configurations,
        "max_uvl": max_uvl,
        "min_num_configurations": min_num_configurations,
        "min_uvl": min_uvl,
        "publication_type": publication_type,
        "query": query,
        "sorting": sorting,
        "start_date": start_date,
    }
    return search_criteria
