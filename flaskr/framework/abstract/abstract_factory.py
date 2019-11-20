from flaskr.framework.abstract.abstract_model import AbstractModel
from flaskr.framework.exception import MethodNotImplemented


class AbstractFactory:
    def create(self, data=None) -> AbstractModel:
        raise MethodNotImplemented
