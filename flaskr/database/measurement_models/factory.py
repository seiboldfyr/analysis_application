from flaskr.database.measurement_models.measurement import Measurement
from flaskr.framework.abstract.abstract_factory import AbstractFactory


class Factory(AbstractFactory):
    def create(self, data=None) -> Measurement:
        model = Measurement()
        if data is not None:
            model.set_data(data)

        return model
