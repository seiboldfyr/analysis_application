import datetime
from bson import ObjectId
import time
import numpy

from flask import flash, current_app

from flaskr.database.dataset_models.factory import Factory
from flaskr.database.dataset_models.repository import Repository
from flaskr.database.measurement_models.factory import Factory as MeasurementFactory
from flaskr.database.measurement_models.manager import Manager as MeasurementManager
from flaskr.framework.abstract.abstract_importer import AbstractImporter
from flaskr.framework.exception import InvalidArgument
from flaskr.framework.model.Io.xlsx_file import XLSXFile
from flaskr.framework.model.request.response import Response


def buildname(info):
    return info['Date'] + info['Id'] + '_' + info['Initials']

def buildid(info):
    infoID = info['Date'] + info['Id'] + info['Initials'] + str(current_app.config['VERSION'].strip('.')) + '1212121212'
    return ObjectId(infoID.encode())

def getseconds(t):
    time = datetime.datetime.strptime(t[:-4], '%m/%d/%Y %H:%M:%S')
    return time.second + time.minute * 60 + time.hour * 3600


class ImportProcessor(AbstractImporter):
    def __init__(self):
        self.identifers = dict(group=1, sample=0, triplicate=0, previous='')
        self.experimentlength = 0

    def execute(self, request, info) -> Response:
        dataset_repository = Repository()
        factory = Factory()
        model = factory.create()
        found_dataset = dataset_repository.get_connection().find_one({'name': buildname(info)})
        if found_dataset is None:
            model = factory.create({'name': buildname(info)})
        else:
            model = factory.create({'_id': found_dataset['_id'],
                                    'name': buildname(info)})
        dataset_repository.save(model)
        self.dataset = model
        self.measurement_factory = MeasurementFactory()
        self.measurement_manager = MeasurementManager()

        infofile = None
        rfufile = None

        for f in request.files:
            file = request.files.get(f)
            try:
                xlsx_file = XLSXFile(file)
            except InvalidArgument:
                dataset_repository.delete(self.dataset)
                return Response(False, 'An invalid file was provided, please make sure you are uploading a .txt file')

            if file.filename.endswith('INFO.xlsx'):
                infofile = xlsx_file
            elif file.filename.endswith('RFU.xlsx'):
                rfufile = xlsx_file

        self.getexperimentlength(infofile)
        for info, rfu in zip(infofile.read(sheet='0', userows=True), rfufile.read(sheet='SYBR', usecolumns=True)):
            self.add_measurement(info, rfu)

            self.measurement_manager.save()

        # TODO: remove files after reading
        # xlsx_file.delete()
        # infofile.delete()
        # rfufile.delete()

        model['measure_count'] = model.get_well_collection().get_size()
        dataset_repository.save(model)

        flash('File imported successfully.')
        return Response(
            True,
            self.dataset.get_id()
        )

    def getexperimentlength(self, info):
        start = 0
        for row in info.read(sheet='Run Information', userows=True):
            if row[0] == 'Run Ended':
                self.experimentlength = getseconds(row[1])
            elif row[0] == 'Run Started':
                start = getseconds(row[1])
        self.experimentlength -= start

    def iterateidentifiers(self, label):
        if self.identifers['previous'] == '':
            self.identifers['control'] = label

        if self.identifers['previous'] != label:
            self.identifers['sample'] += 1
            self.identifers['triplicate'] += 1

            if label == self.identifers['control'] and self.identifers['triplicate'] > 1:
                self.identifers['group'] += 1
                self.identifers['sample'] = 1

        self.identifers['previous'] = label

    def add_measurement(self, inforow, rfuvalues):
        self.iterateidentifiers(inforow[5] + '_' + inforow[6])

        data = {'dataset_id': self.dataset.get_id(),
                'excelheader': inforow[1],
                'label': inforow[5] + '_' + inforow[6],
                'group': self.identifers['group'],
                'sample': self.identifers['sample'],
                'triplicate': self.identifers['triplicate'],
                'cycle': self.experimentlength/len(rfuvalues),
                'RFUs': []
                }

        measurement_model = self.measurement_factory.create(data)
        measurement_model.add_values(rfuvalues)

        self.measurement_manager.add(measurement_model)
