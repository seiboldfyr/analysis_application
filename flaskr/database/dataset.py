from flaskr.database.measurement_models.collection import Collection as MeasurementCollection
from flaskr.framework.abstract.abstract_model import AbstractModel


class Dataset(AbstractModel):
    measurement_collection = None

    def __init__(self, name: str = ''):
        super().__init__()
        # TODO: add as attributes: date, id, initials
        self['name'] = name

    def get_name(self) -> str:
        return self['name']

    def get_well_collection(self) -> MeasurementCollection:
        if self.measurement_collection is None:
            self.measurement_collection = MeasurementCollection()
            self.measurement_collection.add_filter('dataset_id', self.get_id())
        return self.measurement_collection

    def get_well_count(self) -> int:
        """This should be added after the measures are imported"""
        try:
            return self['measure_count']
        except KeyError:
            return -1

