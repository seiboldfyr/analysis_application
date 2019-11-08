import xlsxwriter
import os
from flask import current_app
from datetime import date

from flaskr.framework.abstract.abstract_processor import AbstractProcessor


class WriteMetadata(AbstractProcessor):
    def __init__(self, path='', data=None):
        self.path = path
        self.data = data

    def execute(self):
        path = os.path.join(self.path, str('output_v' + current_app.config['VERSION']))
        try:
            os.mkdir(path)
        except OSError:
            increment = self.getPreExistingOutputNumber()
            path = 'output_v' + current_app.config['VERSION'] + '_' + str(increment)
            try:
                path = os.path.join(self.path, path)
                os.mkdir(path)
            except OSError:
                pass

        with open(os.path.join(path, 'metadata.txt'), 'w') as f:
            f.write("Fyr Diagnostics Data Analysis")
            f.write('\n')
            f.write("Program Version: ")
            f.write(current_app.config['VERSION'])
            f.write('\n')
            f.write(str(date.today().strftime("%B %d, %Y")))
            f.write('\n')
            f.write('\n')
            for item in self.data.keys():
                if item == 'Run':
                    continue
                line = str(item) + ': ' + str(self.data[item]) + '\n'
                f.write(line)
        return path

    def getPreExistingOutputNumber(self):
        increment = 0
        for file in os.listdir(self.path):
            if file.startswith(current_app.config['VERSION']):
                fileend = file.split('_')[-1]
                if fileend[0] != 'v':
                    increment = max(float(fileend) + 1, increment)
        return int(increment)
