
from flaskr.framework.abstract.abstract_model import AbstractModel


class Component(AbstractModel):
    component_collection = None

    def __init__(self):
        super().__init__()
        self['_id'] = None
        self['type'] = ''
        self['name'] = ''
        self['unit'] = ''
        self['base_protocol'] = 0

    def get_name(self) -> str:
        return self['name']

    def get_type(self) -> str:
        return self['type']

    def get_unit(self) -> str:
        return self['unit']
