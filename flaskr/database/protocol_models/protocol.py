
from flaskr.framework.abstract.abstract_model import AbstractModel


class Protocol(AbstractModel):

    def __init__(self, measurement_id=None, dataset_id=None, component_id=None, quantity=float):
        super().__init__()
        self['_id'] = None
        self['triplicate_id'] = measurement_id
        self['dataset_id'] = dataset_id
        self['component_id'] = component_id
        self['quantity'] = quantity

    def get_name(self) -> str:
        return self['name']

    def get_type(self) -> str:
        return self['type']

    def get_unit(self) -> str:
        return self['unit']



