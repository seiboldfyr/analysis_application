import os
import numpy as np
from flask import current_app, flash
from statistics import mean, stdev

# def getGroupHeaders(triplicateHeaders):
#     headers = []
#     previousgroup = 0
#     for h in triplicateHeaders:
#         if int(h[-1]) > previousgroup:
#             headers.append(h[7:])
#             previousgroup = int(h[-1])
#     return headers


def get_unique(keylist):
    indexes = np.unique(keylist, return_index=True)[1]
    return [keylist[value] for value in sorted(indexes)]


# def getTriplicateKeys(self, path, inputinfo) -> {}:
#     labelraw = pd.ExcelFile(path)
#     labelsheet = labelraw.parse('0')
#     label = labelsheet.values
#     if len(inputinfo) == 0:
#         control = label[0, 5]
#         group = 1
#         prevrow = 0
#         triplicate = -1
#         previoussample = ''
#         for row in range(0, len(label[:, 1])):
#             usedrow = row
#             if label[row, 5] == control and row > 6 and row > prevrow + 6:
#                 group += 1
#                 prevrow = row
#             if label[row, 1] in self.swaps.keys():
#                 usedrow = replacementIndex(self, row, label[:, 1])
#             sample = str(label[usedrow, 5]) + '_' + str(label[usedrow, 6])
#             header = sample + '_' + str(group)
#             triplicate = getTriplicateNumber(triplicate, sample, previoussample)
#             previoussample = sample
#             addHeader(self, usedrow, header, label[usedrow, 1], group, triplicate, sample)
#     else:
#         row = 0
#         triplicate = -1
#         previoussample = ''
#         for group in inputinfo.keys():
#             groupsize = float(inputinfo[group]['Group Wells']) * float(inputinfo[group]['Group Samples'])
#             if groupsize % 1 != 0:
#                 flash('possible error with wells/samples', 'error')  # TODO: validator
#             grouplabel = inputinfo[group]['Group Label']
#             for well in range(int(groupsize)):
#                 row += 1
#                 usedrow = row
#                 if label[row, 1] in self.swaps.keys():
#                     usedrow = replacementIndex(self, row, label[:, 1])
#                 if row > len(label[:, 1]):
#                     flash('The wells and samples added up to be more than the % s wells' % len(label[:, 1]), 'error')
#                 sample = str(label[usedrow, 5]) + '_' + str(label[usedrow, 6])
#                 header = sample + '_' + grouplabel + '_' + str(group)
#                 triplicate = getTriplicateNumber(triplicate, sample, previoussample)
#                 previoussample = sample
#                 addHeader(self, usedrow, header, label[usedrow, 1], group, triplicate, sample)


# def getTriplicateNumber(triplicate, sample, previoussample):
#     if sample != previoussample:
#         return triplicate + 1
#     return triplicate


# def replacementIndex(self, row, labels):
#     fromLabel = labels[row]
#     for searchidx, search in enumerate(labels):
#         if search == self.swaps[fromLabel]['To']:
#             return searchidx

#
# def addHeader(self, row, header, excelindex, group, triplicate, sample):
#     self.data[row] = {'Label': header, 'ExcelHeader': excelindex, 'Group': group, 'Triplicate': triplicate,
#                       'Sample': sample, 'Values': []}


# def ind2sub(array_shape, ind):
#     ind[ind < 0] = -1
#     ind[ind >= array_shape[0]*array_shape[1]] = -1
#     rows = (ind.astype('int') / array_shape[1])
#     cols = ind % array_shape[1]
#     return rows, cols


def saveImage(self, plt, figuretitle):
    title = os.path.split(self.path)[1][:13] + '_' + self.customtitle
    title = str(title + '_' + figuretitle)
    plt.title(title, fontsize=14)
    path = os.path.join(self.path, 'Graphs')
    strFile = os.path.join(path, title+'.png')
    if os.path.isfile(strFile):
        os.remove(strFile)
    plt.savefig(strFile)
    plt.close()


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