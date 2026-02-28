from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from docker import DockerClient
from docker.models.images import Image

from myagent.v1._types import RoOrRw


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
    img_tag: str = field(default="agent-env:latest")


Volumes = dict[str, dict[Literal["bind", "mode"], str]]


@dataclass(slots=True)
class AllVolumes:
    user_tools: Volumes
    agent_tools: Volumes
    docs: Volumes

    def render_for_sys_prompt(self) -> str:
        return f"""
```bash
/mnt/
  {self._format_docs_for_sys_prompt(self.docs)}
  {self._format_tools_for_sys_prompt(self.agent_tools)}
  {self._format_tools_for_sys_prompt(self.user_tools)}
```
"""

    def to_docker_volumes(self) -> dict:
        return {**self.docs, **self.agent_tools, **self.user_tools}

    @staticmethod
    def _format_docs_for_sys_prompt(docs: Volumes, level: int = 0):
        formatted = ""
        indent = "   " * level

        for mnt in docs.keys():
            local_p = Path(mnt)
            bind_path = docs[mnt]["bind"]
            mode = docs[mnt]["mode"]

            if local_p.is_dir():
                formatted += f"{indent}|-{bind_path}/  # {mode}\n"

                for _, subdirs, filenames in local_p.walk():
                    for file in filenames:
                        file_indent = "   " * (level + 1)
                        formatted += f"{file_indent}|-{file}  # {mode}\n"

                    if subdirs:
                        for subdir in subdirs:
                            formatted += AllVolumes._format_docs_for_sys_prompt(
                                {
                                    str(local_p / subdir): {
                                        "mode": mode,
                                        "bind": subdir,
                                    }
                                },
                                level + 1,
                            )
                    break
            else:
                formatted += f"{indent}|-{bind_path}  # {mode}\n"

        return formatted

    @staticmethod
    def _format_tools_for_sys_prompt(tools: Volumes) -> str:
        names = []
        indent = "    "
        for local_tool_path in tools.keys():
            names.append(f"{Path(tools[local_tool_path]['bind'])}")

        return f"\n{indent}|-".join(names) + "\n"
