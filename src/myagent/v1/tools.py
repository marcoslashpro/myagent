from dataclasses import dataclass, field
from functools import wraps

from typing import Callable


@dataclass(slots=True)
class Tool:
    func: Callable
    name: str
    description: str | None = field(default=None)


def tool(func: Callable):
    def to_tool() -> Tool:
        return Tool(func=func, name=func.__name__, description=func.__doc__)

    return to_tool()
