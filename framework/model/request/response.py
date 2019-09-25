class Response(dict):
    def __init__(self, success: bool = False, message: str = ''):
        self.message = message
        self.success = success
        super().__init__(self, message=message, success=success)

    def get_message(self) -> str:
        return self.message

    def is_success(self) -> bool:
        return self.success
