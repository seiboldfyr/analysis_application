from flaskr.database.dataset import Dataset
from flaskr.framework.abstract.abstract_factory import AbstractFactory


class Factory(AbstractFactory):
    def create(self, data=None) -> Dataset:
        model = Dataset()
        if data is not None:
            model.set_data(data)
        return model
