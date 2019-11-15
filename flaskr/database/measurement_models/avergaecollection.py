import numpy as np

from flaskr.database.measurement_models.factory import Factory as MeasurementFactory
from flaskr.framework.abstract.abstract_collection import AbstractCollection


class Collection(AbstractCollection):
    name = 'measurement'
    idxgroup = 0
    idxsample = 0
    idxtriplicate = 0

    def __init__(self):
        super().__init__(MeasurementFactory())

    def __next__(self):
        if self.cursor is None:
            self.cursor = self.find()
        data = self.cursor.next()
        model = self.factory.create(data) #first item in triplicate
        self.idxgroup = model.get_data()
        return model

    def average(self, item):
        return np.nanmean(item)

