#!/bin/bash
export FLASK_APP=application
export FLASK_ENV=development

flask=$(which python3 -m flask)

if [ -z "$flask" ]; then
    echo "You need flask installed, please see http://flask.pocoo.org"
fi;

python3 -m flask run