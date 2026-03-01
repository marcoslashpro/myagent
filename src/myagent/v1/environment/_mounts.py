from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal
from warnings import warn

from myagent.v1.errors import InvalidMountError, InvalidToolMountError
from myagent.v1.environment._models import Volumes, Ro, RoOrRw, Rw


@dataclass(slots=True)
class MountProtocol[ModeT](ABC):
    path: Path
    mode: ModeT

    def __post_init__(self):
        if not self.path.expanduser().exists():
            raise InvalidMountError(path=str(self.path))
        self._validate()

    def _validate(self) -> None:
        """
        Optional function to implement, called in `__post_init__`,
        to perform checks on the instance attributes
        """

    @abstractmethod
    def to_volumes(self, root_mnt_dir: str) -> Volumes: ...


@dataclass(slots=True)
class Mount(MountProtocol[RoOrRw]):
    def to_volumes(self, root_mnt_dir: str) -> Volumes:
        return {
            str(self.path): {
                "bind": f"{root_mnt_dir}/{self.path.name}",
                "mode": self.mode,
            }
        }


TOOL_FORMATTING_INSTRUCTIONS = (
    "tool_name/\n"
    "   |-README.md  # instructions for the agent on how to use the tool\n"
    "   |-launch.sh  # bash script to use the tool, can take any n. of args\n"
    "   |-...        # any other needed files and directory (optional)"
)


@dataclass(slots=True)
class BaseTool[ModeT: RoOrRw, DirT: Literal["agent", "user"]](MountProtocol[ModeT]):
    bind_dir_name: DirT

    def _validate(self):
        if not self.path or not isinstance(self.path, Path) or not self.path.is_dir():
            raise InvalidToolMountError(
                msg=(
                    "The provided tool is not a directory.\n"
                    "Please provide a tool directory like this:\n"
                    f"{TOOL_FORMATTING_INSTRUCTIONS}"
                )
            )

        if not self.path.joinpath("README.md").exists():
            warn(
                "[WARNING] - Missing description for the tool: "
                f"{self.path.name}, the agent will not "
                "be able to easily infer how to use said tool. I suggest "
                "to always provide one, and to keep it under ~200/300 tokens.\n"
                "TIP: Try formatting your tools like this:\n"
                f"{TOOL_FORMATTING_INSTRUCTIONS}"
            )

        if not self.path.joinpath("launch.sh").exists():
            raise InvalidToolMountError(
                msg=(
                    "Missing execution file in the tool directory.\n"
                    "Please provide a tool directory like this:\n"
                    f"{TOOL_FORMATTING_INSTRUCTIONS}"
                )
            )

    def to_volumes(self, root_mnt_dir: str) -> Volumes:
        return {
            str(self.path): {
                "bind": f"{root_mnt_dir}/{self.bind_dir_name}/{self.path.name}",
                "mode": self.mode,
            }
        }


@dataclass(slots=True)
class AgentTool(BaseTool[Rw, Literal["agent"]]):
    path: Path
    mode: Rw = field(default="rw")
    bind_dir_name: Literal["agent"] = "agent"


@dataclass(slots=True)
class UserTool(BaseTool[Ro, Literal["user"]]):
    path: Path
    mode: Ro = field(default="ro")
    bind_dir_name: Literal["user"] = "user"


Tool = UserTool | AgentTool
