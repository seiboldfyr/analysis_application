from flask import flash, current_app
import pandas as pd
import numpy as np
import time

from flaskr.database.measurement_models.manager import Manager as MeasurementManager
from flaskr.database.dataset_models.repository import Repository
from flaskr.framework.model.request.response import Response
from flaskr.framework.abstract.abstract_processor import AbstractProcessor
from flaskr.model.helpers.calcfunctions import get_derivatives, get_percent_difference, get_linear_approx
from flaskr.model.helpers.buildfunctions import build_group_inputs, build_swap_inputs, swap_wells, validate_errors,\
    add_custom_group_label
from flaskr.model.helpers.importfunctions import get_existing_metadata, update_metadata, get_collection
from flaskr.model.helpers.peakfunctions import get_peaks


class Processor(AbstractProcessor):
    def __init__(
            self,
            form: dict,
            dataset_id: str
    ):
        self.form = form
        self.errorwells = []
        self.dataset_id = dataset_id
        self.swaps = {}
        self.tempswaps = {}
        self.groupings = {}
        self.statistics = pd.DataFrame(columns=['group', 'sample', '1', '2', '3', '4'])
        self.time = []
        self.control = None
        self.controllist = []
        self.ctlist = []
        self.ctthreshold = {'Ct RFU': [], 'Ct Cycle': []}

    def execute(self) -> Response:
        timestart = time.time()
        self.measurement_manager = MeasurementManager()

        if self.form is None:
            get_existing_metadata(self)
        else:
            update_metadata(self)

        build_swap_inputs(self)
        build_group_inputs(self)
        validate_errors(self)

        wellindex = 0
        for wellindex, well in enumerate(get_collection(self)):

            well = add_custom_group_label(self, well, wellindex)

            # swap wells and shift RFUs to account for a cut time
            if len(self.swaps) > 0 and self.swaps.get(well.get_excelheader()) is not None:
                well = swap_wells(self, well)
                self.measurement_manager.update(well)
                try:
                    self.swaps.pop(well.get_excelheader())
                except KeyError:
                    current_app.logger.error('Error deleting swap from swap dictionary')

            # set well status to invalid if reported
            if well.get_excelheader() in self.errorwells:
                well['is_valid'] = False

            # build time list from first well
            if wellindex < 2:
                self.time = [n for n in range(len(well.get_rfus()))]

            self.measurement_manager.update(well)
            response = self.processData(well)

            if not response.is_success():
                return Response(False, response.get_message())

        if len(self.swaps) > 0:
            missing_swaps = ", ".join([item for item in self.swaps.keys()])
            flash('Swap(s) from the following well(s) %s could not occur. Please verify the entered values.' % missing_swaps, 'error')
        if len(self.errorwells) > 0 and self.errorwells[0] != '':
            flash('Peaks were not found in wells %s' % str(', '.join(self.errorwells)), 'error')

        self.getStatistics()

        welltotal = sum([int(self.groupings[g]['Wells']) for g in self.groupings.keys()])
        if welltotal == 0:
            welltotal = wellindex + 1
        if welltotal != wellindex+1:
            flash('Number of Wells in Custom Groups Not Equal to Total Number of Wells', 'error')
            flash('Please Edit Inputs', 'error')

        return Response(True, str(round(time.time() - timestart, 2)))

    def processData(self, well):
        if well['excelheader'] in self.errorwells:
            well['is_valid'] = False

        else:
            well['is_valid'] = True
            percentdiffs = [0 for x in range(4)]
            deltact = [0 for x in range(3)]
            inflectiondict = {}
            derivatives = get_derivatives(well)

            for dIndex in derivatives.keys():
                inflectiondict = get_peaks(self,
                                           well=well,
                                           derivativenumber=dIndex,
                                           derivative=derivatives[dIndex],
                                           allpeaks=inflectiondict)
            inflectiondict = dict(sorted(inflectiondict.items()))

            well['inflections'] = [(key, inflectiondict[key]['inflection']) for key in inflectiondict.keys()]
            well['inflectionRFUs'] = [(key, inflectiondict[key]['rfu']) for key in inflectiondict.keys()]

            if len(inflectiondict.keys()) < 4:
                flash('%s of 4 inflections were found in well: %s' % (str(len(inflectiondict)),
                                                                      well.get_excelheader()), 'error')

            if self.groupings.get(str(well.get_group())):
                groupcontrols = self.groupings[str(well.get_group())]['Controls'].split(',')
                if well.get_excelheader() in groupcontrols:
                    well['is_control'] = True
                    # TODO: will need to loop through all wells, set control property
                    # before making the following calculations

            if self.control is None or well.get_group() != self.control.get_group():
                self.control = well
                self.controllist = []
                self.ctthreshold = {'Ct RFU': [], 'Ct Cycle': []}

            #for all samples that match the control sample, collect controls
            if self.control.get_sample() == well.get_sample():
                self.controllist.append([x for x in well.get_inflections()])
                if not self.form.get('gPCR'):
                    controlCt = self.getCtThreshold(well, derivatives[1], inflectiondict)
                    self.ctlist.append(controlCt)
                    deltact = [0, controlCt['Ct Cycle'], controlCt['Ct RFU']]

                #average the control inflections
                #TODO: what if the first control has only 2 inflections and the others have 4? or vice versa?

                for idx, x in enumerate(self.control.get_inflections()):
                    i = int(x[0])
                    self.control['inflections'][idx] = (str(i), np.mean([controlinflection[idx][1]
                                                                         for controlinflection in self.controllist
                                                                         if len(controlinflection) > idx]))

                #average the ct threshold
                self.ctthreshold['Ct Cycle'] = np.mean([x['Ct Cycle'] for x in self.ctlist])
                self.ctthreshold['Ct RFU'] = np.mean([x['Ct RFU'] for x in self.ctlist])

            # get percent differences and delta ct values
            elif self.control.get_sample() != well.get_sample():
                percentdiffs = get_percent_difference(self, well['inflections'])
                if not self.form.get('gPCR'):
                    deltact = self.getDeltaCt(well)

            # calculate delta ct and percent diffs
            well['deltaCt'] = deltact
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

    def getCtThreshold(self, well, derivative, inflectiondict):
        plateauborders = [0, len(derivative)]
        for idx, key in enumerate(inflectiondict.keys()):
            if idx == 0:
                plateauborders[0] = int(inflectiondict[key]['location'])
            else:
                plateauborders[1] = int(inflectiondict[key]['location'])
                break
        plateauslope = derivative[plateauborders[0]: plateauborders[1]]

        if not plateauslope.any():
            try:
                plateauslope = derivative[int(inflectiondict['2']['location']): int(inflectiondict['1']['location'])]
            except KeyError:
                return {'Ct RFU': 0, 'Ct Cycle': 0}

        plateaumin = (np.where(plateauslope == min(plateauslope))[0])
        if len(plateaumin) > 1:
            plateaumin = plateaumin[0]
        plateaucenter = int(plateaumin) + plateauborders[0]
        return {'Ct RFU': well.get_rfus()[plateaucenter],
                'Ct Cycle': self.time[plateaucenter]}

    def getDeltaCt(self, well):
        for idx, wellRFU in enumerate(well.get_rfus()):
            if wellRFU > self.ctthreshold['Ct RFU']:
                lineareqn = get_linear_approx(x1=self.time[idx-1],
                                              x2=self.time[idx],
                                              y1=well.get_rfus()[idx-1],
                                              y2=wellRFU)
                ctthreshold = self.getxValueFromLinearApprox(lineareqn)

                deltact = self.ctthreshold['Ct Cycle'] - ctthreshold
                return [deltact, ctthreshold, self.ctthreshold['Ct RFU']]

        return [0, 0]

    def getxValueFromLinearApprox(self, equation):
        slope = equation[0]
        yintercept = equation[1]
        return (self.ctthreshold['Ct RFU'] - yintercept) / slope

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
