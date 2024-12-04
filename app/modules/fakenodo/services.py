import logging
import os

from app.modules.dataset.models import DataSet
from app.modules.fakenodo.models import Deposition
from app.modules.fakenodo.repositories import DepositionRepository
from app.modules.featuremodel.models import FeatureModel

from core.configuration.configuration import uploads_folder_name
from dotenv import load_dotenv
from flask_login import current_user


from core.services.BaseService import BaseService

logger = logging.getLogger(__name__)

load_dotenv()


class FakenodoService(BaseService):

    def __init__(self):
        self.deposition_repository = DepositionRepository()

    def create_new_deposition(self, dataset: DataSet) -> dict:
        """
        Create a new deposition in Fakenodo.

        Args:
            dataset (DataSet): The DataSet object containing the metadata of the deposition.

        Returns:
            dict: The response in JSON format with the details of the created deposition.
        """

        logger.info("Dataset sending to Fakenodo...")
        logger.info(f"Publication type...{dataset.ds_meta_data.publication_type.value}")

        metadata = {
            "title": dataset.ds_meta_data.title,
            "upload_type": "dataset" if dataset.ds_meta_data.publication_type.value == "none" else "publication",
            "publication_type": (
                dataset.ds_meta_data.publication_type.value
                if dataset.ds_meta_data.publication_type.value != "none"
                else None
            ),
            "description": dataset.ds_meta_data.description,
            "creators": [
                {
                    "name": author.name,
                    **({"affiliation": author.affiliation} if author.affiliation else {}),
                    **({"orcid": author.orcid} if author.orcid else {}),
                }
                for author in dataset.ds_meta_data.authors
            ],
            "keywords": (
                ["uvlhub"] if not dataset.ds_meta_data.tags else dataset.ds_meta_data.tags.split(", ") + ["uvlhub"]
            ),
            "access_right": "open",
            "license": "CC-BY-4.0",
        }

        try:
            new_deposition = self.deposition_repository.create_new_deposition(dep_metadata=metadata)

            return {
                "conceptrecid": f"fakenodo-{new_deposition.id}",
                "id": new_deposition.id,
                "metadata": metadata,
                "message": "Dataset created successfully in fakenodo."
            }
        except Exception as e:
            raise Exception(f"Failed to create local deposition: {str(e)}")

    def upload_file(self, dataset: DataSet, deposition_id: int, feature_model: FeatureModel, user=None) -> dict:
        """
        Save a file to a deposition in Fakenodo.

        Args:
            deposition_id (int): The ID of the deposition.
            feature_model (FeatureModel): The FeatureModel object representing the feature model.
            user (FeatureModel): The User object representing the file owner.

        Returns:
            dict: The response in JSON format with the details of the uploaded file.
        """
        uvl_filename = feature_model.fm_meta_data.uvl_filename
        user_id = current_user.id if user is None else user.id
        file_path = os.path.join(uploads_folder_name(), f"user_{str(user_id)}", f"dataset_{dataset.id}/", uvl_filename)

        response = {
            "id": deposition_id,
            "filename": uvl_filename,
            "filesize": os.path.getsize(file_path),
            "checksum": calculate_checksum(file_path),
            "message": "File uploaded successfully to fakenodo."
        }

        return response

    def publish_deposition(self, deposition_id: int) -> dict:
        """
        Publish a deposition in Fakenodo.

        Args:
            deposition_id (int): The ID of the deposition in Fakenodo.

        Returns:
            dict: The response in JSON format with the details of the published deposition.
        """
        deposition = Deposition.query.get(deposition_id)
        if not deposition:
            raise Exception("Deposition not found")

        try:
            deposition.doi = f"10.5281/fakenodo.{deposition_id}"
            deposition.status = "published"
            self.deposition_repository.update(deposition)

            response = {
                "id": deposition_id,
                "status": "published",
                "conceptdoi": f"10.5281/fakenodo.{deposition_id}",
                "message": "Deposition published successfully in fakenodo."
            }
            return response

        except Exception as e:
            raise Exception(f"Failed to publish deposition: {str(e)}")

    def get_deposition(self, deposition_id: int) -> dict:
        """
        Get a deposition from Fakenodo.

        Args:
            deposition_id (int): The ID of the deposition in Fakenodo.

        Returns:
            dict: The response in JSON format with the details of the deposition.
        """
        deposition = Deposition.query.get(deposition_id)
        if not deposition:
            raise Exception("Deposition not found")

        response = {
            "id": deposition.id,
            "doi": deposition.doi,
            "metadata": deposition.dep_metadata,
            "status": deposition.status,
            "message": "Deposition retrieved successfully from fakenodo."
        }
        return response

    def get_doi(self, deposition_id: int) -> str:
        """
        Get the DOI of a deposition from Fakenodo.

        Args:
            deposition_id (int): The ID of the deposition in Fakenodo.

        Returns:
            str: The DOI of the deposition.
        """
        return self.get_deposition(deposition_id).get("doi")


def calculate_checksum(file_path):
    import hashlib
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()
