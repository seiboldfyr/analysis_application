import os

from flask import render_template, redirect, url_for, current_app, request, flash, Blueprint, send_from_directory
from forms import DataInputForm, ExperimentInputForm

from flaskr.database.importprocessor import ImportProcessor
from flaskr.model.processor import Processor
from flaskr.model.validators.import_validator import ImportValidator
from flaskr.graphing.graphs import Grapher

base_blueprint = Blueprint('', __name__, template_folder='templates')


@base_blueprint.route('/')
def home():
    return render_template('home.html')


@base_blueprint.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':

        validator = ImportValidator()
        result = validator.execute(request)
        if not result.is_success():
            flash('%s' % result.get_message(), 'error')
            return redirect(url_for('home'))

        filedata = {}
        fileinfo = {}
        for f in request.files:
            if request.files.get(f).filename.endswith('INFO.xlsx'):
                filedata['infofile'] = request.files.get(f)
            else:
                filedata['rfufile'] = request.files.get(f)
                fileinfo['Date'] = filedata['rfufile'].filename[:8]
                fileinfo['Id'] = filedata['rfufile'].filename[8]
                fileinfo['Initials'] = filedata['rfufile'].filename[10:12]

        processor = ImportProcessor()
        response = processor.execute(request, fileinfo)
        if not response.is_success():
            flash('Error processing the data file')

        return render_template('search.html', result=fileinfo, id=response.get_message())

    return render_template('home.html')


@base_blueprint.route('/manual/<id>', methods=['GET', 'POST'])
def manual( id):
    input_form = DataInputForm()
    return render_template('manual.html', form=input_form, id=id)


@base_blueprint.route('/process/<id>', methods=['GET', 'POST'])
def process(id):
    input_form = ExperimentInputForm()
    if request.method == 'POST':
        if id is None:
            flash('error', 'Error. No dataset information was found')
            return render_template('home.html')

        # outputPath = WriteMetadata(data=request.form).execute()

        response = Processor(request,
                             dataset_id=id).execute()

        if not response.is_success():
            flash('%s' % response.get_message(), 'error')
            return render_template('process.html', form=input_form, id=id)
        flash('Processed successfully')

        response = Grapher(dataset_id=id,
                           customtitle=request.form['customlabel']#TODO: include manually changed header here
                           ).execute()
        if not response.is_success():
            flash('%s' % response.get_message(), 'error')
            return render_template('process.html', form=input_form, id=id)

        flash('%s' % response.get_message(), 'success')
        return render_template('process.html', form=input_form, id=id)

    return render_template('process.html', form=input_form, id=id)


@base_blueprint.route('/graphs/<id>', methods=['GET', 'POST'])
def graphs(id):
    path = os.path.join(current_app.config['IMAGE_FOLDER'], 'graphs')
    graphs = [os.path.sep + os.path.join("static", "images", "graphs", item) for item in os.listdir(path)]
    return render_template('graphs.html', id=id, graphs=graphs)


@base_blueprint.route('/runstats', methods=['GET', 'POST'])
def runbatch():
    #TODO: batch processing
    #Create graphs and a file of summary stats
    return render_template('stats.html')
