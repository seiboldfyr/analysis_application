import pandas as pd

from flaskr.database.measurement_models.factory import Factory as MeasurementFactory
from flaskr.framework.abstract.abstract_collection import AbstractCollection


class Collection(AbstractCollection):
    name = 'measurement'
    buffer = []

    def __init__(self):
        super().__init__(MeasurementFactory())

    def __next__(self):
        if self.cursor is None:
            self.cursor = self.find()
        data = self.cursor.next()
        model = self.factory.create(data)
        return model



