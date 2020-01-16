from flask import flash
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time

from flaskr.database.measurement_models.manager import Manager as MeasurementManager
from flaskr.database.dataset_models.repository import Repository
from flaskr.framework.model.request.response import Response
from flaskr.framework.abstract.abstract_processor import AbstractProcessor
from flaskr.model.helpers.buildfunctions import build_group_inputs, build_swap_inputs, get_collection, add_custom_group_label
from flaskr.model.helpers.calcfunctions import get_derivatives, get_percent_difference, get_expected_values
from flaskr.model.helpers.peakfunctions import get_peaks


class Processor(AbstractProcessor):
    def __init__(
            self, request,
            dataset_id: str
    ):
        self.request = request
        self.dataset_id = dataset_id
        self.swaps = {}
        self.groupings = {}
        self.statistics = pd.DataFrame(columns=['group', 'sample', '1', '2', '3', '4'])
        self.time = []
        self.control = None

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

            # build time list from first well
            if wellindex < 2:
                #TODO: undo
                self.time = [n * well.get_cycle() / 60 for n in range(cut, len(well.get_rfus()))]

            well = add_custom_group_label(self, well)

            self.measurement_manager.update(well)
            response = self.processData(well)

            if not response.is_success():
                return Response(False, response.get_message())

        if len(self.errorwells) > 0 and self.errorwells[0] != '':
            flash('Peaks were not found in wells %s' % str(', '.join(self.errorwells)), 'error')

        self.getStatistics()

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
            percentdiffs = [0, 0, 0, 0]
            inflectiondict = {}
            derivatives = get_derivatives(well)
            for dIndex in derivatives.keys():
                inflectiondict = get_peaks(self, well=well,
                                           derivativenumber=dIndex,
                                           derivative=derivatives[dIndex],
                                           allpeaks=inflectiondict)
            inflectiondict = dict(sorted(inflectiondict.items()))

            #TODO: are the RFUs getting sorted?
            if len(inflectiondict.keys()) < 4:
                well['is_valid'] = False
                flash('%s of 4 inflections were found in well: %s' % (str(len(inflectiondict)),
                                                                      well.get_excelheader()), 'error')

            well['inflections'] = [(key, inflectiondict[key]['inflection']) for key in inflectiondict.keys()]
            well['inflectionRFUs'] = [(key, inflectiondict[key]['rfu']) for key in inflectiondict.keys()]
            well['plateau'] = self.getPlateau(well, derivatives, inflectiondict)
            if self.control is None or well.get_group() != self.control.get_group():
                self.control = well

            if self.control.get_sample() != well.get_sample():
                percentdiffs = get_percent_difference(self, well['inflections'])
            well['percentdiffs'] = percentdiffs

            #TODO: check validity? These should be able to be corrected on another run
            if len(inflectiondict.keys()) == 4:
                self.statistics = self.statistics.append([{'group': well.get_group(),
                                                           'sample': well.get_sample(),
                                                           '1': inflectiondict.get('1')['inflection'],
                                                           '2': inflectiondict.get('2')['inflection'],
                                                           '3': inflectiondict.get('3')['inflection'],
                                                           '4': inflectiondict.get('4')['inflection']}],
                                                         ignore_index=True)

        self.measurement_manager.update(well)
        return Response(True, '')

    def getPlateau(self, well, derivative, inflectiondict):
        # plateautime = inflectiondict['inflection']
        # i = int(inflectiondict['location'])
        startPlateau = int(inflectiondict['1']['location'])
        endPlateau = int(inflectiondict['2']['location'])
        i = startPlateau
        print(startPlateau, endPlateau)
        # flattest = min(well.get_rfus()[startPlateau: endPlateau])
        plateau = derivative[1][startPlateau: endPlateau]
        # print(derivative[1])
        flattest = list(np.where(derivative[1] == min(plateau)))
        print(inflectiondict['1']['inflection'], inflectiondict['2']['inflection'], flattest)
        #Want 18
        #TODO: try if derivative <= 0 when WSZ <= 5
        #TODO: try if derivative[2][i] < 0 and derivative[2][i+1] >=0
        # and derivative[1][i] < derivative[1][i+1]
        #Minimize derivative[1] between inflection 2 and 3
        while derivative[1][i] > 0 and i < len(self.time)-2:
            print(i, self.time[i], well.get_rfus()[i], derivative[1][i], derivative[2][i])
            plateautime = self.time[i]
            i += 1
        # print(inflectiondict['inflection'], plateautime, well.get_rfus()[i])
        # plt.plot([x/50 for x in well.get_rfus()])
        plt.plot(self.time, well.get_rfus())
        plt.axvline(x=inflectiondict['1']['inflection'])
        plt.axvline(x=inflectiondict['2']['inflection'])
        # plt.plot(derivative[1][:100])
        # plt.plot(derivative[2][:100])
        plt.savefig('derivative.png')
        sys.exit()
        return [plateautime, well.get_rfus()[i]]

    def getStatistics(self):
        if not self.statistics.empty:

            dataset_repository = Repository()
            dataset = dataset_repository.get_by_id(self.dataset_id)

            dataset['statistics'] = {'sample variation': self.statistics.groupby('sample').std()
                                                                  [['1', '2', '3', '4']].mean(1).tolist(),
                                     'group variation': self.statistics.groupby('group').std()
                                                                 [['1', '2', '3', '4']].mean(1).tolist()}
            flash('Average variation for each concentration is: %s' %
                  ', '.join([str(round(item, 3)) for item in dataset['statistics']['sample variation']]), 'msg')
            flash('Average variation for each group is: %s' %
                  ', '.join([str(round(item, 3)) for item in dataset['statistics']['group variation']]), 'msg')
            dataset_repository.save(dataset)
