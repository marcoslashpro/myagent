from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from docker import DockerClient
from docker.models.images import Image

from myagent.v1.types import RoOrRw


@dataclass(slots=True)
class Mount:
    path: Path
    mode: RoOrRw


@dataclass(slots=True)
class ImageMetadata:
    base_img: str | None
    description: str | None
    shell: str = field(default="/bin/sh")

    @classmethod
    def from_img(cls, img: Image) -> "ImageMetadata":
        labels = img.attrs["Config"].get("Labels", {})
        return cls(
            shell=labels.get("agent.shell", "/bin/sh"),
            description=labels.get("agent.description"),
            base_img=labels.get("agent.base_img"),
        )

    def __repr__(self) -> str:
        return f"""
Default Shell: {self.shell}\n
Base img: {self.base_img if self.base_img else "NOT PROVIDED"}\n
Description: {self.description if self.description else "NOT PROVIDED"}\n
"""


@dataclass(slots=True)
class DockerSpecs:
    local_dockerfile: Path | None = field(default=None)
    remote_repo: str | None = field(default=None)


Volumes = dict[str, dict[Literal["bind", "mode"], str]]
