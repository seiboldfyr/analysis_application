
from flaskr.components.component_models.factory import Factory as ComponentFactory
from flaskr.framework.abstract.abstract_collection import AbstractCollection


class Collection(AbstractCollection):
    name = 'component'
    buffer = []

    def __init__(self):
        super().__init__(ComponentFactory())

    def __next__(self):
        if self.cursor is None:
            self.cursor = self.find()
        data = self.cursor.next()
        model = self.factory.create(data)
        return model

