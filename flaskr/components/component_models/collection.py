
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

    def get_types(self):
        types = []
        for item in self:
            if item['type'] not in types:
                types.append(item['type'])

        return types

    def get_components(self):
        components = dict()
        for item in self:
            if not components.get(item['type']):
                components[item['type']] = []
            components[item['type']].append(item['name'])
        return components



