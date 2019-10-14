#!/bin/bash
export FLASK_APP=flaskstart
export FLASK_ENV=development

flask=$(which flask)

if [ -z "$flask" ]; then
    echo "You need flask installed, please see http://flask.pocoo.org"
fi;

flask run