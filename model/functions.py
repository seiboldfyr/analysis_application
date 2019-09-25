from scipy.signal import find_peaks
import numpy as np
import os
import xlrd
import pandas as pd


def calculateCycleLength(self):
    if self.cycle == 0:
        self.cycle = self.length/self.datacount
    for time in self.data['Time']:
        self.data['Time'] = time * self.cycle


def getFilePath(name, path):
    for file in os.listdir(path):
        fileend = name + '.xlsx'
        if file.endswith(fileend):
            name = os.path.join(path, file)
            break
    return name


def getUniqueKeys(keylist):
    indexes = np.unique(keylist, return_index=True)[1]
    return [keylist[value] for value in sorted(indexes)]


def getTriplicateKeys(self) -> {}:
    labeldict = {}
    labelraw = pd.ExcelFile(self.path)
    labelsheet = labelraw.parse('0')
    label = labelsheet.values
    triplicates = np.asarray(getUniqueKeys(label[:, 17]))
    for label, position in enumerate(triplicates):
        self.data[label] = [[position] for i in range(3)]
        labeldict[position] = label
    return labeldict


def getTriplicateValues(self, labeldict):
    wb = xlrd.open_workbook(self.path)
    sheet = wb.sheet_by_name('SYBR')
    for column in range(0, sheet.ncols):
        if column == 0:
            wellLabel = 'Time'
            calculateCycleLength()
        else:
            wellLabel = labeldict[column] # TODO: confirm that all columns and time are collected
        self.data[wellLabel] = sheet.col_values(column, start_rowx=self.cut)


def getDerivatives(self) -> []:
    derivative = {}
    derivative[1] = smooth(np.gradient(self.data[:]))
    derivative[2] = np.gradient(derivative[1])
    return derivative


def getPeaks(derivative, includenegative) -> []:
    if includenegative:  # flip to find the negative peak
        derivativeline = -derivative

    for width in range(8, 1, -1):
        for proms in range(50, 10, -1):
            peaks, properties = find_peaks(abs(derivativeline), prominence=proms, width=width)
            if len(peaks) >= 2:
                width = getPeakWidths(np.maximum(properties))
                return [peaks, peaks - width, peaks + width]
    # TODO: what if more than two peaks are found?
    return ['Eror finding peaks', _, _]


def getPeakWidths(properties) -> []:
    # take the width of the peak, divide in half, this is the half width, no smaller than 4 units
    # TODO: use something different then the generic 4
    return np.maximum(properties["widths"] / 2, 4)


def ind2sub(array_shape, ind):
    ind[ind < 0] = -1
    ind[ind >= array_shape[0]*array_shape[1]] = -1
    rows = (ind.astype('int') / array_shape[1])
    cols = ind % array_shape[1]
    return rows, cols


def square(datalist):
    return [i ** 2 for i in datalist]


def fitPolyEquation(timelist, observed):
    polynomial = 2
    coefs = np.polyfit(timelist, observed, polynomial)
    return coefs


def getExpectedValues(self, wellid, timestart, timeend, timecenter) -> []:
    polynomialcoefs = fitPolyEquation(self.data[wellid][timestart:timeend])

    x2 = square(timecenter)
    ax2 = [polynomialcoefs[0]*x for x in x2]
    bx = [polynomialcoefs[1]*x for x in timecenter]
    prediction = [(a+b+polynomialcoefs[2]) for (a, b) in zip(ax2, bx)]
    return prediction


def smooth(a):
    # a: NumPy 1-D array containing the data to be smoothed
    # WSZ: smoothing window size needs, which must be odd number,
    # as in the original MATLAB implementation
    windowsize = 5
    out0 = np.convolve(a, np.ones(windowsize, dtype=int), 'valid')/windowsize
    r = np.arange(1, windowsize-1,2)
    start = np.cumsum(a[:windowsize-1])[::2]/r
    stop = (np.cumsum(a[:-windowsize:-1])[::2]/r)[::-1]
    return np.concatenate((start, out0, stop))
