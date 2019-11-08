import pytest

from flaskr import create_app
from flaskr import db


@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
        'DB_NAME': 'test_fyr_app'
    })

    with app.app_context():
        db.init_db()

    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()
