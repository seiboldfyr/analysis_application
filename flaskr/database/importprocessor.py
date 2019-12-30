import datetime

from flask import flash, current_app

from flaskr.database.dataset_models.factory import Factory
from flaskr.database.dataset_models.repository import Repository
from flaskr.database.measurement_models.factory import Factory as MeasurementFactory
from flaskr.database.measurement_models.manager import Manager as MeasurementManager
from flaskr.framework.abstract.abstract_importer import AbstractImporter
from flaskr.framework.exception import InvalidArgument
from flaskr.framework.model.Io.xlsx_file import XLSXFile
from flaskr.framework.model.request.response import Response


def buildname(excelfilename):
    filename = excelfilename.split('_')
    info = {}
    info['Date'] = filename[0][:-1]
    info['Id'] = filename[0][-1]
    info['Initials'] = filename[1]
    if len(excelfilename) > 4:
        info['Other Info'] = filename[2:-1][0]
    return [info['Date'] + info['Id'] + '_' + info['Initials'], info]


def buildid(name):
    return name + '_' + str(current_app.config['VERSION'].strip('.'))


def getTime(t):
    time = datetime.datetime.strptime(t[:-4], '%m/%d/%Y %H:%M:%S')
    return time


class ImportProcessor(AbstractImporter):
    def __init__(self):
        self.identifers = dict(group=0, sample=-1, triplicate=-1, previous='')
        self.experimentlength = 0
        self.cyclelength = 0
        self.protocoldict = {}

    def search(self, name) -> {}:
        info = {}
        dataset_repository = Repository()
        #TODO: filter datasets by date
        found_dataset = dataset_repository.get_connection().find_one({'name': buildid(name)})
        if found_dataset is not None:
            for key in found_dataset.keys():
                info[key] = found_dataset[key]
            return info
        return None

    def execute(self, request, name) -> Response:
        dataset_repository = Repository()
        factory = Factory()
        model = factory.create({'name': buildid(name)})
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
                name = buildname(file.filename)

        self.getexperimentlength(infofile)
        self.getprotocols(request)
        for info, rfu in zip(infofile.read(sheet='0', userows=True), rfufile.read(sheet='SYBR', usecolumns=True)):
            self.add_measurement(info, rfu)

            self.measurement_manager.save()

        xlsx_file.delete()
        rfufile.delete()

        model['measure_count'] = model.get_well_collection().get_size()
        model['version'] = current_app.config['VERSION']
        model['metadata'] = dict(Protocols=self.protocoldict,
                                 Cut=0,
                                 Groupings={},
                                 Swaps={},
                                 CustomLabel='',
                                 Error_Wells={},
                                 Cycle_Length=self.cyclelength)
        dataset_repository.save(model)

        flash('File imported successfully', 'success')
        return Response(
            True,
            self.dataset.get_id()
        )

    def getprotocols(self, request):
        for item in request.form.keys():
            if item.startswith('pr'):
                self.protocoldict[request.form[item]] = request.form['pr' + str(item[-1])]

    def getexperimentlength(self, info):
        start = 0
        end = 0
        for row in info.read(sheet='Run Information', userows=True):
            if row[0] == 'Run Ended':
                end = getTime(row[1])
            if row[0] == 'Run Started':
                start = getTime(row[1])
        if start == 0 or end == 0:
            current_app.logger("Error retrieving experiment length")
        self.experimentlength = (end-start).total_seconds()

    def iterateidentifiers(self, label):
        if self.identifers['previous'] == '':
            self.identifers['control'] = label[:12]

        if self.identifers['previous'] != label:
            self.identifers['sample'] += 1
            self.identifers['triplicate'] += 1

            # TODO: check if control is labeled with '_0'
            if label[:12] == self.identifers['control']:
                self.identifers['group'] += 1
                self.identifers['sample'] = 0

        self.identifers['previous'] = label

    def add_measurement(self, inforow, rfuvalues):
        self.iterateidentifiers(inforow[5] + '_' + inforow[6])
        self.cyclelength = self.experimentlength/len(rfuvalues)

        data = {'dataset_id': self.dataset.get_id(),
                'excelheader': inforow[1],
                'cycle': self.cyclelength,
                'protocol': self.protocoldict,
                'label': inforow[5] + '_' + inforow[6],
                'group': self.identifers['group'],
                'sample': self.identifers['sample'],
                'triplicate': self.identifers['triplicate'],
                'RFUs': []
                }

        measurement_model = self.measurement_factory.create(data)
        measurement_model.add_values(rfuvalues)

        self.measurement_manager.add(measurement_model)
