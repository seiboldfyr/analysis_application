
from flaskr.database.protocol_models.factory import Factory as ProtocolFactory
from flaskr.framework.abstract.abstract_collection import AbstractCollection


class Collection(AbstractCollection):
    name = 'protocol'
    buffer = []

    def __init__(self):
        super().__init__(ProtocolFactory())

    def __next__(self):
        if self.cursor is None:
            self.cursor = self.find()
        data = self.cursor.next()
        model = self.factory.create(data)
        return model




