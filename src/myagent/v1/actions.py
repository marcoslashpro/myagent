from dataclasses import dataclass, field
from typing import Literal


@dataclass(slots=True)
class ThinkAction:
    content: str
    type: Literal["think"] = "think"


@dataclass(slots=True)
class CodeAction:
    content: str
    type: Literal["code"]


@dataclass(slots=True)
class FinalAction:
    content: str
    type: Literal["final_answer"] = "final_answer"


@dataclass(slots=True)
class Observation:
    content: str
    type: Literal["observation", "observation_error"]
    status_code: int

    def __repr__(self) -> str:
        return f"""
```observation
{"stdout" if self.type == 'observation' else "stderr"}: {self.content}
exit status: {self.status_code}
```
"""


@dataclass(slots=True)
class AgentAction:
    final_answer: str | None = field(default=None)
    think: str | None = field(default=None)
    code: str | None = field(default=None)
