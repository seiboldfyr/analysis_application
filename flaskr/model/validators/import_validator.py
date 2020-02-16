
from flaskr.framework.abstract.abstract_validator import AbstractValidator
from flaskr.framework.model.request.response import Response


class ImportValidator(AbstractValidator):

    def execute(self, request) -> Response:
        if request.form['Select'] != 'Select':
            return Response(True, '')

        if request.form.get('delete') and request.form['Select'] == 'Select':
            return Response(False, 'No dataset selected')

        if request.files is None:
            return Response(False, 'Files are required')

        for file in request.files.values():
            if file is None or file.filename == '':
                return Response(False, 'A file is required')

            if not file.filename.endswith('.xlsx'):
                return Response(False, 'The file has an incorrect filetype')

        return Response(True, '')




