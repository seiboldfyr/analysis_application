from flaskr.database.dataset_models.factory import Factory
from flaskr.framework.abstract.abstract_repository import AbstractRepository


class Repository(AbstractRepository):
    name = 'dataset'
    factory = Factory()

    def get_by_name(self, name: str):
        data = self.get_connection().find_one({'name': name})
        if data is None:
            return None
        model = self.factory.create(data)
        return model

    def get_empty(self, name: str):
        data = self.get_connection().find({'measurement_count': 0})
        emptydataset = None
        if data is not None:
            for dataset in data:
                if dataset.get_name().startswith(name[:8]):
                    emptydataset = data
                    break
                emptydataset = dataset

        model = self.factory.create(emptydataset)
        return model
