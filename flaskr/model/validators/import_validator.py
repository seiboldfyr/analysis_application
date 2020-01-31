
from flaskr.framework.abstract.abstract_validator import AbstractValidator
from flaskr.framework.model.request.response import Response


class ImportValidator(AbstractValidator):

    def execute(self, request) -> Response:
        if request.files is None:
            return Response(False, 'Files are required')

        for file in request.files.values():
            if file is None or file.filename == '':
                return Response(False, 'A file is required')

            if not file.filename.endswith('.xlsx'):
                return Response(False, 'The file has an incorrect filetype')

        return Response(True, '')

    def units(self, request) -> Response:
        return Response(True, '')
        # check if units are legitimate for the found component
        # and check if quantity is non-zero
        # and check that a target, linear template, reporter template, and reagents are uploaded


