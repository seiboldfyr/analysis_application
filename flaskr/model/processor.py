import numpy as np
import os
from flask import flash, current_app
from statistics import mean, stdev

from flaskr.database.dataset_models.repository import Repository
from flaskr.framework.model.request.response import Response
from flaskr.framework.abstract.abstract_processor import AbstractProcessor
from flaskr.model.functions import getFile, getTriplicateKeys, getTriplicateValues, getCycleLength, fitPolyEquation
from flaskr.model.functions import getDerivatives, getPeaks, getExpectedValues
from flaskr.filewriter.writer import Writer

class Processor(AbstractProcessor):
    def __init__(
            self,
            dataset_id: str,
            paths: dict = None,
            cut: int = 0,
            label: str = '',
            swaps: dict = None,
            groupings: dict = None,
            errorwells: [] = None
    ):
        self.dataset_id = dataset_id
        self.paths = paths
        self.cut = cut
        self.customlabel = label
        self.swaps = swaps
        self.groupings = groupings
        self.data = {}
        self.errorwells = [well for well in errorwells.split(',')]
        self.statistics = {}
        self.time = []

    def execute(self) -> Response:
        dataset_repository = Repository()
        dataset = dataset_repository.get_by_id(self.dataset_id)
        collection = dataset.get_well_collection()

        collection = self.swapWells(collection)
        print('1')
        print(collection)
        for wellindex, well in enumerate(collection):
            print(wellindex)
            if wellindex < 2:
                self.time = [n*well.get_cycle() for n in range(len(well.get_rfus()))]
                print(self.time[:5])
            well['label'] = well.get_label() + '_' + well.get_group()
            response = self.processData(well, wellindex)
            if not response.is_succes():
                return Response(False, response.get_message())

        # self.getPercentDifferences()
        if len(self.errorwells) > 0 and self.errorwells[0] != '':
            flash('Peaks were not found in wells %s' % str(', '.join(self.errorwells)), 'error')


        # Writer(self.dataset_id, self.time).writebook(self.paths['output'])
        #
        # self.writeStatistics()

        return Response(True, 'Successfully processed inflections')

    def swapWells(self, collection):
        for well in collection:
            if self.swaps.get(well['excelheader']):
                for destwell in collection:
                    if destwell.get_excelheader() == self.swaps[well['excelheader']]:
                        well.edit_labels(dict(group=destwell.get_group(),
                                              sample=destwell.get_sample(),
                                              triplicate=destwell.get_triplicate(),
                                              label=destwell.get_label(),
                                              RFUs=destwell.get_rfus()))
        return collection

    def processData(self, well, index):
        if well['excelheader'] not in self.errorwells:
            derivatives = getDerivatives(self, int(index))
            inflectionList = []
            rfuList = []
            borderList = []
            for dIndex in derivatives.keys():
                response = self.getInflectionPoints(dIndex, derivatives[dIndex], inflectionList, borderList)
                if not response.is_success():
                    return Response(False, response.get_message())
            if inflectionList is [] or len(inflectionList) < 4:
                well['is_valid'] = False
            else:
                inflectionList = np.sort(inflectionList)
                for index, inflectionPoint in enumerate(inflectionList):
                    rfuList.append(getExpectedValues(self, index, inflectionPoint,
                                                     borderList[index][0], borderList[index][1]))
            well['inflections'] = inflectionList
            well['inflectionRFUs'] = rfuList
        else:
            well['is_valid'] = False
        return Response(True, '')

    def getInflectionPoints(self, dindex, derivative, inflectionList, borderList):
        peaks, xstart, xend = getPeaks(dindex, derivative)
        #TODO: improve peak finding to find the single largest, and then the second largest
        if type(peaks[0]) == str:
            return Response(False, 'Error retrieving inflection points')
        for peakindex, peak in enumerate(peaks):
            timediff = [(self.time[t] + self.time[t + 1]) / 2 for t in range(len(self.time) - 1)]
            leftside = xstart[peakindex]
            rightside = min([xend[peakindex], len(derivative), len(timediff)])
            polycoefs = fitPolyEquation(timediff[leftside:rightside], derivative[leftside:rightside])
            inflectionList.append((-polycoefs[1] / (2 * polycoefs[0]))/60)
            borderList.append([leftside, rightside])
        return Response(True, '')

    def getPercentDifferences(self):
        previousgroup = 0
        control = [0]
        for triplicate in sorted(self.data.items(), key=lambda x: x[1]['Triplicate']):
            triplicateGroup = []
            for well in self.data.keys():
                if self.data[well]['ExcelHeader'] not in self.errorwells and self.data[well]['Triplicate'] == triplicate[1]['Triplicate']:
                    wellinflections = self.data[well]['Inflections']
                    if len(wellinflections) != 4:
                        current_app.logger.info('Only %s inflections found in well: %s', str(len(wellinflections)), str(well))
                        continue
                    triplicateGroup.append(wellinflections)
            if len(triplicateGroup) == 0:
                continue
            tripAverage = np.mean(triplicateGroup, axis=0)
            if triplicate[1]['Group'] != previousgroup:
                control = tripAverage
                previousgroup = triplicate[1]['Group']
            if tripAverage.all() != 0 and control.all() != 0:
                relativeDifference = [abs(a - b) / ((a + b) / 2) for a, b in zip(tripAverage, control)]
                relativeDifference = [element * 100 for element in relativeDifference]
            else:
                relativeDifference = 'err'
            individualDifference = [abs(a - b) / ((a + b) / 2) for a, b in zip(triplicate[1]['Inflections'], control)]
            self.data[triplicate[0]]['Relative Difference'] = [individualDifference, relativeDifference]

        self.statistics['StDev Relative Difference for Inflection 1'] = \
            stdev([wellvalue['Relative Difference'][0][0] for wellvalue in self.data.values()
                   if wellvalue.get('Relative Difference')])
        self.statistics['StDev Relative Difference for Inflection 2,3,4'] = \
            stdev([mean(wellvalue['Relative Difference'][0][1:]) for wellvalue in self.data.values()
                   if wellvalue.get('Relative Difference')])
        self.statistics['StDev Relative Difference for all'] = \
            stdev([mean(wellvalue['Relative Difference'][0]) for wellvalue in self.data.values()
                   if wellvalue.get('Relative Difference')])

    def writeStatistics(self):
        with open(os.path.join(self.paths['output'], 'metadata.txt'), 'a') as f:
            f.write('\n')
            f.write("Additional Statistics: ")
            f.write('\n')
            for item in self.statistics.keys():
                line = str(item) + ': ' + str(self.statistics[item]) + '\n'
                f.write(line)