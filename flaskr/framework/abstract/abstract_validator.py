from framework.exception import MethodNotImplemented
from framework.model.request.response import Response


class AbstractValidator:
    def execute(self, request) -> Response:
        raise MethodNotImplemented
