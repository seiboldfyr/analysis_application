from flaskr.framework.exception import MethodNotImplemented
from flaskr.framework.model.request.response import Response


class AbstractProcessor:
    def execute(self) -> Response:
        raise MethodNotImplemented
