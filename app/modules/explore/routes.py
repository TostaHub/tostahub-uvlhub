from flask import render_template, request, jsonify
from app.modules.explore import explore_bp
from app.modules.explore.forms import ExploreForm
from app.modules.explore.services import ExploreService


@explore_bp.route('/explore', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        query = request.args.get('query', '')  # Obtener la consulta desde la URL
        form = ExploreForm()
        return render_template('explore/index.html', form=form, query=query)

    if request.method == 'POST':
        criteria = request.get_json()

        # Extrae criterios de filtro individuales
        query_string = criteria.get("query", "")
        sorting = criteria.get("sorting", "newest")
        publication_type = criteria.get("publication_type", "any")

        # Llama al servicio de exploración con los parámetros
        datasets = ExploreService().filter(query_string, sorting, publication_type)
        return jsonify([dataset.to_dict() for dataset in datasets])
