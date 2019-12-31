from flaskr.components.component_models.component import Component
from flaskr.framework.abstract.abstract_factory import AbstractFactory


class Factory(AbstractFactory):
    def create(self, data=None) -> Component:
        model = Component()
        if data is not None:
            model.set_data(data)

        return model
