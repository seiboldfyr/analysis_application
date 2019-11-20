from flask import flash
import sys

from flaskr.database.measurement_models.manager import Manager as MeasurementManager
from flaskr.database.dataset_models.repository import Repository
from flaskr.framework.model.request.response import Response
from flaskr.framework.abstract.abstract_processor import AbstractProcessor
from flaskr.model.helpers.buildfunctions import build_group_inputs, build_swap_inputs
from flaskr.model.helpers.calcfunctions import fit_poly_equation, get_expected_values, get_derivatives, \
    get_percent_difference
from flaskr.model.helpers.peakfunctions import get_peaks


class Processor(AbstractProcessor):
    def __init__(
            self, request,
            dataset_id: str
    ):
        self.request = request
        self.dataset_id = dataset_id
        self.swaps = {}
        self.groupings = None
        self.data = {}
        self.statistics = {}
        self.time = []
        self.control = []
        self.controlgroup = int

    def execute(self) -> Response:
        self.measurement_manager = MeasurementManager()

        cut = self.request.form['cutlength']
        if cut is None:
            cut = 0
        customlabeladdition = self.request.form['customlabel'] #TODO: move this to wherever we use it
        build_swap_inputs(self)
        build_group_inputs(self)
        self.errorwells = [well for well in self.request.form['errorwells'].split(',')]

        for wellindex, well in enumerate(self.get_collection()):

            #swap wells
            if len(self.swaps) > 0 and self.swaps.get(well.get_excelheader()) is not None:
                self.swapWells(well)

            #set well status to invalid if reported
            if well.get_excelheader() in self.errorwells:
                well['is_valid'] = False
                self.measurement_manager.update(well)

            #build time list from first well
            if wellindex < 2:
                self.time = [n*well.get_cycle() for n in range(len(well.get_rfus()))]

            well['label'] = well.get_label() + '_' + str(well.get_group())

            response = self.processData(well)

            if not response.is_success():
                return Response(False, response.get_message())

        # todo: Writer(self.dataset_id, self.time).writebook(self.paths['output'])
        # todo: self.writeStatistics()

        if len(self.errorwells) > 0 and self.errorwells[0] != '':
            flash('Peaks were not found in wells %s' % str(', '.join(self.errorwells)), 'error')
        return Response(True, 'Successfully processed inflections')

    def swapWells(self, originwell):
        for destwell in self.get_collection():
            if destwell.get_excelheader() == self.swaps[originwell.get_excelheader()]:
                originwell.edit_labels(dict(group=destwell.get_group(),
                                            sample=destwell.get_sample(),
                                            triplicate=destwell.get_triplicate(),
                                            label=destwell.get_label(),
                                            RFUs=destwell.get_rfus()))
                self.measurement_manager.update(originwell)

    def processData(self, well):
        if well['excelheader'] not in self.errorwells:
            derivatives = get_derivatives(well)
            inflectionList = {} #
            rfuList = []
            for dIndex in derivatives.keys():
                response = self.getInflectionPoints(dIndex, derivatives[dIndex], inflectionList)
                if not response.is_success():
                    return Response(False, response.get_message())
            if inflectionList is [] or len(inflectionList) < 4:
                well['is_valid'] = False
            else:
                inflectionList = dict(sorted(inflectionList.items()))
                for index, key in enumerate(inflectionList):
                    rfuList.append(get_expected_values(self, well, key, inflectionList[key])[0])
            well['inflections'] = list(inflectionList.keys())
            well['inflectionRFUs'] = list(rfuList)
            if well.get_group() != self.controlgroup:
                self.controlgroup = well.get_group()
                self.control = well['inflections']
            well['percentdiffs'] = get_percent_difference(self, well['inflections'])
        else:
            well['is_valid'] = False
        self.measurement_manager.update(well)
        return Response(True, '')


    def getInflectionPoints(self, dindex, derivative, inflectionList):
        peaks, xstarts, xends = get_peaks(dindex, derivative)
        #TODO: Move this to it's own class
        #TODO: improve peak finding to find the single largest, and then the second largest
        if type(peaks[0]) == str:
            return Response(False, 'Error retrieving inflection points')
        for peakindex, peak in enumerate(peaks):
            timediff = [(self.time[t] + self.time[t + 1]) / 2 for t in range(len(self.time) - 1)]
            leftside = xstarts[peakindex]
            rightside = min([xends[peakindex], len(derivative), len(timediff)])
            polycoefs = fit_poly_equation(timediff[leftside:rightside], derivative[leftside:rightside])
            inflectionList[(-polycoefs[1] / (2 * polycoefs[0]))/60] = dict(left=leftside, right=rightside)
        return Response(True, '')

    def get_collection(self):
        dataset_repository = Repository()
        dataset = dataset_repository.get_by_id(self.dataset_id)
        return dataset.get_well_collection()


