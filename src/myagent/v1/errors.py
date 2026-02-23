class ModelError(Exception):
    pass


class ModelResponseError(ModelError):
    """Exception raised when model response is invalid."""

    pass


class ToolError(ModelError):
    def __init__(self, message: str, tool_name: str) -> None:
        super().__init__(message)
        self.tool_name = tool_name


class InvalidMountError(Exception):
    def __init__(self, path: str) -> None:
        super().__init__(f"Invalid file path: {path}, does not exists")
