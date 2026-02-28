from dataclasses import dataclass, field
from functools import wraps

from pathlib import Path
from typing import Callable
from warnings import warn

from myagent.v1.errors import InvalidToolMountError
from myagent.v1._types import Ro, Rw


@dataclass(slots=True)
class BaseTool[ModeT]:
    path: Path
    mode: ModeT

    def __post_init__(self):
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


@dataclass(slots=True)
class AgentTool(BaseTool[Rw]):
    path: Path
    mode: Rw = field(default='rw')


@dataclass(slots=True)
class UserTool(BaseTool[Ro]):
    path: Path
    mode: Ro = field(default='ro')


TOOL_FORMATTING_INSTRUCTIONS = (
    "tool_name/\n"
    "   |-README.md  # instructions for the agent on how to use the tool\n"
    "   |-launch.sh  # bash script to use the tool, can take any n. of args\n"
    "   |-...        # any other needed files and directory (optional)"
)


Tool = AgentTool | UserTool