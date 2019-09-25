import numpy as np
import xlsxwriter
import xlrd
from collections import OrderedDict, Counter

from framework.model.request.response import Response
from framework.abstract.abstract_processor import AbstractProcessor
from model.functions import getFilePath, getTriplicateKeys, getTriplicateValues, fitPolyEquation, averagetriplicates
from model.functions import calculateCycleLength, getDerivatives, getPeaks, getExpectedValues


class Processor(AbstractProcessor):
    def __init__(
            self,
            path: str,
            cycle: int = 27,
            cut: int = 0,
            length: int = 0,
            datacount: int = 0
    ):
        self.path = path
        self.cycle = cycle
        self.cut = cut
        self.length = length
        self.datacount = datacount
        self.data = {}
        self.output = OrderedDict()

    def execute(self, request) -> Response:
        self.getData()
        self.processData()

    def getData(self):
        rfufile = getFilePath('RFU', self.path)
        infofile = getFilePath('INFO', self.path)
        labelDict = getTriplicateKeys(infofile)
        getTriplicateValues(rfufile, labelDict)

    def processData(self) -> Response:
        calculateCycleLength()
        inflectionDict = OrderedDict()  # keys: 'Inflection 1-4' , values are the inflection points
        rfuDict = OrderedDict()
        for wellID in self.data.keys():
            if wellID != 'Time':
                derivatives = getDerivatives(self)
                for derivative in derivatives.keys():
                    inflectionList = self.getInflectionPoints(derivative)
                    if inflectionList is []:
                        message = str('Peaks could not be found in well:' + wellID)
                    else:
                        np.sort(inflectionList)
                        for inflectionPoint, inflectionIndex in enumerate(inflectionList):
                            inflectionLabel = 'Inflection ' + str(inflectionIndex + 1)
                            rfuLabel = 'RFU at Inflection ' + str(inflectionIndex + 1)
                            inflectionDict[inflectionLabel] = inflectionPoint
                            rfuDict[rfuLabel] = getExpectedValues(wellID, inflectionPoint)
            self.output[wellID] = [inflectionDict, rfuDict]
        return Response(True, message)


def getInflectionPoints(self, derivative) -> []:
    inflectionList = []
    peaks, xstart, xend = getPeaks(derivative)
    if peaks[0].type == str:
        return []
    for peaks, peakindex in enumerate(peaks):
        leftside = xstart[peakindex]
        rightside = xend[peakindex]
        timediff = [(self.data['TIME'][t] + self.data['TIME'][t + 1]) / 2 for t in range(len(self.data['TIME']) - 1)]
        polycoefs = fitPolyEquation(timediff[leftside:rightside], derivative[leftside:rightside])
        inflectionList.append(-polycoefs[1] / (2 * polycoefs[0]))
    return inflectionList
