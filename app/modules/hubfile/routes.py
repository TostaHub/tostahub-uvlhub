from datetime import datetime, timezone
import os
import uuid
from flask import current_app, jsonify, make_response, request, send_from_directory,Blueprint
from flask_login import current_user
from app.modules.hubfile import hubfile_bp
from app.modules.hubfile.models import HubfileDownloadRecord, HubfileViewRecord
from app.modules.hubfile.services import HubfileDownloadRecordService, HubfileService
from flask import abort, send_from_directory
from app import db


from flask import jsonify, current_app
import traceback


@hubfile_bp.route("/file/download/<int:file_id>", methods=["GET"])
def download_file(file_id):
    try:
        # Intentamos obtener el archivo del servicio
        file = HubfileService().get_or_404(file_id)  
        # Configuración de la ruta de descarga
        filename = file.name
        directory_path = "app/modules/dataset/uvl_examples/"
        parent_directory_path = os.path.dirname(current_app.root_path)
        file_path = os.path.join(parent_directory_path, directory_path)

        
        # Si el archivo existe, proceder con el proceso de descarga
        user_cookie = request.cookies.get("file_download_cookie", str(uuid.uuid4()))
        existing_record = HubfileDownloadRecord.query.filter_by(
            user_id=current_user.id if current_user.is_authenticated else None,
            file_id=file_id,
            download_cookie=user_cookie
        ).first()

        if not existing_record:
            HubfileDownloadRecordService().create(
                user_id=current_user.id if current_user.is_authenticated else None,
                file_id=file_id,
                download_date=datetime.now(timezone.utc),
                download_cookie=user_cookie,
            )

        resp = make_response(
            send_from_directory(directory=file_path, path=filename, as_attachment=True)
        )
        resp.set_cookie("file_download_cookie", user_cookie)
        return resp

    except Exception as e:
        # Si ocurre un error, capturamos la excepción y devolvemos 500
        current_app.logger.error(f"Error inesperado al intentar descargar el archivo: {e}")
        current_app.logger.error(traceback.format_exc())  # Esto imprime el traceback completo para mayor claridad
        return jsonify({
            "error": "An unexpected error occurred",
            "message": str(e)
        }), 500



    


@hubfile_bp.route('/file/view/<int:file_id>', methods=['GET'])
def view_file(file_id):
    file = HubfileService().get_or_404(file_id)
    filename = file.name

    directory_path = f"uploads/user_{file.feature_model.data_set.user_id}/dataset_{file.feature_model.data_set_id}/"
    parent_directory_path = os.path.dirname(current_app.root_path)
    file_path = os.path.join(parent_directory_path, directory_path, filename)

    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()

            user_cookie = request.cookies.get('view_cookie')
            if not user_cookie:
                user_cookie = str(uuid.uuid4())

            # Check if the view record already exists for this cookie
            existing_record = HubfileViewRecord.query.filter_by(
                user_id=current_user.id if current_user.is_authenticated else None,
                file_id=file_id,
                view_cookie=user_cookie
            ).first()

            if not existing_record:
                # Register file view
                new_view_record = HubfileViewRecord(
                    user_id=current_user.id if current_user.is_authenticated else None,
                    file_id=file_id,
                    view_date=datetime.now(),
                    view_cookie=user_cookie
                )
                db.session.add(new_view_record)
                db.session.commit()

            # Prepare response
            response = jsonify({'success': True, 'content': content})
            if not request.cookies.get('view_cookie'):
                response = make_response(response)
                response.set_cookie('view_cookie', user_cookie, max_age=60*60*24*365*2)

            return response
        else:
            return jsonify({'success': False, 'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
