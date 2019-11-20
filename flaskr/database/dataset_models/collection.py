from flaskr.database.dataset_models.factory import Factory
from flaskr.framework.abstract.abstract_collection import AbstractCollection


class Collection(AbstractCollection):
    name = 'dataset'

    def __init__(self):
        super().__init__(Factory())


