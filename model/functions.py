from scipy.signal import find_peaks
import numpy as np
import os
import xlrd
import pandas as pd
import datetime
from flask import flash


def getCycleLength(self, infopath, rfupath):
    inforaw = pd.ExcelFile(infopath)
    infosheet = inforaw.parse('Run Information').values
    length = getRunEnd(infosheet[:, :2]) - getRunStart(infosheet[:, :2])

    rfuraw = pd.ExcelFile(rfupath)
    rfusheet = rfuraw.parse('SYBR').values
    datacount = len(rfusheet[:, 0])
    self.cycle = length/datacount


def getRunStart(data) -> datetime:
    labels = data[:, 0]
    values = data[:, 1]
    for idx, item in enumerate(labels):
        if str(item) == 'Run Started':
            time = datetime.datetime.strptime(values[idx][:-4], '%m/%d/%Y %H:%M:%S')
            return time.second + time.minute * 60 + time.hour * 3600


def getRunEnd(data) -> datetime:
    labels = data[:, 0]
    values = data[:, 1]
    for idx, item in enumerate(labels):
        if str(item) == 'Run Ended':
            time = datetime.datetime.strptime(values[idx][:-4], '%m/%d/%Y %H:%M:%S')
            return time.second + time.minute * 60 + time.hour * 3600


def getGroupHeaders(triplicateHeaders):
    headers = []
    previousgroup = 0
    for h in triplicateHeaders:
        if int(h[-1]) > previousgroup:
            headers.append(h[7:])
            previousgroup = int(h[-1])
    return headers


def getTriplicateIndexes(data):
    triplicateIndex = -1
    triplicateIndexList = []
    previouslabel = ''
    for label in data:
        if label != previouslabel:
            triplicateIndex += 1
            previouslabel = label
        triplicateIndexList.append(triplicateIndex)
    return triplicateIndexList


def getUniqueKeys(keylist):
    indexes = np.unique(keylist, return_index=True)[1]
    return [keylist[value] for value in sorted(indexes)]


def getTriplicateKeys(self, path, inputinfo) -> {}:
    labelraw = pd.ExcelFile(path)
    labelsheet = labelraw.parse('0')
    label = labelsheet.values
    if len(inputinfo) == 0:
        control = label[0, 5]
        group = 1
        prevrow = 0
        for row in range(0, len(label[:, 1])):
            if label[row, 5] == control and row > 6 and row > prevrow + 6:
                group += 1
                prevrow = row
            header = str(label[row, 5]) + '_' + str(label[row, 6]) + '_' + str(group)
            addHeader(self, row, header, group, label[row, 1])
    else:
        row = 0
        for group in inputinfo.keys():
            groupsize = float(inputinfo[group]['Group Wells']) * float(inputinfo[group]['Group Samples'])
            if groupsize % 1 != 0:
                flash('possible error with wells/samples', 'error')  # TODO: validator
            grouplabel = inputinfo[group]['Group Label']
            for well in range(int(groupsize)):
                row += 1
                if row > len(label[:, 1]):
                    flash('The wells and samples added up to be more than the % s wells' % len(label[:, 1]), 'error')
                header = str(label[row, 5]) + '_' + str(label[row, 6]) + '_' + grouplabel + '_' + str(group)
                addHeader(self, row, header, group, label[row, 1])


def addHeader(self, row, header, group, excelindex):
    self.data[row] = {'Label': header, 'Group': group, 'Values': []}
    self.labeldict[row] = [header, group, excelindex]


def getTriplicateValues(self, path):
    wb = xlrd.open_workbook(path)
    sheet = wb.sheet_by_name('SYBR')
    for column in range(1, sheet.ncols):
        if column == 1:
            self.data['Time'] = [self.cycle * time for time in sheet.col_values(column, start_rowx=int(self.cut))[1:]]
        else:
            self.data[column-2]['Values'] = sheet.col_values(column, start_rowx=int(self.cut))[1:]


def getDerivatives(self, well) -> []:
    derivative = {1: smooth(np.gradient(self.data[well]['Values']))}
    derivative[2] = np.gradient(derivative[1])
    return derivative


def getPeaks(dindex, derivative) -> []:
    if dindex == 2:  # flip to find the negative peak
        derivative = -derivative
    for proms in range(20, 5, -1):
        for width in range(15, 5, -1):
            peaks, properties = find_peaks(abs(derivative), prominence=proms, width=width)
            if len(peaks) == 2:
                return getPeakBorders(peaks, properties, len(derivative))
    # search more extremes if it doesn't work
    for proms in range(10,1,-1): # (50,10,-1):
        for width in range(5,1,-1): # (8,1,-1):
            peaks, properties = find_peaks(abs(derivative), prominence=proms, width=width)
            if len(peaks) == 2:
                return getPeakBorders(peaks, properties, len(derivative))
    # TODO: what if more than two peaks are found?
    return ['Error finding peaks', 0, 0]


def getPeakBorders(peaks, properties, maxlength):
    widths = getMaxWidth(properties["widths"])
    start = [np.maximum(int(peakstart - width), 1) for peakstart, width in zip(peaks, widths)]
    end = [np.minimum(int(peakend + width), maxlength) for peakend, width in zip(peaks, widths)]
    return [peaks, start, end]


def getMaxWidth(widths) -> []:
    # TODO: use something different then the generic 4
    return np.maximum(widths / 2, 4)


def ind2sub(array_shape, ind):
    ind[ind < 0] = -1
    ind[ind >= array_shape[0]*array_shape[1]] = -1
    rows = (ind.astype('int') / array_shape[1])
    cols = ind % array_shape[1]
    return rows, cols


def square(data):
    return [i ** 2 for i in data]


def fitPolyEquation(timelist, observed):
    polynomial = 2
    coefs = np.polyfit(timelist, observed, polynomial)
    return coefs


def getExpectedValues(self, wellid, xvalue, start, end) -> []:
    polynomialcoefs = fitPolyEquation(self.data['Time'][start:end], self.data[wellid]['Values'][start:end])
    if isinstance(xvalue, float):
        xvalue = [xvalue]
    x2 = square(xvalue)
    ax2 = [polynomialcoefs[0]*x for x in x2]
    bx = [polynomialcoefs[1]*x for x in xvalue]
    prediction = [(a+b+polynomialcoefs[2]) for (a, b) in zip(ax2, bx)]
    return prediction


def smooth(a):
    # a: NumPy 1-D array containing the data to be smoothed
    # WSZ: smoothing window size needs, which must be odd number,
    # as in the original MATLAB implementation
    windowsize = 11
    out0 = np.convolve(a, np.ones(windowsize, dtype=int), 'valid')/windowsize
    r = np.arange(1, windowsize-1,2)
    start = np.cumsum(a[:windowsize-1])[::2]/r
    stop = (np.cumsum(a[:-windowsize:-1])[::2]/r)[::-1]
    return np.concatenate((start, out0, stop))


def saveImage(self, plt, title):
    plt.title(str(self.title + '_' + title), fontsize=14)
    strFile = os.path.join(self.path, title+'.png')
    if os.path.isfile(strFile):
        os.remove(strFile)
    plt.savefig(strFile)
    plt.close()