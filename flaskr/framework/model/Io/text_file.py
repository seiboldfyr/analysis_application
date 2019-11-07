# TODO: Delete

import os
import re

from flask import current_app
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from framework.exception import InvalidArgument


class TextFile():
    FOLDER = 'text'
    ALLOWED_EXTENSION = ['txt']

    file = None

    def __init__(self, file: FileStorage):
        if not self.is_allowed(file.filename):
            raise InvalidArgument('Only txt files are allowed')

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

    def read(self):
        line_count = 0
        self.error_count = 0

        with open(self.get_file_save_path()) as f:
            for line in f:
                line_count += 1
                if not self.is_valid_line(line):
                    self.error_count += 1
                    current_app.logger.warning('invalid line found line: %s' % line_count)
                    continue
                yield re.split(r'\s+', line)

    def save(self):
        self.file.save(self.get_file_save_path())

    def delete(self):
        os.remove(self.get_file_save_path())

    def is_valid_line(self, line) -> bool:
        return re.match(r'^\d+\.?\d+?\s(-?\d+\.?\d+?\s?)+', line) is not None
