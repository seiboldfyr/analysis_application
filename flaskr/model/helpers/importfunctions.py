
from flaskr.framework.model.request.response import Response
from flaskr.database.dataset_models.repository import Repository
from flaskr.components.component_models.factory import Factory as ComponentFactory


def edit_RFUs(self, originwell, cut):
    originwell.edit_labels(dict(RFUs=originwell.get_rfus()[cut:]))
    self.measurement_manager.update(originwell)


def get_collection(self):
    dataset_repository = Repository()
    dataset = dataset_repository.get_by_id(self.dataset_id)
    return dataset.get_well_collection()


def get_existing_metadata(self):
    dataset_repository = Repository()
    model = dataset_repository.get_by_id(self.dataset_id)
    self.form = dict(form=dict())
    self.form = model.get_metadata()


def update_metadata(self):
    dataset_repository = Repository()
    model = dataset_repository.get_by_id(self.dataset_id)
    model['metadata'] = self.form
    dataset_repository.save(model)


def save_dataset_component(self, quantity, component_id, triplicate_id):
    data = {'triplicate_id': triplicate_id,
            'dataset_id': self.dataset.get_id(),
            'component_id': component_id,
            'quantity': quantity}
    #TODO: convert all to pM units?
    protocol = self.protocol_factory.create(data)
    self.protocol_manager.add(protocol)


def add_component(self, name, unit):
    # TODO: delete when component library is filled
    factory = ComponentFactory()
    model = factory.create({'type': 'Target', 'name': name, 'unit': unit})
    self.component_repository.save(model)


def search_components(self, name, unit):
    component = self.component_repository.search_by_name_and_unit(name, unit)
    if component is not None:
        return Response(True, component['_id'])
    # TODO: edit case if component is not found in library
    # return Flash('Target does not exist in the component library')
    add_component(self, name=name, unit=unit)
    return self.component_repository.search_by_name_and_unit(name, unit)['_id']
