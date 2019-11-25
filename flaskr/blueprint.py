
from flask import render_template, redirect, url_for, request, flash, Blueprint, send_file
import zipfile
import base64
from io import BytesIO

from flaskr.forms import DataInputForm, ExperimentInputForm
from flaskr.auth.blueprint import login_required
from flaskr.database.importprocessor import ImportProcessor, buildname
from flaskr.model.processor import Processor
from flaskr.model.validators.import_validator import ImportValidator
from flaskr.graphing.graphs import Grapher

base_blueprint = Blueprint('base', __name__, template_folder='templates')


@base_blueprint.route('/')
@login_required
def home():
    return render_template('home.html')


@base_blueprint.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    if request.method == 'POST':

        validator = ImportValidator()
        result = validator.execute(request)
        if not result.is_success():
            flash('%s' % result.get_message(), 'error')
            return redirect(url_for('base.home'))

        fileinfo = {}
        for f in request.files:
            [name, fileinfo] = buildname(request.files.get(f).filename)

        processor = ImportProcessor()
        dataset_exists = processor.search(name)
        if dataset_exists is not None:
            flash('A dataset was found.')
            return render_template('search.html',
                                   result={i: dataset_exists[i] for i in dataset_exists if i not in ['_id', 'Name']},
                                   id=dataset_exists['_id'])

        response = processor.execute(request, name)
        if not response.is_success():
            flash(response.get_message(), category='error')

        return render_template('search.html', result=fileinfo, id=response.get_message())
    return redirect(url_for('base.home'))


@base_blueprint.route('/manual/<id>', methods=['GET', 'POST'])
@login_required
def manual(id):
    input_form = DataInputForm()
    return render_template('manual.html', form=input_form, id=id)


@base_blueprint.route('/process/<id>', methods=['GET', 'POST'])
@login_required
def process(id, graphs=None):
    if graphs is None:
        graphs = []
    input_form = ExperimentInputForm()
    if request.method == 'POST':
        if id is None:
            flash('No dataset information was found', 'error')
            return redirect(url_for('base.home'))

        response = Processor(request,
                             dataset_id=id).execute()

        if not response.is_success():
            flash('%s' % response.get_message(), 'error')
            return render_template('processinfo.html', form=input_form, id=id)

        flash('Processed successfully in: %s seconds' % response.get_message(), 'msg')
        return render_template('processinfo.html', form=input_form, id=id, graphed=True)

    return render_template('processinfo.html', form=input_form, id=id)


@base_blueprint.route('/graphs/<id>', methods=['GET', 'POST'])
@login_required
def graphs(id):
    graph_urls = Grapher(dataset_id=id).execute()
    # TODO: include manually changed header here
    if len(graph_urls) == 0:
        flash('Something went wrong with graphing', 'error')
        return render_template('processinfo.html', id=id)
    if request.method == 'POST':
        memory_file = BytesIO()
        with zipfile.ZipFile(memory_file, 'w') as zf:
            for itemtitle in graph_urls.keys():
                data = zipfile.ZipInfo()
                data.filename = itemtitle
                zf.writestr(data, base64.decodebytes(graph_urls[itemtitle].encode('ascii')))
        memory_file.seek(0)
        return send_file(memory_file, attachment_filename='graphs.zip', as_attachment=True)

    return render_template('graphs.html', id=id, graphs=graph_urls.values())


@base_blueprint.route('/runstats', methods=['GET', 'POST'])
@login_required
def runbatch():
    #TODO: batch processing
    #Create graphs and a file of summary stats
    return render_template('stats.html')
