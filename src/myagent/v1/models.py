from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass(slots=True)
class Mount:
    path: Path
    mode: Literal["rw", "ro"]
