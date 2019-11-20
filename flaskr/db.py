import pymongo
import click
from flask import current_app, g
from flask.cli import with_appcontext


def get_db():
    if 'db' not in g:
        g.db = pymongo.MongoClient(current_app.config['DB_HOST'],
                                   int(current_app.config['DB_PORT'])
                                   )[current_app.config['DB_NAME']]

    return g.db


def init_db():
    get_db()

@click.command('init-db')
@with_appcontext
def init_db_command():
    init_db()
    click.echo('Connected to mongo')


def init_app(app):
    app.cli.add_command(init_db_command)
