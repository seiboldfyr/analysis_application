#!/usr/bin/env python
from flask import Flask, render_template, redirect, url_for, request, flash
from forms import DataInputForm
from model.processor import Processor
import os

# create application
APP = Flask(__name__)

APP.secret_key = b'\xd7^\x9d6j\xde"v\x12\x99r[\xed\xcb\x17\xba'





required_extension = ['INFO.xlsx', 'RFU.xlsx']

def required_file(folder):
    for extension in required_extension:
        for file in os.listdir(folder):
            if file.endswith(extension):
                break
        flash(extension + 'file not found in provided location.')
        return False


# @APP.route('/getfile', methods=['GET','POST'])
# def getfile():

# @APP.route('/')
# def home():
#     return render_template('home.html')


@APP.route('/', methods=['GET', 'POST'])
def home():
    input_form = DataInputForm()
    if request.method == 'POST':  # and input_form.validate():
        folder = request.form['folder']

        response = Processor(path=folder,
                             cut=request.form['cutlength'],
                             label=request.form['customlabel']
                             ).execute()
        if response.is_success():
            flash('%s' % response.get_message(), 'Processed successfully!')
            return redirect(url_for('home'))
        else:
            flash('%s' % response.get_message(), 'error')
            return redirect(url_for('home'))
    return render_template('home.html', form=input_form)


@APP.route('/fyr/graph/')
def graph():
    return render_template('graph.html')


if __name__ == '__main__':
    APP.debug = True
    APP.run()
