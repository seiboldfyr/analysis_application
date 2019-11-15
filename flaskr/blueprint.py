import os
from flask import render_template, redirect, url_for, request, flash, Blueprint, current_app
from forms import DataInputForm, ExperimentInputForm

from flaskr.database.importprocessor import ImportProcessor
from flaskr.model.processor import Processor
from flaskr.model.validators.import_validator import ImportValidator
from flaskr.filewriter.metadatawriter import WriteMetadata
from flaskr.model.graphs import Grapher

base_blueprint = Blueprint('', __name__)


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

        folder = request.form['folder']
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

        return render_template('search.html', result=fileinfo, folder=folder.replace(os.sep, '+'),
                               id=response.get_message())

    return render_template('home.html')


@base_blueprint.route('/manual/<folder>/<id>', methods=['GET', 'POST'])
def manual(folder, id):
    input_form = DataInputForm()
    return render_template('manual.html', form=input_form, folder=folder, id=id)


@base_blueprint.route('/process/<folder>/<id>', methods=['GET', 'POST'])
#TODO: pass folder and info as json
def process(folder, id):
    input_form = ExperimentInputForm()
    if request.method == 'POST':
        if folder is None:
            flash('error', 'No corrected information was found')
            return render_template('home.html')

        folderpath = folder.replace('+', os.sep)

        # outputPath = WriteMetadata(path=folderpath, data=request.form).execute()

        response = Processor(request,
                             dataset_id=id).execute()

        if not response.is_success():
            flash('%s' % response.get_message(), 'error')
            return render_template('process.html', form=input_form)
        flash('Processed successfully')

        response = Grapher(dataset_id=id,
                           path=folder,
                           customtitle=request.form['customlabel']#TODO: include manually changed header here
                           ).execute()
        if not response.is_success():
            flash('%s' % response.get_message(), 'error')
            return render_template('process.html', form=input_form)

        flash('%s' % response.get_message(), 'success')
        return render_template('process.html', form=input_form)

    return render_template('process.html', form=input_form)


@base_blueprint.route('/runstats', methods=['GET', 'POST'])
def runbatch():
    #TODO: start at top folder, search all for valid data files
    #get inflections from output and create graphs
    return render_template('stats.html')

