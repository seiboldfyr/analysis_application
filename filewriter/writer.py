import xlsxwriter
import numpy as np
from filewriter.helper import addTimeMeasurements, averageTriplicates, buildInflectionData
import filewriter.sheetwriter as writeSheet

################### UNFINISHED ########################


class WriteToOutput:
    def __init__(
            self,
            original_data: [] = None,
            processed_data: [] = None ):
        self.original = original_data
        self.processed = processed_data
        self.rebuilt = {}

    def writebook(self, path, sheet, data, analysisdata, time, variablelabels, originallabels):
        workbook = xlsxwriter.Workbook(path + '_AnalysisOutput.xlsx')

        processed_output = buildInflectionData(self.processed)
        workbook = writeSheet(workbook, 'Inflections', originallabels, processed_output)

        original_output = addTimeMeasurements(self.original, variablelabels, time)
        workbook = writeSheet(workbook, 'Raw RFU', variablelabels, original_output)

        original_averaged_output = averageTriplicates(data, originallabels)
        workbook = writeSheet(workbook, 'Raw RFU avgs', time, original_averaged_output)

        workbook.close()

    def buildInflectionData(self, header):

        lastheader = ''
        g = -1
        individualresult = {}  # np.empty((wellcount, 14))
        triplicateresult = {}  # np.zeros((int(wellcount / 3), 26))

        # for wellID in self.data.keys():
        # # Retrieve experiment number from label
            # if lastheader != header[i]:
            #     g += 1
            # exp = int(header[i][-2:].replace('_', ''))
            # lastheader = header[i]

            # # each row is an individual well, the first column is the triplicate #, the second is the experiment #,
            # # following columns are the parameters
            # individualresult[i, :3] = [header[i], g, exp]
            # individualresult[i, 3:7] = [x / 60 for x in inflectionpoint[:, i]]  # time of inflection points 1 thru 4
            # individualresult[i, 7:11] = [x for x in inflectionrfu[:, i]]  # RFU of inflection points 1 through 4
            # individualresult[i, 11] = (inflectionpoint[2, i] - inflectionpoint[0, i]) / 60  # diff of inf 1 and 3
            # individualresult[i, 12] = (inflectionpoint[3, i] - inflectionpoint[1, i]) / 60  # diff of inf 2 and 4
            # individualresult[i, 13:] = [x / 60 for x in maxderivatives[:, i]]  # max derivative of derivatives

        # each row is a triplicate, each column is a variable, avg is listed, then std
        triplicates = np.unique(individualresult[:, 0])
        for trip in triplicates:
            col = 0
            for variable in range(len(individualresult[0, :])):
                triplicatevars = [k for j, k in enumerate(individualresult[:, variable])
                                  if individualresult[j, 0] == int(trip)]
                if variable < 2:
                    triplicateresult[int(trip), col] = triplicatevars[0]
                    col += 1
                else:
                    triplicateresult[int(trip), col] = np.nanmean(triplicatevars)
                    col += 1
                    triplicateresult[int(trip), col] = np.nanstd(triplicatevars)
                    col += 1







        # output_data = data.deepcopy
        # numberofvariables = len(data[0, 3:])
        # col = 0
        # row = 0
        # for well in range(data.shape[0]):
        #     row += 1
        #     r = int(data[well, 1] - 1) * (numberofvariables + 2)
        #     if data[well, 1] != data[well - 1, 1] and well > 0:
        #         col = 0
        #     col += 1
        #     for var in range(numberofvariables):
        #         if var == 0:  # Well labels only need to be written in first row once
        #             output_data[r, col] = data[well, 0]
        #         r += 1
        #         # if col == 1:  # Variable labels only need to be written in first column once
        #             # output_data[r, 0] = variablelabels[var]
        #         output_data[r, col] = data[well, var + 2]  # Variable value


