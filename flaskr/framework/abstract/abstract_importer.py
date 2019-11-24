from flaskr.framework.exception import MethodNotImplemented
from flaskr.framework.model.request.response import Response


class AbstractImporter:
    def search(self, info) -> {}:
        raise MethodNotImplemented

    def execute(self, request, name) -> Response:
        raise MethodNotImplemented
