import json
import logging
import os
import shutil
import tempfile
import uuid
import io
import zipfile
from datetime import datetime, timezone
from zipfile import ZipFile


from flask import (abort, jsonify, make_response, render_template, send_file,
                   request, send_from_directory, url_for, flash, redirect)
from flask_login import current_user, login_required
from app.modules.dataset import dataset_bp
from app.modules.dataset.forms import DataSetForm
from app.modules.dataset.models import DSDownloadRecord, PublicationType
from app.modules.dataset.services import (
    AuthorService,
    DSDownloadRecordService,
    DSMetaDataService,
    DSViewRecordService,
    DataSetService,
    DOIMappingService,
    DSRatingService
)
from app.modules.fakenodo.services import FakenodoService
from app.modules.dataset.forms import EditDatasetForm
from werkzeug.exceptions import NotFound
from app.modules.hubfile.services import HubfileService
from flamapy.metamodels.fm_metamodel.transformations import UVLReader, GlencoeWriter, SPLOTWriter, UVLWriter
from flamapy.metamodels.pysat_metamodel.transformations import FmToPysat, DimacsWriter
from app.modules.zenodo.services import ZenodoService
from core.configuration.configuration import USE_FAKENODE

logger = logging.getLogger(__name__)


dataset_service = DataSetService()
author_service = AuthorService()
dsmetadata_service = DSMetaDataService()
nodo_service = FakenodoService() if USE_FAKENODE else ZenodoService()
doi_mapping_service = DOIMappingService()
ds_view_record_service = DSViewRecordService()
ds_rating_service = DSRatingService()


@dataset_bp.route("/dataset/upload", methods=["GET", "POST"])
@login_required
def create_dataset():
    form = DataSetForm()
    if request.method == "POST":

        dataset = None

        if not form.validate_on_submit():
            return jsonify({"message": form.errors}), 400

        try:
            logger.info("Creating dataset...")
            dataset = dataset_service.create_from_form(form=form, current_user=current_user)
            logger.info(f"Created dataset: {dataset}")
            dataset_service.move_feature_models(dataset)
        except Exception as exc:
            logger.exception(f"Exception while create dataset data in local {exc}")
            return jsonify({"Exception while create dataset data in local: ": str(exc)}), 400

        # send dataset as deposition to Zenodo/Fakenodo
        data = {}
        actualNode = "Fakenodo" if USE_FAKENODE else "Zenodo"
        try:
            nodo_response_json = nodo_service.create_new_deposition(dataset.ds_meta_data)
            response_data = json.dumps(nodo_response_json)
            data = json.loads(response_data)
        except Exception as exc:
            data = {}
            nodo_response_json = {}
            logger.exception(f"Exception while create dataset data in {actualNode} {exc}")

        deposition_id = data.get("id")
        if deposition_id:
            print("DEPOSITION")
            print(deposition_id)

            # update dataset with deposition id in Zenodo/Fakenodo
            dataset_service.update_dsmetadata(dataset.ds_meta_data_id, deposition_id=deposition_id)

            try:
                # iterate for each feature model (one feature model = one request to Zenodo/Fakenodo)
                for feature_model in dataset.feature_models:
                    nodo_service.upload_file(dataset, deposition_id, feature_model)

                # publish deposition
                nodo_service.publish_deposition(deposition_id)

                # update DOI
                deposition_doi = nodo_service.get_doi(deposition_id)
                dataset_service.update_dsmetadata(dataset.ds_meta_data_id, dataset_doi=deposition_doi)
            except Exception as e:
                msg = f"it has not been possible upload feature models in {actualNode} and update the DOI: {e}"
                return jsonify({"message": msg}), 200

        # Delete temp folder
        file_path = current_user.temp_folder()
        if os.path.exists(file_path) and os.path.isdir(file_path):
            shutil.rmtree(file_path)

        msg = "Everything works!"
        return jsonify({"message": msg}), 200

    return render_template("dataset/upload_dataset.html", form=form, use_fakenodo=USE_FAKENODE)


@dataset_bp.route("/dataset/list", methods=["GET", "POST"])
@login_required
def list_dataset():
    return render_template(
        "dataset/list_datasets.html",
        datasets=dataset_service.get_synchronized(current_user.id),
        local_datasets=dataset_service.get_unsynchronized(current_user.id),
    )


@dataset_bp.route("/api/v1/datasets/user/<int:user_id>", methods=["GET"])
def user_dataset(user_id):
    return render_template(
        "dataset/user_datasets.html",
        datasets=dataset_service.get_synchronized(user_id),
        local_datasets=dataset_service.get_unsynchronized(user_id),
    )


@dataset_bp.route("/dataset/file/upload", methods=["POST"])
@login_required
def upload():
    file = request.files["file"]
    temp_folder = current_user.temp_folder()

    if not file or not file.filename.endswith(".uvl"):
        return jsonify({"message": "No valid file"}), 400

    # create temp folder
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    file_path = os.path.join(temp_folder, file.filename)

    if os.path.exists(file_path):
        # Generate unique filename (by recursion)
        base_name, extension = os.path.splitext(file.filename)
        i = 1
        while os.path.exists(
            os.path.join(temp_folder, f"{base_name} ({i}){extension}")
        ):
            i += 1
        new_filename = f"{base_name} ({i}){extension}"
        file_path = os.path.join(temp_folder, new_filename)
    else:
        new_filename = file.filename

    try:
        file.save(file_path)
    except Exception as e:
        return jsonify({"message": str(e)}), 500

    return (
        jsonify(
            {
                "message": "UVL uploaded and validated successfully",
                "filename": new_filename,
            }
        ),
        200,
    )


@dataset_bp.route("/dataset/file/delete", methods=["POST"])
def delete():
    data = request.get_json()
    filename = data.get("file")
    temp_folder = current_user.temp_folder()
    filepath = os.path.join(temp_folder, filename)

    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({"message": "File deleted successfully"})

    return jsonify({"error": "Error: File not found"})


@dataset_bp.route("/dataset/download/<int:dataset_id>", methods=["GET"])
def download_dataset(dataset_id):
    dataset = dataset_service.get_or_404(dataset_id)

    file_path = f"uploads/user_{dataset.user_id}/dataset_{dataset.id}/"

    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, f"dataset_{dataset_id}.zip")

    with ZipFile(zip_path, "w") as zipf:
        for subdir, dirs, files in os.walk(file_path):
            for file in files:
                full_path = os.path.join(subdir, file)

                relative_path = os.path.relpath(full_path, file_path)

                zipf.write(
                    full_path,
                    arcname=os.path.join(
                        os.path.basename(zip_path[:-4]), relative_path
                    ),
                )

    user_cookie = request.cookies.get("download_cookie")
    if not user_cookie:
        user_cookie = str(
            uuid.uuid4()
        )  # Generate a new unique identifier if it does not exist
        # Save the cookie to the user's browser
        resp = make_response(
            send_from_directory(
                temp_dir,
                f"dataset_{dataset_id}.zip",
                as_attachment=True,
                mimetype="application/zip",
            )
        )
        resp.set_cookie("download_cookie", user_cookie)
    else:
        resp = send_from_directory(
            temp_dir,
            f"dataset_{dataset_id}.zip",
            as_attachment=True,
            mimetype="application/zip",
        )

    # Check if the download record already exists for this cookie
    existing_record = DSDownloadRecord.query.filter_by(
        user_id=current_user.id if current_user.is_authenticated else None,
        dataset_id=dataset_id,
        download_cookie=user_cookie
    ).first()

    if not existing_record:
        # Record the download in your database
        DSDownloadRecordService().create(
            user_id=current_user.id if current_user.is_authenticated else None,
            dataset_id=dataset_id,
            download_date=datetime.now(timezone.utc),
            download_cookie=user_cookie,
        )

    return resp


def generate_glencoe_file(file_id):
    temp_file = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
    try:
        hubfile = HubfileService().get_or_404(file_id)
        file_name = hubfile.name
        directory_path = "app/modules/dataset/uvl_examples"
        file_path = os.path.join(directory_path, file_name)

        if not os.path.isfile(file_path):
            raise NotFound(f"File {file_name} not found")

        fm1 = UVLReader(file_path).transform()
        GlencoeWriter(temp_file.name, fm1).transform()
        return temp_file.name  # Retorna la ruta del archivo generado
    except Exception as e:
        raise RuntimeError(f"Error generating Glencoe file: {e}")


def generate_splot_file(file_id):
    temp_file = tempfile.NamedTemporaryFile(suffix='.splx', delete=False)
    try:
        hubfile = HubfileService().get_by_id(file_id)
        file_name = hubfile.name
        directory_path = "app/modules/dataset/uvl_examples"
        file_path = os.path.join(directory_path, file_name)

        if not os.path.isfile(file_path):
            raise NotFound(f"File {file_name} not found")

        fm = UVLReader(file_path).transform()
        SPLOTWriter(temp_file.name, fm).transform()
        return temp_file.name  # Retorna la ruta del archivo generado
    except Exception as e:
        raise RuntimeError(f"Error generating SPLOT file: {e}")


def generate_cnf_file(file_id):
    temp_file = tempfile.NamedTemporaryFile(suffix='.cnf', delete=False)
    try:
        hubfile = HubfileService().get_by_id(file_id)
        file_name = hubfile.name
        directory_path = "app/modules/dataset/uvl_examples"
        file_path = os.path.join(directory_path, file_name)

        if not os.path.isfile(file_path):
            raise NotFound(f"File {file_name} not found")

        fm = UVLReader(file_path).transform()
        sat = FmToPysat(fm).transform()
        DimacsWriter(temp_file.name, sat).transform()
        return temp_file.name  # Retorna la ruta del archivo generado
    except Exception as e:
        raise RuntimeError(f"Error generating DIMACS file: {e}")


def generate_uvl_file(file_id):
    temp_file = tempfile.NamedTemporaryFile(suffix='.uvl', delete=False)
    try:
        hubfile = HubfileService().get_by_id(file_id)
        file_name = hubfile.name
        directory_path = "app/modules/dataset/uvl_examples"
        file_path = os.path.join(directory_path, file_name)

        if not os.path.isfile(file_path):
            raise NotFound(f"File {file_name} not found")

        fm = UVLReader(file_path).transform()
        UVLWriter(temp_file.name, fm).transform()
        return temp_file.name  # Retorna la ruta del archivo generado
    except Exception as e:
        raise RuntimeError(f"Error generating UVL file: {e}")


@dataset_bp.route('/download_all/<int:file_id>')
def download_all_formats(file_id):
    try:
        # Generar los archivos
        uvl_path = generate_uvl_file(file_id)
        glencoe_path = generate_glencoe_file(file_id)
        dimacs_path = generate_cnf_file(file_id)
        splot_path = generate_splot_file(file_id)

        # Crear un archivo ZIP en memoria
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w') as zf:
            zf.write(uvl_path, os.path.basename(uvl_path))
            zf.write(glencoe_path, os.path.basename(glencoe_path))
            zf.write(dimacs_path, os.path.basename(dimacs_path))
            zf.write(splot_path, os.path.basename(splot_path))

        memory_file.seek(0)

        # Eliminar archivos temporales
        os.remove(uvl_path)
        os.remove(glencoe_path)
        os.remove(dimacs_path)
        os.remove(splot_path)

        # Devolver archivo ZIP como respuesta
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"files_{file_id}.zip"
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@dataset_bp.route("/doi/<path:doi>/", methods=["GET"])
def subdomain_index(doi):

    # Check if the DOI is an old DOI
    new_doi = doi_mapping_service.get_new_doi(doi)
    if new_doi:
        # Redirect to the same path with the new DOI
        return redirect(url_for('dataset.subdomain_index', doi=new_doi), code=302)

    # Try to search the dataset by the provided DOI (which should already be the new one)
    ds_meta_data = dsmetadata_service.filter_by_doi(doi)

    if not ds_meta_data:
        abort(404)

    # Get dataset
    dataset = ds_meta_data.data_set

    # Save the cookie to the user's browser
    user_cookie = ds_view_record_service.create_cookie(dataset=dataset)
    resp = make_response(render_template("dataset/view_dataset.html", dataset=dataset))
    resp.set_cookie("view_cookie", user_cookie)

    return resp


@dataset_bp.route("/dataset/unsynchronized/<int:dataset_id>/", methods=["GET"])
@login_required
def get_unsynchronized_dataset(dataset_id):

    # Get dataset
    dataset = dataset_service.get_unsynchronized_dataset(current_user.id, dataset_id)

    if not dataset:
        abort(404)

    return render_template("dataset/view_dataset.html", dataset=dataset)


@dataset_bp.route("/dataset/<int:dataset_id>/", methods=["GET"])
def view_dataset(dataset_id):
    # Obtén el dataset por su ID
    dataset = dataset_service.get_or_404(dataset_id)

    # Renderiza la plantilla con los datos del dataset
    return render_template("dataset/view_dataset.html", dataset=dataset)


@dataset_bp.route('/dataset/<int:dataset_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_dataset(dataset_id):
    # Obtener el dataset a partir de su ID
    dataset = DataSetService().get_by_id(dataset_id)

    # Verificar si el dataset existe
    if dataset is None:
        abort(404)  # Manejo de error si el dataset no existe

    # Verificar si el usuario logueado es el propietario del dataset
    if dataset.user_id != current_user.id:
        abort(403)  # Si el usuario no es el propietario, mostrar un error 403 (Prohibido)

    form = EditDatasetForm()

    if form.validate_on_submit():
        # Asignar valores del formulario al modelo DSMetaData
        dataset.ds_meta_data.title = form.title.data
        dataset.ds_meta_data.description = form.description.data
        dataset.ds_meta_data.publication_type = PublicationType[form.publication_type.data]
        dataset.ds_meta_data.tags = form.tags.data

        # Guardar los cambios en la base de datos
        DataSetService().update(dataset)

        flash("Dataset updated successfully", "success")  # Mensaje de éxito
        return redirect(url_for('dataset.view_dataset', dataset_id=dataset_id))

    # Pre-popular el formulario con los datos existentes del dataset
    form.title.data = dataset.ds_meta_data.description
    form.description.data = dataset.ds_meta_data.description
    form.publication_type.data = dataset.ds_meta_data.publication_type.name
    form.tags.data = dataset.ds_meta_data.tags

    return render_template('dataset/edit_dataset.html', form=form, dataset=dataset)


@dataset_bp.route("/datasets/<int:dataset_id>/rate", methods=["POST"])
@login_required
def rate_dataset(dataset_id):
    try:
        user_id = current_user.id
        rating_value = request.json.get('rating')

        # Validar que el rating esté presente
        if rating_value is None:
            return jsonify({'error': 'Rating is required.'}), 400

        # Intentar añadir o actualizar el rating
        rating = ds_rating_service.add_or_update_rating(dataset_id, user_id, rating_value)
        return jsonify({'message': 'Rating added', 'rating': rating.to_dict()}), 200

    except ValueError as e:
        # Manejar valores inválidos de rating
        return jsonify({'error': str(e)}), 400

    except Exception:
        # Manejar errores inesperados
        return jsonify({'error': 'Rating must be between 1 and 5.'}), 500


@dataset_bp.route('/datasets/<int:dataset_id>/average-rating', methods=['GET'])
@login_required
def get_dataset_average_rating(dataset_id):
    average_rating = ds_rating_service.get_dataset_average_rating(dataset_id)
    return jsonify({'average_rating': average_rating}), 200
