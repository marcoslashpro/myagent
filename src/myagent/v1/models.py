from dataclasses import dataclass
from pathlib import Path
from typing import Literal


RoOrRw = Literal["ro", "rw"]


@dataclass(slots=True)
class Mount:
    path: Path
    mode: RoOrRw


Volumes = dict[str, dict[Literal["bind", "mode"], str]]
