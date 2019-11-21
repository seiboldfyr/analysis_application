import numpy as np

#
# def writeSheet(workbook, name, labels, data):
#     datasheet = workbook.add_worksheet(name)
#
#     # TODO: get labels from info file here?
#     writeHeadersToSheet(labels, datasheet)
#     writeDataToSheet(data, datasheet)
#     return workbook


# def writeDataToSheet(data, sheet):
#     for col in range(data.shape[1]):
#         for row in range(data.shape[0]):
#             sheet.write(row+1, col, data[row, col])
#     return sheet
#
#
# def writeHeadersToSheet(headers, sheet):
#     for i in range(len(headers)):
#         sheet.write(0, i+3, headers[i])
#         setHeaderWidth(headers[i])
#     return sheet
#
#
# def setHeaderWidth(self, header):
#     width = len(header)
#     self.datasheet.set_column(0, 0, width)


def addTimeMeasurements(sheet, time) -> []:
    labels = ['Cycle', 'Time (Sec)', 'Time (Min)']
    sheet.write(0, 0, labels[0])
    sheet.write(0, 1, labels[1])
    sheet.write(0, 2, labels[2])
    for t in range(len(time)):
        sheet.write(t + 1, 0, time[t] / 60)
        sheet.write(t + 1, 1, time[t])
        sheet.write(t + 1, 2, time[t] / 27)
    return sheet

# def addTimeMeasurements(time) -> []:
#     labels = ['Cycle', 'Time (Sec)', 'Time (Min)']
#
#     data = np.concatenate((np.array(time/60)[:, np.newaxis], data), axis=1)
#     data = np.concatenate((np.array(time)[:, np.newaxis], data), axis=1)
#     data = np.concatenate((np.array(time/27)[:, np.newaxis], data), axis=1)
#     return data


# def averageTriplicates(data, label):
#     tripavgs = np.empty((data.shape[0], int(data.shape[1] / 3)))  # todo: can we initialize without hardcoding the 3?
#     for well in range(data.shape[1]):
#         triplicatename = label[well]
#         TotalInTriplicate = 0
#         while label[well+TotalInTriplicate] == triplicatename:
#             TotalInTriplicate += 1
#         tripavgs[:, well] = np.nanmean([data[well, trip] for trip in range(TotalInTriplicate)])