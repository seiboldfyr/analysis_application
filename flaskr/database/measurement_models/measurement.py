from flaskr.framework.exception import MissingMeasures
from flaskr.framework.abstract.abstract_model import AbstractModel
from flaskr.database.protocol_models.collection import Collection as ProtocolCollection
from flaskr.components.component_models.collection import Collection as ComponentCollection



class Measurement(AbstractModel):
    component_collection = None

    def __init__(self, dataset_id=None, excelheader='', label='', concentration=str, group=float, sample=float,
                 triplicate=float, triplicate_id=None, RFUs=None):
        super().__init__()
        if RFUs is None:
            RFUs = []
        self['dataset_id'] = dataset_id
        self['excelheader'] = excelheader
        self['is_valid'] = True
        self['concentration'] = concentration
        self['label'] = label
        self['group'] = group
        self['sample'] = sample
        self['triplicate'] = triplicate
        self['triplicate_id'] = triplicate_id
        self['RFUs'] = RFUs
        self['inflections'] = []
        self['inflectionRFUs'] = []
        self['percentdiffs'] = [0 for x in range(4)]
        self['deltaCt'] = [0 for x in range(3)]

    def edit_labels(self, labels: dict = None):
        for key in labels.keys():
            if self[key] is not None:
                self[key] = labels[key]

    def add_values(self, measures: dict = None):
        if measures is None:
            raise MissingMeasures('At least one measure is required')

        for value in measures:
            self['RFUs'].append(value)

    def is_valid(self) -> bool:
        return self['is_valid']

    def has_output(self) -> bool:
        if len(self['inflections']) == 0:
            return False
        return True

    def get_excelheader(self) -> '':
        return self['excelheader']

    def get_cycle(self) -> float:
        return self['cycle']

    def get_label(self) -> '':
        return self['label']

    def get_concentration(self) -> str:
        return self['concentration']

    def get_group(self) -> int:
        return self['group']

    def get_sample(self) -> int:
        return self['sample']

    def get_triplicate(self) -> int:
        return self['triplicate']

    def get_inflections(self) -> list:
        return self['inflections']

    def get_inflectionrfus(self) -> list:
        return self['inflectionRFUs']

    def get_delta_ct(self) -> float:
        return self['deltaCt'][0]

    def get_ct_threshold(self) -> float:
        return self['deltaCt'][1]

    def get_percentdiffs(self) -> list:
        return self['percentdiffs']

    def get_rfus(self) -> list:
        return self['RFUs']

    def get_component_collection(self) -> ProtocolCollection:
            if self.component_collection is None:
                self.component_collection = ProtocolCollection()
                self.component_collection.add_filter('triplicate_id', self['triplicate_id'])
                # for item in self.component_collection:
                    # TODO: get component name/unit from componentcollection
            return self.component_collection
