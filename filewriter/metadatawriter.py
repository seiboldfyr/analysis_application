import xlsxwriter
from framework.abstract.abstract_workbook import AbstractWorkbook


class WriteMetadata(AbstractWorkbook):
    def __init__(
            self,
            path='',
            data=None):
        self.path = path
        self.data = data

    def execute(self):
        with open(self.path + '_metadata.txt', 'w') as f:
            for element in self.data.keys():
                f.write(element)
        return

