from flaskr.database.dataset_models.factory import Factory
from flaskr.framework.abstract.abstract_repository import AbstractRepository
from flaskr.framework.exception import NoSuchEntityError


class Repository(AbstractRepository):
    name = 'dataset'
    factory = Factory()

    def get_by_name(self, name: str):
        data = self.get_connection().find_one({'name': name})
        if data is None:
            raise NoSuchEntityError
        model = self.factory.create(data)
        return model
