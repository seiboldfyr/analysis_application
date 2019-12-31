
from flaskr.database.protocol_models.protocol import Protocol
from flaskr.framework.abstract.abstract_factory import AbstractFactory


class Factory(AbstractFactory):
    def create(self, data=None) -> Protocol:
        model = Protocol()
        if data is not None:
            model.set_data(data)

        return model
