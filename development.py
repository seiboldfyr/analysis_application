#!/usr/bin/env python
from flask import Flask, render_template, redirect, url_for, request
from forms import DataInputForm
from model.processor import processdata

# create application
APP = Flask(__name__)

APP.secret_key = b'\xd7^\x9d6j\xde"v\x12\x99r[\xed\xcb\x17\xba'


def calculatecycles(length: int, totaldata: int) -> int:
    return length/totaldata


@APP.route('/fyr/')
def home():
    return render_template('home.html')


@APP.route('/fyr/process', methods=['GET', 'POST'])
def process():
    input_form = DataInputForm()
    if request.method == 'POST':  # and input_form.validate():
        cycles = request.form['cyclelength']
        if cycles is None:
            cycles = calculatecycles(request.form['length'], request.form['totaldata'])

        # TODO: find a way to take in the folder path
        folder = '/Users/KnownWilderness/2019/Coding/Fyr'

        processeddata = processdata(folder, cycles, request.form['cutlength'])
        # (processeddata)
        # graphs(inflections,request.files['fileupload'])
        if processeddata is True:
            return redirect(url_for('success', message='Success!'))
        else:
            return redirect(url_for('success', message='Failed.'))
    return render_template('home.html', form=input_form)



@APP.route('/fyr/graph/')
def graph():
    return render_template('graph.html')


if __name__ == '__main__':
    APP.debug = True
    APP.run()
