import numpy as np
import os
from flask import flash, current_app

from framework.model.request.response import Response
from framework.abstract.abstract_processor import AbstractProcessor
from model.functions import getTriplicateKeys, getTriplicateValues, getCycleLength, fitPolyEquation
from model.functions import getDerivatives, getPeaks, getExpectedValues, getUniqueKeys
from model.graphs import Grapher

class Processor(AbstractProcessor):
    def __init__(
            self,
            paths: [] = None,
            cut: int = 0,
            label: str = '',
            groupings: dict = None,
            errorwells= []
    ):
        self.path = paths
        self.cut = cut
        self.filelabel = label
        self.groupings = groupings
        self.cycle = 27
        self.data = {}
        self.labeldict = {}
        self.output = {}
        self.averageoutput = {}
        self.errorwells = errorwells

    def execute(self) -> Response:
        self.getData()
        response = self.processData()
        flash('Processed file. Beginning graph creation...')

        # Grapher(path=self.path,
        #         data=self.data,
        #         labels=self.labeldict,
        #         output=self.output,
        #         averageoutput=self.averageoutput,
        #         errors=self.errorpeaks
        #         ).execute()

        return Response(response.is_success(), response.get_message())

    def getData(self) -> {}:
        rfufilepath = self.getFile('RFU')
        infofilepath = self.getFile('INFO')
        getTriplicateKeys(self, infofilepath, self.groupings)
        getTriplicateValues(self, rfufilepath)
        getCycleLength(self, infofilepath, rfufilepath)

    def processData(self) -> Response:
        message = ''
        self.errorwells = [well for well in self.errorwells.split(',')]
        for wellID in self.data.keys():
            if wellID != 'Time' and self.labeldict[wellID][2] not in self.errorwells:
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
                self.output[wellID] = {'Inflections': inflectionList, 'RFUs': rfuList}
        self.getPercentDifferences()
        if len(self.errorwells) != 0:
            message = 'Peaks were not found in wells:' + str(self.errorwells)
            flash(message)
        return Response(True, message)

    def getFile(self, filetype) -> str:
        for file in os.listdir(self.path):
            fileend = filetype + '.xlsx'
            if file.endswith(fileend):
                name = os.path.join(self.path, file)
                return name
        return ''

    def getInflectionPoints(self, dindex, derivative, inflectionList, borderList):
        peaks, xstart, xend = getPeaks(dindex, derivative)
        if type(peaks[0]) == str:
            return []
        for peakindex, peak in enumerate(peaks):
            timediff = [(self.data['Time'][t] + self.data['Time'][t + 1]) / 2 for t in range(len(self.data['Time']) - 1)]
            leftside = xstart[peakindex]
            rightside = min([xend[peakindex], len(derivative), len(timediff)])
            polycoefs = fitPolyEquation(timediff[leftside:rightside], derivative[leftside:rightside])
            inflectionList.append((-polycoefs[1] / (2 * polycoefs[0]))/60)
            borderList.append([leftside, rightside])

    def getPercentDifferences(self):
        previousgroup = 0
        control = [0]
        Triplicates = [self.data[int(well)]['Label'] for well in self.data.keys() if well != 'Time']
        for triplicate in getUniqueKeys(Triplicates):
            group = triplicate[-1]
            triplicateGroup = []
            for well in self.data.keys():
                if well != 'Time' and self.labeldict[well][2] not in self.errorwells and \
                        self.data[int(well)]['Label'] == triplicate:
                    wellinflections = self.output[int(well)]['Inflections']
                    if len(wellinflections) != 4:
                        current_app.logger.info('Only %s inflections found in well: %s', str(len(wellinflections)), str(well))
                        continue
                    triplicateGroup.append(wellinflections)
            tripAverage = np.mean(triplicateGroup, axis=0)
            if group != previousgroup:
                control = tripAverage
                previousgroup = group
            if tripAverage.all() != 0 and control.all() != 0:
                relativeDifference = [abs(a - b) / ((a + b) / 2) for a, b in zip(tripAverage, control)]
                relativeDifference = [element * 100 for element in relativeDifference]
            else:
                relativeDifference = 'err'
            if self.averageoutput.get(triplicate) is None:
                self.averageoutput[triplicate] = relativeDifference
            else:
                self.averageoutput[triplicate].append([relativeDifference])
