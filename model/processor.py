import numpy as np
from collections import OrderedDict

from framework.model.request.response import Response
from framework.abstract.abstract_processor import AbstractProcessor
from model.functions import getFilePath, getTriplicateKeys, getTriplicateValues, getCycleLength, fitPolyEquation
from model.functions import getDerivatives, getPeaks, getExpectedValues, getUniqueKeys
from model.graphs import Grapher


class Processor(AbstractProcessor):
    def __init__(
            self,
            path: str = '',
            cut: int = 0,
            label: str = ''
    ):
        self.path = path
        self.cut = cut
        self.filelabel = label
        self.cycle = 27
        self.data = {}
        self.labeldict = {}
        self.output = {}
        self.averageoutput = {}
        self.errorpeaks = []

    def execute(self) -> Response:
        self.getData()
        response = self.processData()

        Grapher(path=self.path,
                data=self.data,
                labels=self.labeldict,
                output=self.output,
                averageoutput=self.averageoutput,
                errors=self.errorpeaks
                ).execute()

        return Response(response.is_success(), response.get_message())

    def getData(self) -> {}:
        rfufilepath = getFilePath('RFU', self.path)
        infofilepath = getFilePath('INFO', self.path)
        getTriplicateKeys(self, infofilepath)
        getCycleLength(self, infofilepath, rfufilepath)
        getTriplicateValues(self, rfufilepath)

    def processData(self) -> Response:
        message = ''
        self.errorpeaks = []
        for wellID in self.data.keys():
            if wellID != 'Time':
                derivatives = getDerivatives(self, int(wellID))
                inflectionList = []
                rfuList = []
                borderList = []
                for dIndex in derivatives.keys():
                    self.getInflectionPoints(dIndex, derivatives[dIndex], inflectionList, borderList)
                    if inflectionList is []:
                        self.errorpeaks.append(wellID)
                    else:
                        np.sort(inflectionList)
                        for index, inflectionPoint in enumerate(inflectionList):
                            rfuList.append(getExpectedValues(self, wellID, inflectionPoint,
                                                             borderList[index][0], borderList[index][1]))
                self.output[wellID] = {'Inflections': inflectionList, 'RFUs': rfuList}
        self.getPercentDifferences()
        if len(self.errorpeaks) != 0:
            message = 'Peaks could not be found in wells:' + str(self.errorpeaks)
        print(message)
        return Response(True, message)

    def getInflectionPoints(self, dindex, derivative, inflectionList, borderList):
        peaks, xstart, xend = getPeaks(dindex, derivative)
        if type(peaks[0]) == str:
            return []
        for peakindex, peaks in enumerate(peaks):
            timediff = [(self.data['Time'][t] + self.data['Time'][t + 1]) / 2 for t in range(len(self.data['Time']) - 1)]
            leftside = xstart[peakindex]
            rightside = min([xend[peakindex], len(derivative), len(timediff)])
            polycoefs = fitPolyEquation(timediff[leftside:rightside], derivative[leftside:rightside])
            inflectionList.append(-polycoefs[1] / (2 * polycoefs[0]))
            borderList.append([leftside, rightside])

    def getPercentDifferences(self):
        previousgroup = 0
        control = [0]
        Triplicates = [self.data[int(well)]['Label'] for well in self.data.keys() if well != 'Time']
        for triplicate in getUniqueKeys(Triplicates):
            group = triplicate[-1]
            triplicateGroup = []
            for well in self.data.keys():
                if well != 'Time' and self.data[int(well)]['Label'] == triplicate:
                    triplicateGroup.append(self.output[int(well)]['Inflections'])
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
