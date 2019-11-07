"""This file serves as a boostrap for the framework initialization"""
import click
from flask import g
from flask.cli import with_appcontext


# setup globals
# nav items
def get_nav_items():
    """This will work as a place to include navigation menu items"""
    if 'nav_items' not in g:
        g.nav_items = []
    return g.nav_items


@click.command('init-nav')
@with_appcontext
def init_nav():
    get_nav_items()


def init_framework(app):
    app.cli.add_command(init_nav)
