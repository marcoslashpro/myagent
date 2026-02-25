from dataclasses import dataclass, field
from functools import wraps

from pathlib import Path
from typing import Callable
from warnings import warn

from myagent.v1.errors import InvalidToolMountError


@dataclass(slots=True)
class Tool:
    func: Callable
    name: str
    description: str | None = field(default=None)


def tool(func: Callable):
    def to_tool() -> Tool:
        return Tool(func=func, name=func.__name__, description=func.__doc__)

    return to_tool()


TOOL_FORMATTING_INSTRUCTIONS = (
    "Please provide a tool directory like this:\n"
    "tool_name/\n"
    "   |-README.md  # instructions for the agent on how to use the tool\n"
    "   |-launch.sh  # bash script to use the tool, can take any n. of args\n"
    "   |-...        # any other needed files and directory (optional)"
)


def validate_tool(tool_path: Path):
    if not tool_path.is_dir():
        raise InvalidToolMountError(
            msg=(
                "The provided tool is not a directory.\n"
                f"{TOOL_FORMATTING_INSTRUCTIONS}"
            )
        )
    if not tool_path.joinpath("README.md").exists():
        warn(
            "[WARNING] - Missing description for the tool: "
            f"{tool_path.name}, the agent will not "
            "be able to easily infer how to use said tool. I suggest "
            "to always provide one, and to keep it under ~200/300 tokens.\n"
            "TIP: Try formatting your tools like this:\n"
            f"{TOOL_FORMATTING_INSTRUCTIONS}"
        )
    if not tool_path.joinpath("launch.sh").exists():
        raise InvalidToolMountError(
            msg=(
                "Missing execution file in the tool directory.\n"
                f"{TOOL_FORMATTING_INSTRUCTIONS}"
            )
        )
