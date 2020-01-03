import os
import numpy as np
from flask import current_app
from statistics import mean, stdev


def get_unique(keylist):
    indexes = np.unique(keylist, return_index=True)[1]
    return [list(keylist)[value] for value in sorted(indexes)]


def get_unique_name(keylist):
    indexes = np.unique(keylist, return_index=False)
    return indexes


def get_unique_group(keylist):
    temp = [item[-1] for item in keylist]
    index = np.unique(temp, return_index=True)[1]
    return [keylist[k] for k in index]


def saveImage(self, plt, figuretitle):
    #TODO: include manually built label here
    plt.title(figuretitle, fontsize=14)
    path = os.path.join(current_app.config['IMAGE_FOLDER'], 'graphs')
    strFile = os.path.join(path, figuretitle + ".png")
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