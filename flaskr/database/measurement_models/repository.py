from flaskr.database.dataset import Dataset
from flaskr.database.measurement_models.factory import Factory
from flaskr.framework.abstract.abstract_repository import AbstractRepository


class Repository(AbstractRepository):
    name = 'measurement'
    factory = Factory()

    def delete_by_dataset(self, dataset: Dataset):
        if dataset.get_id() is None:
            return
        self.delete_by_filter({'dataset_id': dataset.get_id()})
