class ModelError(Exception):
    pass


class UserError(Exception):
    pass


class ModelResponseError(ModelError):
    """Exception raised when model response is invalid."""

    pass


class ToolError(ModelError):
    def __init__(self, message: str, tool_name: str) -> None:
        super().__init__(message)
        self.tool_name = tool_name


class InvalidMountError(Exception):
    def __init__(self, msg: str | None = None, path: str | None = None) -> None:
        super().__init__(msg if msg else f"Invalid file path: {path}, does not exists")


class InvalidToolMountError(InvalidMountError):
    def __init__(self, msg: str | None = None, path: str | None = None) -> None:
        super().__init__(
            msg if msg else f"Tool executable not found at path: {path}", path
        )


class DockerSetupError(Exception):
    pass


class InvalidDockerSpecsError(UserError, DockerSetupError):
    pass


class DockerConfigError(DockerSetupError):
    pass


class InvalidDockerFileError(InvalidDockerSpecsError):
    def __init__(self, path: str) -> None:
        super().__init__(f"Dockerfile at path: {path} not found")


class AgentEnvironmentError(Exception):
    pass
