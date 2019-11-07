import numpy as np
import os
from flask import flash, current_app

from framework.abstract.abstract_opener import AbstractOpener


class OpenFile(AbstractOpener):
    def __init__(self, path: str = ''):
        self.path = path
        self.filepaths = {}
        self.data = {}

    def execute(self) -> []:
        files = ['RFU', 'INFO', 'Metadata']
        for file in files:
            filepath = self.getFile(file)
            if filepath != '':
                self.setFileData(filepath)
            else:
                if file == 'Metadata':
                    flash('A pre-existing metadata file was not found.')
                else:
                    flash('% s file could not be found' % file)
            self.filepaths[file] = filepath
        return self

    def setFileData(self, filepath):
        basename = os.path.basename(filepath)
        self.data['Date'] = basename[:8]
        self.data['Id'] = basename[8]
        self.data['Initials'] = basename[10:12]

    def getFile(self, filetype) -> str:
        for file in os.listdir(self.path):
            fileend = filetype + '.xlsx'
            if file.endswith(fileend):
                name = os.path.join(self.path, file)
                return name
        return ''


