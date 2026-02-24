from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Mapping


@dataclass(slots=True)
class Mount:
    path: Path
    mode: Literal["rw", "ro"]


Volumes = dict[str, dict[Literal["bind", "mode"], str]]
