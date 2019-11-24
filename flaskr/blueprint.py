
from flask import render_template, redirect, url_for, request, flash, Blueprint, send_file

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
                                   result={i: dataset_exists[i] for i in dataset_exists if i != '_id'},
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
def process(id, graphs=[]):
    input_form = ExperimentInputForm()
    if request.method == 'POST':
        if id is None:
            flash('No dataset information was found', 'error')
            return redirect(url_for('base.home'))

        # outputPath = WriteMetadata(data=request.form).execute()

        response = Processor(request,
                             dataset_id=id).execute()

        if not response.is_success():
            flash('%s' % response.get_message(), 'error')
            return render_template('processinfo.html', form=input_form, id=id)

        [graphs, zip] = Grapher(dataset_id=id,
                           customtitle=request.form['customlabel']
                         #TODO: include manually changed header here
                           ).execute()

        if len(graphs) > 0:
            # graphs(id, graphs, zip)
            return(render_template('graphs.html', id=id, graphs=graphs, zip=zip))
        else:
            flash('Something went wrong with graphing :(', 'error')

        return render_template('processinfo.html', form=input_form, id=id)

    return render_template('processinfo.html', form=input_form, id=id)


@base_blueprint.route('/graphs/<id>', methods=['GET', 'POST'])
@login_required
def graphs(id, graphs, zip):
    return render_template('graphs.html', id=id, graphs=graphs, zip=zip)


@base_blueprint.route('/runstats', methods=['GET', 'POST'])
@login_required
def runbatch():
    #TODO: batch processing
    #Create graphs and a file of summary stats
    return render_template('stats.html')
