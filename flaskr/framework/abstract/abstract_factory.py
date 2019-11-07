# TODO: Delete

from framework.abstract.abstract_model import AbstractModel
from framework.exception import MethodNotImplemented


class AbstractFactory:
    def create(self, data=None) -> AbstractModel:
        raise MethodNotImplemented
