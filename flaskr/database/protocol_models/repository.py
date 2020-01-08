from flaskr.database.protocol_models.factory import Factory
from flaskr.framework.abstract.abstract_repository import AbstractRepository


class Repository(AbstractRepository):
    name = 'protocol'
    factory = Factory()

