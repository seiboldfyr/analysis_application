import xlsxwriter
import os
from filewriter.helper import addTimeMeasurements


class Writer:
    def __init__(
            self,
            data: {} = None):
        self.data = data
        self.workbook = None

    def writebook(self, path):
        self.workbook = xlsxwriter.Workbook(os.path.join(path, 'OutputData.xlsx'), {'nan_inf_to_errors': True})
        self.writeInflectionData()
        # TODO: write average inflections
        self.writeRawData()
        # TODO: write average raw data
        # TODO: write corrected data
        self.workbook.close()


    def writeInflectionData(self):
        sheet = self.workbook.add_worksheet('Inflections')
        for row, label in enumerate(createLabels()):
            sheet.write(0, row + 1, label)

        for row, key in enumerate(self.data.keys()):
            col = 0
            sheet.write(row + 1, col, self.data[key]['Label'])
            for inflection in self.data[key]['Inflections']:
                col += 1
                sheet.write(row, col, inflection)
            for rfu in self.data[key]['RFUs']:
                col += 1
                sheet.write(row, col, rfu[0])
            if not self.data[key].get['Relative Difference']:
                continue
            for reldiff in self.data[key]['Relative Difference'][1]:
                col += 1
                sheet.write(row, col, reldiff)

    def writeRawData(self):
        sheet = self.workbook.add_worksheet('Raw RFU')
        sheet = addTimeMeasurements(sheet, self.data['Time'])
        for col, key in enumerate(self.data.keys()):
            if key == 'Time':
                continue
            row = 0
            sheet.write(row, col, self.data[key]['Label'])  # header
            for value in self.data[key]['Values']:
                row += 1
                sheet.write(row, col, value)


def createLabels():
    label = ['Inflection 1', 'Inflection 2', 'Inflection 3', 'Inflection 4']
    label.extend(['RFU 1', 'RFU 2', 'RFU 3', 'RFU 4'])
    # label.extend(['Percent Difference from Control'])
    return label



# label = ['Inflection 1 avg','Inflection 1 std','Inflection 2 avg','Inflection 2 std']
# label.extend(['Inflection 3 avg','Inflection 3 std','Inflection 4 avg','Inflection 4 std'])
# label.extend(['RFU 1 avg','RFU 1 std','RFU 2 avg','RFU 2 std'])
# label.extend(['RFU 3 avg','RFU 3 std','RFU 4 avg','RFU 4 std'])
# label.extend(['Diff 1 to 3 avg','Diff 1 to 3 std','Diff 2 to 4 avg','Diff 2 to 4 std'])
# label.extend(['Max slope phase 1 (avg RFU/min)','Max slope phase 1 (std RFU/min)'])
# label.extend(['Max slope phase 2 (avg RFU/min)','Max phase slope 2 (std RFU/min)'])
#
#
# worksheet = workbook.add_worksheet('Mean Inflections')
# col,r = (0 for i in range(2))
# previousgroup = 0
# for trip in Triplicates: #each triplicate
#     if not trip in GroupResult[:,1]:
#         continue
#     j = np.where(GroupResult[:,1] == trip)[0][0]
#     if GroupResult[j,0]==0:
#         continue
#     group = GroupResult[j,0]
#     r = int(group-1) * (nVars*2+2)
#     group = GroupResult[j,0]
#     if j > 0 and group != previousgroup:
#         col = 0
#         previousgroup = group
#     col += 1
#     for var in range(nVars*2):
#         if var == 0: #Well labels only need to be written in first row once
#             worksheet.write(r,col,triplicateHeaders[j])
#         r += 1
#         if col == 1: #Variable labels only need to be written in first column once
#             worksheet.write(r, col-1, label[var])
#         worksheet.write(r,col,GroupResult[j,var+4]) #Variable value
# width= np.max([len(i) for i in label])
# worksheet.set_column(0, 0, width)
#
# workbook = writeSheet(workbook,'Corr RFU',header,cycle,times,dataconv)
# workbook = writeSheet(workbook,'Raw RFU',header,cycle,times,data)
# dataAverages = averageTriplicates(data,Triplicates,IndResult[:,1])
# workbook = writeSheet(workbook,'Raw RFU avgs',triplicateHeaders,cycle,times,dataAverages)
#
#
# worksheet = workbook.add_worksheet('Percent Diffs')
# worksheet.write(0,0,'Triplicate')
# worksheet.write(0,1,'Inflection 1 (% Difference)')
# worksheet.write(0,2,'Inflection 2 (% Difference)')
# worksheet.write(0,3,'Inflection 3 (% Difference)')
# worksheet.write(0,4,'Inflection 4 (% Difference)')
# for inflectionIndex in range(1,5):
#     inflectionIndex = int(inflectionIndex)
#     row = 1
#     for triplicate in Triplicates:
#         triplicate = int(triplicate)
#         worksheet.write(row,0,triplicateHeaders[triplicate])
#         width = len(triplicateHeaders[triplicate])
#         worksheet.set_column(row, 0, width)
#         worksheet.write(row,inflectionIndex,RelDiffs[inflectionIndex][triplicate])
#         row += 1
#
# workbook.close()
