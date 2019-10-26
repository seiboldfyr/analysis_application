#!/usr/bin/env python
from flask import Flask, render_template, redirect, url_for, request, flash
from forms import DataInputForm, ExperimentInputForm
from model.processor import Processor
from model.opener import OpenFile

import os
from filewriter.metadatawriter import WriteMetadata

# create application
APP = Flask(__name__)

APP.secret_key = b'\xd7^\x9d6j\xde"v\x12\x99r[\xed\xcb\x17\xba'

Version = 'output_v2.1'

# required_extension = ['INFO.xlsx', 'RFU.xlsx']
#
# def required_file(folder):
#     for extension in required_extension:
#         for file in os.listdir(folder):
#             if file.endswith(extension):
#                 break
#         flash(extension + 'file not found in provided location.')
#         return False


def buildGroupInputs(requestinfo):
    groupdetails = {}
    for item in request.form.keys():
        if item.startswith('Group'):
            if groupdetails.get(str(item[-1])) is None:
                groupdetails[str(item[-1])] = {}
            groupdetails[item[-1]][item[:-2]] = request.form[item]
    return groupdetails


def checkFolder(requestdata):
    folder = requestdata.form['folder']
    files = OpenFile(path=folder).execute()
    if files.filepaths is None:
        return redirect(url_for('home'))
    return files


@APP.route('/')
def home():
    return render_template('home.html')


@APP.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        files = checkFolder(request)
        folderurl = request.form['folder'].replace(os.sep, '+')
        return render_template('search.html', result=files.data, folder=folderurl)
    return render_template('home.html')


@APP.route('/manual/<folder>')
def manual(folder):
    input_form = DataInputForm()
    return render_template('manual.html', form=input_form, folder=folder)


@APP.route('/process/<folder>', methods=['GET', 'POST'])
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


if __name__ == '__main__':
    APP.debug = True
    APP.run()
