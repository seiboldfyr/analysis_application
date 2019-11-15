from flaskr.framework.exception import MethodNotImplemented
from flaskr.framework.model.request.response import Response


class AbstractImporter:
    def execute(self, request, customfileinfo) -> Response:
        raise MethodNotImplemented
