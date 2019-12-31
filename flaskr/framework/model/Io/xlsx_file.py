import os
import pandas as pd

from flask import current_app
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from flaskr.framework.exception import InvalidArgument


class XLSXFile():
    FOLDER = 'excel'
    ALLOWED_EXTENSION = ['xlsx', 'xls']

    file = None

    def __init__(self, file: FileStorage):
        if not self.is_allowed(file.filename):
            raise InvalidArgument('Only xlsx files are allowed')

        if file.filename != secure_filename(file.filename):
            raise InvalidArgument('Unsecure filename provided')

        self.file = file
        self.save()

    def is_allowed(self, filename: str) -> bool:
        allowed = True
        if '.' not in filename:
            allowed = False

        if filename.rsplit('.', 1)[1].lower() not in self.ALLOWED_EXTENSION:
            allowed = False

        return allowed

    def get_file_save_path(self) -> str:
        return os.path.join(current_app.config['UPLOAD_FOLDER'], self.FOLDER, self.file.filename)

    def read(self, sheet: '', userows: bool = False, usecolumns: bool = False):
        self.error_count = 0

        raw = pd.ExcelFile(self.get_file_save_path())
        if sheet == '':
            sheet = raw.sheet_names[0]
        sheetvalues = raw.parse(sheet).values
        [rows, columns] = sheetvalues.shape

        if usecolumns:
            for column in range(columns):
                if column < 2: #Skip the time column
                    continue
                if self.is_invalid_line(sheetvalues[:, column]):
                    current_app.logger.warning('invalid line found for column %s', column)
                    continue

                yield sheetvalues[:, column]

        elif userows:
            for row in range(rows):
                yield sheetvalues[row, :]

    def save(self):
        self.file.save(self.get_file_save_path())

    def delete(self):
        os.remove(self.get_file_save_path())

    def is_invalid_line(self, line) -> bool:
        if pd.isnull(line.any()):
            self.error_count += 1
            return True
        return False
