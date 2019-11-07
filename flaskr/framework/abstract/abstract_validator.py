from flaskr.framework.exception import MethodNotImplemented
from flaskr.framework.model.request.response import Response


class AbstractValidator:
    def execute(self, request) -> Response:
        raise MethodNotImplemented
