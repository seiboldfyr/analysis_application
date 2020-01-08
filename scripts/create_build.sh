#!/usr/bin/env bash
# for chars in the random string generator
LC_ALL=C

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." >/dev/null 2>&1 && pwd )"
CONFIG_DIR=$DIR/flaskr
CONFIG_DIST_FILE="config.dist"
CONFIG_FILE="config.py"

# create the config file
RANDOM_STRING=$(openssl rand -base64 12 | sed 's/\\/-/')
touch ${CONFIG_DIR}/${CONFIG_FILE}
sed "s/{{random}}/$RANDOM_STRING/" ${CONFIG_DIR}/${CONFIG_DIST_FILE} > ${CONFIG_DIR}/${CONFIG_FILE}

# clean up pycache
find $DIR -depth -name '__pycache__' -exec rm -rf {} \;

# create the zip file to be deployed
cd $DIR
zip $DIR/../app.zip -r * .[^.]* -x .git\* node_modules\*

# remove the config file
rm $DIR/flaskr/config.py
