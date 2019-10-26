import xlsxwriter
import os
from datetime import date

from framework.abstract.abstract_processor import AbstractProcessor


class WriteMetadata(AbstractProcessor):
    def __init__(self, path='', data=None, version=None):
        self.path = path
        self.data = data
        self.version = version

    def execute(self):
        path = os.path.join(self.path, self.version)
        try:
            os.mkdir(path)
        except OSError:
            increment = self.getPreExistingOutputNumber()
            path = self.version + '_' + str(increment)
            try:
                path = os.path.join(self.path, path)
                os.mkdir(path)
            except OSError:
                pass

        path = os.path.join(path, 'metadata.txt')
        with open(path, 'w') as f:
            f.write("Fyr Diagnostics Data Analysis")
            f.write('\n')
            f.write("Program Version: ")
            f.write(self.version)
            f.write('\n')
            f.write(str(date.today().strftime("%B %d, %Y")))
            f.write('\n')
            f.write('\n')
            for item in self.data.keys():
                if item == 'Run':
                    continue
                line = str(item) + ': ' + str(self.data[item]) + '\n'
                f.write(line)
        return

    def getPreExistingOutputNumber(self):
        for file in os.listdir(self.path):
            if file.startswith(self.version):
                fileend = file.split('_')[-1]
                if fileend[0] != 'v':
                    return float(fileend) + 1
                return 0
        return 0
