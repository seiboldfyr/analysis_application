import numpy as np
from collections import OrderedDict

from framework.model.request.response import Response
from framework.abstract.abstract_processor import AbstractProcessor
from model.functions import getFilePath, getTriplicateKeys, getTriplicateValues, getCycleLength, fitPolyEquation
from model.functions import getDerivatives, getPeaks, getExpectedValues


class Processor(AbstractProcessor):
    def __init__(
            self,
            path: str = '',
            cut: int = 0
    ):
        self.path = path
        self.cut = cut
        self.cycle = 27
        self.data = {}
        self.labeldict = {}
        self.output = OrderedDict()

    def execute(self) -> Response:
        self.getData()
        response = self.processData()
        return Response(True, '')

    def getData(self) -> {}:
        rfufilepath = getFilePath('RFU', self.path)
        infofilepath = getFilePath('INFO', self.path)
        getTriplicateKeys(self, infofilepath)
        getCycleLength(self, infofilepath, rfufilepath)
        getTriplicateValues(self, rfufilepath)

    def processData(self) -> Response:
        inflectionDict = OrderedDict()  # keys: 'Inflection 1-4' , values are the inflection points
        rfuDict = OrderedDict()
        message = ''
        errorpeaks = []
        for wellID in self.data.keys():
            if wellID != 'Time':
                derivatives = getDerivatives(self, wellID)
                for dIndex in derivatives.keys():
                    [inflectionList, borderList] = self.getInflectionPoints(dIndex, derivatives[dIndex])
                    print(borderList)
                    if inflectionList is []:
                        errorpeaks.append(wellID)
                    else:
                        np.sort(inflectionList)
                        for index, inflectionPoint in enumerate(inflectionList):
                            inflectionLabel = 'Inflection ' + str(index + 1)
                            rfuLabel = 'RFU at Inflection ' + str(index + 1)
                            inflectionDict[inflectionLabel] = inflectionPoint
                            rfuDict[rfuLabel] = getExpectedValues(self, wellID, inflectionPoint,
                                                                  borderList[index][0], borderList[index][1])
                            print(inflectionDict[inflectionLabel],rfuDict[rfuLabel])
            self.output[wellID] = [inflectionDict, rfuDict]
        if len(errorpeaks) != 0:
            message = 'Peaks could not be found in wells:' + str(errorpeaks)
        print(message)
        return Response(True, message)

    def getInflectionPoints(self, dindex, derivative) -> []:
        inflectionList = []
        borderList = []
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
        return [inflectionList, borderList]
