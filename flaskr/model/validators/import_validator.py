import os

from flaskr.framework.abstract.abstract_validator import AbstractValidator
from flaskr.framework.model.request.response import Response


def checkname(file) -> Response:
    if file.filename == '':
        return Response(False, 'File is required')
    if not file.filename.endswith('.xlsx'):
        return Response(False, 'File has wrong filetype')
    return Response(True)


class ImportValidator(AbstractValidator):

    def execute(self, request) -> Response:
        if request.files is None:
            return Response(False, 'Files are required')
        for f in request.files:
            file = request.files.get(f)
            if file is None:
                return Response(False, 'A file is required')
            print(file)

            if not checkname(file).is_success():
                return Response(False, checkname(file).get_message())
            print('next')

        if request.form['folder'] is None:
            return Response(False, 'Output location is required')

        return Response(True)



