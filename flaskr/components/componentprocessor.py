from flask import flash

from flaskr.components.component_models.factory import Factory
from flaskr.components.component_models.repository import Repository
from flaskr.framework.exception import InvalidArgument
from flaskr.framework.model.Io.xlsx_file import XLSXFile
from flaskr.framework.model.request.response import Response


def search(name, unit) -> {}:
    if Repository().search_by_name_and_unit(name, unit) is None:
        flash('A component with name %s and unit %s already exists' % (name, unit), 'error')
        return False
    return True


class ImportComponents:

    def execute(self, request) -> Response:
        component_repository = Repository()
        factory = Factory()

        for f in request.files:
            file = request.files.get(f)
            try:
                xlsx_file = XLSXFile(file)
            except InvalidArgument:
                return Response(False, 'An invalid file was provided, please make sure you are uploading a .xlsx file')

        for row in xlsx_file.read(sheet='', userows=True):
            if not search(row[1], row[2]):
                continue
            model = factory.create({'type': row[0], 'name': row[1], 'unit': row[2]})
            component_repository.save(model)

        xlsx_file.delete()

        return Response(True, 'File imported successfully')

