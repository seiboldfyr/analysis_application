
from flask import render_template, redirect, url_for, request, flash, Blueprint, \
    send_file, current_app
import zipfile
import pandas as pd
import base64
from io import BytesIO

from flaskr.auth.blueprint import login_required
from flaskr.database.importprocessor import ImportProcessor, buildname
from flaskr.model.processor import Processor
from flaskr.model.validators.import_validator import ImportValidator
from flaskr.graphing.graphs import Grapher
from flaskr.filewriter.writer import Writer

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
            print(name)

        processor = ImportProcessor()
        dataset_exists = processor.search(name)
        if dataset_exists is not None:
            flash('A dataset was found.', 'success')
            fileinfo['Version'] = dataset_exists['version']
            #TODO: get components and list on search screen
            return render_template('search.html',
                                   result=fileinfo,
                                   id=dataset_exists['_id'])

        response = processor.execute(request, name)
        if not response.is_success():
            flash(response.get_message(), 'error')
            #TODO: get components and list on search screen

        return render_template('search.html',
                               result=fileinfo,
                               id=response.get_message())
    return redirect(url_for('base.home'))


@base_blueprint.route('/process/<id>', methods=['GET', 'POST'])
@login_required
def process(id):
    if request.method == 'POST':
        if id is None:
            flash('No dataset information was found', 'error')
            return redirect(url_for('base.home'))

        response = Processor(request,
                             dataset_id=id).execute()
        if not response.is_success():
            flash('%s' % response.get_message(), 'error')
            return render_template('processinfo.html', id=id)

        flash('Processed successfully in %s seconds' % response.get_message(), 'timing')
        return render_template('processinfo.html', id=id, graphed=True)

    return render_template('processinfo.html', id=id)


@base_blueprint.route('/graphs/<id>', methods=['GET', 'POST'])
@login_required
def graphs(id):
    graphs, name = Grapher(dataset_id=id).execute()

    # TODO: include manually changed header here
    if len(graphs) == 0:
        flash('Something went wrong with graphing', 'error')
        return render_template('processinfo.html', id=id)

    if request.method == 'POST':
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
                return render_template('processinfo.html', id=id)
            excelwriter.save()
            io.seek(0)

            data = zipfile.ZipInfo()
            data.filename = analysistitle
            zf.writestr(data, io.getvalue())

        memory_file.seek(0)
        zipfilename = 'output' + '_' + name + '_v.' + current_app['VERSION'] + '.zip'
        return send_file(memory_file, attachment_filename=zipfilename, as_attachment=True)

    return render_template('graphs.html', id=id, graphs=graphs.values(), name=name)


