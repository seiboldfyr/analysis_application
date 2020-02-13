import datetime
import re
from bson import ObjectId

from flask import flash, current_app

from flaskr.database.dataset_models.factory import Factory
from flaskr.database.dataset_models.repository import Repository
from flaskr.components.component_models.repository import Repository as ComponentRepository
from flaskr.components.component_models.factory import Factory as ComponentFactory
from flaskr.database.protocol_models.factory import Factory as ProtocolFactory
from flaskr.database.protocol_models.manager import Manager as ProtocolManager
from flaskr.database.measurement_models.factory import Factory as MeasurementFactory
from flaskr.database.measurement_models.manager import Manager as MeasurementManager
from flaskr.framework.abstract.abstract_importer import AbstractImporter
from flaskr.framework.exception import InvalidArgument
from flaskr.framework.model.Io.xlsx_file import XLSXFile
from flaskr.framework.model.request.response import Response
from flaskr.model.helpers.calcfunctions import reg_conc
from flaskr.model.helpers.importfunctions import save_dataset_component


def buildname(excelfilename):
    filename = excelfilename.split('_')
    info = dict(Date=filename[0][:-1],
                Id=filename[0][-1],
                Initials=filename[1])
    if len(excelfilename) > 4:
        info['Other Info'] = filename[2:-1][0]
    return [info['Date'] + info['Id'] + '_' + info['Initials'], info]


def getTime(t):
    time = datetime.datetime.strptime(t[:-4], '%m/%d/%Y %H:%M:%S')
    return time


class ImportProcessor(AbstractImporter):
    def __init__(self, id=None):
        self.identifers = dict(group=0, sample=-1, triplicate=-1, triplicate_id=None, previous='')
        self.experimentlength = 0
        self.cyclelength = 0
        self.dataset = None
        self.dataset_id = id
        self.component_repository = ComponentRepository()
        self.protocol_factory = ProtocolFactory()
        self.protocol_manager = ProtocolManager()

    def search(self, name) -> {}:
        dataset_repository = Repository()
        found_dataset = dataset_repository.get_by_name(name)
        if found_dataset is not None:
            self.dataset = found_dataset
            self.dataset_id = self.dataset.get_id()
            return True
        return False

    def execute(self, request, name) -> Response:
        self.measurement_factory = MeasurementFactory()
        self.measurement_manager = MeasurementManager()

        dataset_repository = Repository()
        if self.dataset is None:
            factory = Factory()
            model = factory.create({'name': name})
            dataset_repository.save(model)
            self.dataset = model

        infofile = None
        rfufile = None

        for f in request.files:
            file = request.files.get(f)
            try:
                xlsx_file = XLSXFile(file)
            except InvalidArgument:
                dataset_repository.delete(self.dataset)
                return Response(False, 'An invalid file was provided, please make sure you are uploading a .xlsx file')

            if file.filename.endswith('INFO.xlsx'):
                infofile = xlsx_file
            elif file.filename.endswith('RFU.xlsx'):
                rfufile = xlsx_file
                name = buildname(file.filename)

        self.getexperimentlength(infofile)
        for info, rfu in zip(infofile.read(sheet='0', userows=True), rfufile.read(sheet='SYBR', usecolumns=True)):
            self.add_measurement(info, rfu)

            self.measurement_manager.save()

        infofile.delete()
        rfufile.delete()

        self.dataset['measure_count'] = self.dataset.get_well_collection().get_size()
        self.dataset['version'] = float(current_app.config['VERSION'])
        dataset_repository.save(self.dataset)

        flash('File imported successfully', 'success')
        flash('Calculated cycle length was %s' % round(self.cyclelength, 3), 'success')

        return Response(
            True,
            self.dataset_id
        )

    def getexperimentlength(self, info):
        start = 0
        end = 0
        for row in info.read(sheet='Run Information', userows=True):
            if row[0] == 'Run Ended':
                end = getTime(row[1])
            if row[0] == 'Run Started':
                start = getTime(row[1])
        if start == 0 or end == 0:
            current_app.logger.error("Error retrieving experiment length")
        self.experimentlength = (end-start).total_seconds()

    def iterateidentifiers(self, label):
        if self.identifers['previous'] == '':
            self.identifers['control'] = label[:12]

        if self.identifers['previous'] != label:
            self.identifers['sample'] += 1
            self.identifers['triplicate'] += 1
            self.identifers['triplicate_id'] = ObjectId()
            search_components = self.validate_target(label)
            if search_components.is_success():
                self.add_target(label=label,
                                component_id=search_components.get_message(),
                                triplicate_id=self.identifers['triplicate_id'])

            # TODO: check if control is labeled with '_0'
            if label[:12] == self.identifers['control']:
                self.identifers['group'] += 1
                self.identifers['sample'] = 0

        self.identifers['previous'] = label

    def validate_target(self, target):
        if re.match(r'^\d+\s*[a-z]+\/*[a-zA-Z]+?\s+\w?', target) is not None:
            quantityRe = re.match(r'^\d+', target)
            unitRe = reg_conc(target)
            if quantityRe is None or unitRe is None:
                Response(False, 'Target units and name could not be identified')
            name = target[unitRe.end():]
            unit = target[quantityRe.end():unitRe.end()]

            component = self.component_repository.search_by_name_and_unit(name, unit)
            if component is not None:
                return Response(True, component['_id'])
            # TODO: edit case if component is not found in library
            # return Response(False, 'Target does not exist in the component library')
            self.add_component(name=name, unit=unit)
        return Response(False, 'Target units and name could not be identified')

    def add_component(self, name, unit):
        # TODO: delete when component library is filled
        factory = ComponentFactory()
        model = factory.create({'type': 'Target', 'name': name, 'unit': unit})
        self.component_repository.save(model)

    def add_target(self, label, component_id, triplicate_id):
        quantity = re.match(r'^\d+', label).group(0)
        save_dataset_component(self, quantity, component_id, triplicate_id)

    def add_measurement(self, inforow, rfuvalues):
        self.iterateidentifiers(str(inforow[5]) + '_' + str(inforow[6]))
        self.cyclelength = self.experimentlength/len(rfuvalues)

        concentration = 'unknown'
        if reg_conc(inforow[5]):
            concentration = reg_conc(inforow[5]).group(0)

        data = {'dataset_id': self.dataset.get_id(),
                'triplicate_id': self.identifers['triplicate_id'],
                'excelheader': inforow[1],
                'cycle': self.cyclelength,
                'label': inforow[5] + '_' + inforow[6],
                'concentration': concentration,
                'group': self.identifers['group'],
                'sample': self.identifers['sample'],
                'triplicate': self.identifers['triplicate'],
                'RFUs': []
                }

        measurement_model = self.measurement_factory.create(data)
        measurement_model.add_values(rfuvalues)

        self.measurement_manager.add(measurement_model)

