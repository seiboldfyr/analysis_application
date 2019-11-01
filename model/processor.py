import numpy as np
import os
from flask import flash, current_app
from statistics import mean, stdev
from operator import attrgetter, itemgetter

from framework.model.request.response import Response
from framework.abstract.abstract_processor import AbstractProcessor
from model.functions import getFile, getTriplicateKeys, getTriplicateValues, getCycleLength, fitPolyEquation
from model.functions import getDerivatives, getPeaks, getExpectedValues
from model.graphs import Grapher
from filewriter.writer import Writer

class Processor(AbstractProcessor):
    def __init__(
            self,
            paths: dict = None,
            cut: int = 0,
            label: str = '',
            swaps: dict = None,
            groupings: dict = None,
            errorwells: [] = None
    ):
        self.paths = paths
        self.cut = cut
        self.customlabel = label
        self.swaps = swaps
        self.groupings = groupings
        self.cycle = 27
        self.data = {}
        self.time = []
        self.errorwells = errorwells
        self.statistics = {}

    def execute(self) -> Response:
        self.getData()
        response = self.processData()
        flash('Processed to: %s' % self.paths['output'])

        Grapher(paths=self.paths,
                customtitle=self.customlabel,
                data=self.data,
                errors=self.errorwells,
                time=self.time
                ).execute()

        Writer(data=self.data).writebook(self.paths['output'])

        self.writeStatistics()

        return Response(response.is_success(), response.get_message())

    def getData(self) -> {}:
        rfufilepath = getFile(self, 'RFU')
        infofilepath = getFile(self, 'INFO')
        getTriplicateKeys(self, infofilepath, self.groupings)
        getTriplicateValues(self, rfufilepath)
        getCycleLength(self, infofilepath, rfufilepath)

    def processData(self) -> Response:
        message = ''
        self.errorwells = [well for well in self.errorwells.split(',')]
        for wellID in self.data.keys():
            if wellID != 'Time' and self.data[wellID]['ExcelHeader'] not in self.errorwells:
                derivatives = getDerivatives(self, int(wellID))
                inflectionList = []
                rfuList = []
                borderList = []
                for dIndex in derivatives.keys():
                    self.getInflectionPoints(dIndex, derivatives[dIndex], inflectionList, borderList)
                if inflectionList is [] or len(inflectionList) < 4:
                    self.errorwells.append(wellID)
                else:
                    inflectionList = np.sort(inflectionList)
                    for index, inflectionPoint in enumerate(inflectionList):
                        rfuList.append(getExpectedValues(self, wellID, inflectionPoint,
                                                         borderList[index][0], borderList[index][1]))
                self.data[wellID]['Inflections'] = inflectionList
                self.data[wellID]['RFUs'] = rfuList
        self.getPercentDifferences()
        if len(self.errorwells) > 0 and self.errorwells[0] != '':
            message = 'Peaks were not found in wells:' + str(self.errorwells) #TODO: concatenate items in string
        return Response(True, message)

    def getInflectionPoints(self, dindex, derivative, inflectionList, borderList):
        peaks, xstart, xend = getPeaks(dindex, derivative)
        if type(peaks[0]) == str:
            return []
        for peakindex, peak in enumerate(peaks):
            timediff = [(self.time[t] + self.time[t + 1]) / 2 for t in range(len(self.time) - 1)]
            leftside = xstart[peakindex]
            rightside = min([xend[peakindex], len(derivative), len(timediff)])
            polycoefs = fitPolyEquation(timediff[leftside:rightside], derivative[leftside:rightside])
            inflectionList.append((-polycoefs[1] / (2 * polycoefs[0]))/60)
            borderList.append([leftside, rightside])

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