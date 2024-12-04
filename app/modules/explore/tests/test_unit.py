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
        create_dataset_db(3, PublicationType.BOOK)

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
    assert len(response.get_json()) == 3, "Wrong number of datasets"


def test_explore_filter_num_uvls_post(test_client):
    """
    Tests access to explore POST request with a filter.
    """

    search_criteria = get_search_criteria(max_uvl="1")
    response = test_client.post("/explore", json=search_criteria)
    assert response.status_code == 200, "The explore page could not be accessed."
    num_ds = len(response.get_json())
    assert num_ds == 3, f"Wrong number of datasets: {num_ds}"

    search_criteria = get_search_criteria(max_uvl="0")
    response = test_client.post("/explore", json=search_criteria)
    assert response.status_code == 200, "The explore page could not be accessed."
    num_ds = len(response.get_json())
    assert num_ds == 0, f"Wrong number of datasets: {num_ds}"


def test_explore_filter_num_configurations_post(test_client):
    """
    Tests access to explore POST request with a filter.
    """

    search_criteria = get_search_criteria(min_num_configurations="1")
    response = test_client.post("/explore", json=search_criteria)
    assert response.status_code == 200, "The explore page could not be accessed."
    num_conf = len(response.get_json())
    assert num_conf == 3, f"Wrong number of datasets: {num_conf}"

    search_criteria = get_search_criteria(max_num_configurations="0")
    response = test_client.post("/explore", json=search_criteria)
    assert response.status_code == 200, "The explore page could not be accessed."
    num_conf = len(response.get_json())
    assert num_conf == 0, f"Wrong number of datasets: {num_conf}"


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
