from flask import flash
import sys
import time

from flaskr.database.measurement_models.manager import Manager as MeasurementManager
from flaskr.framework.model.request.response import Response
from flaskr.framework.abstract.abstract_processor import AbstractProcessor
from flaskr.model.helpers.buildfunctions import build_group_inputs, build_swap_inputs, get_collection
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
        timestart = time.time()
        self.measurement_manager = MeasurementManager()

        #TODO: if dataset has metadata, use that info instead of request.form

        cut = self.request.form['cutlength']
        if cut is None or isinstance(cut, str):
            cut = 0

        build_swap_inputs(self)
        build_group_inputs(self)
        self.errorwells = [well for well in self.request.form['errorwells'].split(',')]

        for wellindex, well in enumerate(get_collection(self)):

            # swap wells and shift RFUs to account for a cut time
            if len(self.swaps) > 0 and self.swaps.get(well.get_excelheader()) is not None:
                self.swapWells(well)
            if cut > 0:
                self.editRFUs(well, cut)

            # set well status to invalid if reported
            if well.get_excelheader() in self.errorwells:
                well['is_valid'] = False
                self.measurement_manager.update(well)

            # build time list from first well
            if wellindex < 2:
                self.time = [n /60.  * well.get_cycle() for n in range(len(well.get_rfus()))]

            if well.get_label()[-2] != "_":
                well['label'] = well.get_label() + '_' + str(well.get_group())

            response = self.processData(well)

            if not response.is_success():
                return Response(False, response.get_message())

        if len(self.errorwells) > 0 and self.errorwells[0] != '':
            flash('Peaks were not found in wells %s' % str(', '.join(self.errorwells)), 'error')

        return Response(True, str(round(time.time() - timestart, 2)))

    def swapWells(self, originwell):
        for destwell in get_collection(self):
            if destwell.get_excelheader() == self.swaps[originwell.get_excelheader()]:
                originwell.edit_labels(dict(group=destwell.get_group(),
                                            sample=destwell.get_sample(),
                                            triplicate=destwell.get_triplicate(),
                                            label=destwell.get_label(),
                                            RFUs=destwell.get_rfus()))
                self.measurement_manager.update(originwell)

    def editRFUs(self, originwell, cut):
        originwell.edit_labels(dict(RFUs=originwell.get_rfus()[cut:]))
        self.measurement_manager.update(originwell)

    def processData(self, well):
        if well['excelheader'] in self.errorwells:
            well['is_valid'] = False

        else:
            derivatives = get_derivatives(well)
            inflection_list = {}  #
            rfu_list = []
            for dIndex in derivatives.keys():
                response = self.getInflectionPoints(dIndex, derivatives[dIndex], inflection_list)
                if not response.is_success():
                    well['is_valid'] = False
                    flash(response.get_message() + ' %s' % well.get_excelheader(), 'error')
                    break
            inflection_list = dict(sorted(inflection_list.items()))
            for index, key in enumerate(inflection_list):
                rfu_list.append(get_expected_values(self, well, key, inflection_list[key])[0])
            # TODO: save inflections in a dictionary from the get-go
            well['inflections'] = list(inflection_list.keys())
            well['inflectionRFUs'] = list(rfu_list)
            if well.get_group() != self.controlgroup:
                self.controlgroup = well.get_group()
                self.control = well['inflections']
            well['percentdiffs'] = get_percent_difference(self, well['inflections'])

        self.measurement_manager.update(well)
        return Response(True, '')

    def getInflectionPoints(self, dindex, derivative, inflection_list):
        peaks, xstarts, xends = get_peaks(dindex, derivative)
        # TODO: improve peak finding to find the single largest, and then the second largest
        if type(peaks[0]) == str:
            return Response(False, 'Error retrieving inflection points for well: ')
        for peakindex, peak in enumerate(peaks):
            timediff = [(self.time[t] + self.time[t + 1]) / 2 for t in range(len(self.time) - 1)]
            leftside = xstarts[peakindex]
            rightside = min([xends[peakindex], len(derivative), len(timediff)])
            polycoefs = fit_poly_equation(timediff[leftside:rightside], derivative[leftside:rightside])
            inflection_list[(-polycoefs[1] / (2 * polycoefs[0]))] = dict(left=leftside, right=rightside)
        if inflection_list is {} or len(inflection_list) < 2:
            return Response(False, '%s of 4 inflections were found in well: ' % len(inflection_list))
        return Response(True, '')
