from framework.exception import MethodNotImplemented
from framework.model.request.response import Response


class AbstractProcessor:
    def execute(self) -> Response:
        raise MethodNotImplemented
