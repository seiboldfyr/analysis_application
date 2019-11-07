#!/usr/bin/env python
import os
import json
from flask import Flask, render_template, redirect, url_for, request, flash
from flaskr.forms import DataInputForm, ExperimentInputForm

from flaskr.model.processor import Processor
from flaskr.model.validators.import_validator import ImportValidator
from flaskr.filewriter.metadatawriter import WriteMetadata


# create application
application = Flask(__name__)

application.secret_key = b'\xd7^\x9d6j\xde"v\x12\x99r[\xed\xcb\x17\xba'

Version = 'output_v2.1'


def buildGroupInputs(requestinfo):
    groupdetails = {}
    for item in requestinfo.keys():
        if item.startswith('Group'):
            if groupdetails.get(str(item[-1])) is None:
                groupdetails[str(item[-1])] = {}
            groupdetails[item[-1]][item[:-2]] = requestinfo[item]
    return groupdetails


def buildSwapInputs(requestinfo):
    swapdetails = {}
    for item in requestinfo.keys():
        if item.startswith('Swap From'):
            if swapdetails.get(requestinfo[item]) is None:
                swapdetails[requestinfo[item]] = {}
            swapdetails[requestinfo[item]]['To'] = requestinfo['Swap To ' + str(item[-1])]
    return swapdetails


@application.route('/')
def home():
    return render_template('home.html')


@application.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        validator = ImportValidator()
        result = validator.execute(request)
        if not result.is_success():
            flash('%s' % result.get_message(), 'error')
            return redirect(url_for('home'))

        folder = request.form['folder']
        basename = os.path.basename(folder)
        fileinfo = {}
        fileinfo['Date'] = basename[:8]
        fileinfo['Id'] = basename[8]
        fileinfo['Initials'] = basename[10:12]

        filedata = {}
        for f in request.files:
            if request.files.get(f).filename.endswith('info.xlsx'):
                filedata['infofile'] = request.files.get(f)
            else:
                filedata['rfufile'] = request.files.get(f)
        json.dumps(dict(date=fileinfo['Date'],
                        id=fileinfo['Id'],
                        initials=fileinfo['Initials'],
                        infofile=filedata['infofile'],
                        rfufile=filedata['rfufile']))
        return render_template('search.html', result=fileinfo, folder = '')
    return render_template('home.html')


@application.route('/manual/<folder>', methods=['GET', 'POST'])
def manual(folder):
    input_form = DataInputForm()
    return render_template('manual.html', form=input_form, folder=folder)


@application.route('/process/<folder>', methods=['GET', 'POST'])
def process(folder):
    input_form = ExperimentInputForm()
    if request.method == 'POST':
        if folder is None:
            flash('error', 'No folder found')
            return render_template('home.html')

        folderpath = folder.replace('+', os.sep)

        outputPath = WriteMetadata(path=folderpath, data=request.form, version=Version).execute()

        cutlength = request.form['cutlength']
        if len(request.form['cutlength']) == 0:
            cutlength = 0

        response = Processor(paths={'input': folderpath, 'output': outputPath},
                             cut=cutlength,
                             label=request.form['customlabel'],
                             swaps=buildSwapInputs(request.form),
                             groupings=buildGroupInputs(request.form),
                             errorwells=request.form['errorwells']
                             ).execute()

        if response.is_success():
            flash('%s' % response.get_message(), 'Processed successfully!')
            return render_template('process.html', form=input_form)
        else:
            flash('%s' % response.get_message(), 'Error processing the file', 'error')
            return render_template('process.html', form=input_form)

    return render_template('process.html', form=input_form)


@application.route('/runstats', methods=['GET', 'POST'])
def runstats():
    #TODO: start at top folder, search all for a v2.1 output
    #get inflections from output and create graphs
    return render_template('stats.html')


if __name__ == '__main__':
    # application.run(port=80)
    # application.run(port=80, debug=True)
    application.run()

