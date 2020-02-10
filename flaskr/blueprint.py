
from flask import render_template, redirect, url_for, request, flash, Blueprint, \
    send_file, current_app
import zipfile
import pandas as pd
import base64
from io import BytesIO

from flaskr.auth.blueprint import login_required
from flaskr.database.importprocessor import ImportProcessor, buildname
from flaskr.components.component_models.collection import Collection
from flaskr.database.dataset_models.collection import Collection as DatasetCollection
from flaskr.model.processor import Processor
from flaskr.model.validators.import_validator import ImportValidator
from flaskr.graphing.graphs import Grapher
from flaskr.filewriter.writer import Writer

base_blueprint = Blueprint('base', __name__, template_folder='templates')


@base_blueprint.route('/')
@login_required
def home():
    dataset_collection = DatasetCollection()
    return render_template('home.html', datasets=dataset_collection)


@base_blueprint.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    if request.method == 'POST':

        validator = ImportValidator()
        importer = ImportProcessor()

        result = validator.execute(request)
        if result.is_success():
            fileinfo = {}
            for f in request.files:
                [name, fileinfo] = buildname(request.files.get(f).filename)

            valid_dataset = importer.search(name)
            if not valid_dataset:
                if importer.dataset is not None:
                    flash('The data was uploaded with an outdated application version %s, '
                          'inflections will be replaced with those found using version %s.'
                          % (importer.dataset['version'], current_app.config['VERSION']), 'msg')
                response = importer.execute(request, name)
                if not response.is_success():
                    flash(response.get_message(), 'error')
                    return redirect(url_for('base.home'))

        else:
            name = request.form['Select a Dataset']
            valid_dataset = importer.search(name[:12])
            if not valid_dataset:
                flash('The data was uploaded with an outdated application version %s, '
                      'please upload new INFO/RFU files.'
                      % importer.dataset['version'], 'error')
                return redirect(url_for('base.home'))

            fileinfo = dict(Date=name[:8],
                            Id=name[8:9],
                            Initials=name[10:12])

        return render_template('search.html',
                               result=fileinfo,
                               id=importer.dataset['_id'])
    return redirect(url_for('base.home'))

@base_blueprint.route('/input/<id>', methods=['GET', 'POST'])
@login_required
def input(id):
    types = Collection().get_types()
    components = Collection().get_components()
    if request.method == 'POST':
        return analysis(id=id, form=request.form)
    return render_template('inputs.html', id=id, types=types, components=components)


@base_blueprint.route('/analysis/<id>', methods=['GET', 'POST'])
@login_required
def analysis(id, form=dict()):
    response = Processor(form=form,
                         dataset_id=id).execute()
    if not response.is_success():
        flash('%s' % response.get_message(), 'error')
        return render_template('analysis.html', id=id)

    flash('Processed successfully in %s seconds' % response.get_message(), 'timing')
    return render_template('analysis.html', id=id)


@base_blueprint.route('/graphs/<id>', methods=['GET', 'POST'])
@login_required
def graphs(id, features=None):
    if request.method == 'POST':
        features = request.form
    graphs, name = Grapher(dataset_id=id)\
        .execute(features=features)

    if len(graphs) == 0:
        flash('Something went wrong with graphing', 'error')
        return redirect(url_for('base.analysis', id=id))

    if request.form.get('download'):
        [memory_file, zipfilename] = download(id=id, graphs=graphs, name=name)
        return send_file(memory_file, attachment_filename=zipfilename, as_attachment=True)

    return render_template('graphs.html',
                           id=id,
                           graphs=graphs.values(),
                           name=name,
                           features=request.form.to_dict())
# TODO: passing these features as parameters is messy way to mark checkboxes on the post form
# find a better way!


def download(id, graphs, name):
    memory_file = BytesIO()

    with zipfile.ZipFile(memory_file, 'w') as zf:

        for itemtitle in graphs.keys():
            data = zipfile.ZipInfo()
            data.filename = itemtitle
            zf.writestr(data, base64.decodebytes(graphs[itemtitle].encode('ascii')))

        io = BytesIO()
        analysistitle = name + '_output.xlsx'
        excelwriter = pd.ExcelWriter(analysistitle, engine='xlsxwriter')
        excelwriter.book.filename = io
        writer = Writer(excelwriter=excelwriter, dataset_id=id)
        response = writer.writebook()
        if not response.is_success():
            return render_template('analysis.html', id=id)
        excelwriter.save()
        io.seek(0)

        data = zipfile.ZipInfo()
        data.filename = analysistitle
        zf.writestr(data, io.getvalue())

    memory_file.seek(0)
    zipfilename = 'output' + '_' + name + '_v.' + current_app.config['VERSION'] + '.zip'
    return [memory_file, zipfilename]
    # return send_file(memory_file, attachment_filename=zipfilename, as_attachment=True)

