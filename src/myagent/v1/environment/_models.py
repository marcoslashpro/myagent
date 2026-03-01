from dataclasses import dataclass, field
from typing import Literal
from docker.models.images import Image


Ro = Literal["ro"]
Rw = Literal["rw"]
RoOrRw = Literal[Ro, Rw]


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


Volumes = dict[str, dict[Literal["bind", "mode"], str]]


@dataclass(slots=True)
class AllVolumes:
    user_tools: Volumes
    agent_tools: Volumes
    docs: Volumes

    def to_docker_volumes(self) -> dict:
        return {**self.docs, **self.agent_tools, **self.user_tools}
