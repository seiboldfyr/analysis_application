
from flaskr.database.measurement_models.collection import Collection as MeasurementCollection
from flaskr.database.measurement_models.dataframe_collection import Collection as DataframeCollection
from flaskr.framework.abstract.abstract_model import AbstractModel
from flaskr.database.protocol_models.collection import Collection as ProtocolCollection
from flaskr.components.component_models.collection import Collection as ComponentCollection


class Dataset(AbstractModel):
    measurement_collection = None
    component_collection = None

    def __init__(self):
        super().__init__()
        self['_id'] = None
        self['version'] = 2.0
        self['protocol'] = ''
        self['metadata'] = []
        self['statistics'] = dict()

    def get_protocol(self) -> str:
        return self['protocol']

    def get_metadata(self) -> []:
        return self['metadata']

    def get_stats(self) -> []:
        return self['statistics']

    def get_name(self) -> str:
        return self['name']

    def get_well_collection(self) -> MeasurementCollection:
        if self.measurement_collection is None:
            self.measurement_collection = MeasurementCollection()
            self.measurement_collection.add_filter('dataset_id', self.get_id())
        return self.measurement_collection

    def get_pd_well_collection(self):
        if self.measurement_collection is None:
            self.measurement_collection = DataframeCollection()
            self.measurement_collection.add_filter('dataset_id', self.get_id())
        return self.measurement_collection.to_df()

    def get_component_collection(self) -> ProtocolCollection:
            if self.component_collection is None:
                self.component_collection = ProtocolCollection()
                self.component_collection.add_filter('dataset_id', self.get_id())
                # for item in self.component_collection:
                    # TODO: get component name/unit from componentcollection
            return self.component_collection

    def get_well_count(self) -> int:
        """This should be added after the measures are imported"""
        try:
            return self['measure_count']
        except KeyError:
            return -1

