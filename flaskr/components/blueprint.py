
from flaskr.auth.blueprint import login_required
from flask import render_template, request, flash, Blueprint
from flaskr.components.componentprocessor import ImportComponents

comp_blueprint = Blueprint('comp', __name__, template_folder='templates', url_prefix='/components')


@comp_blueprint.route('', methods=['GET', 'POST'])
@login_required
def import_components():
    if request.method == 'POST':
        importer = ImportComponents()
        response = importer.execute(request)
        if not response.is_success():
            flash(response.get_message(), 'error')
        flash(response.get_message(), 'success')
    return render_template('componentimport.html')
