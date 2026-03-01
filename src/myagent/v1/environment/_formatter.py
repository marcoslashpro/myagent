from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING

from myagent.v1.environment._models import ImageMetadata, Volumes

if TYPE_CHECKING:
    from myagent.v1.environment import Docker


def format_env(env: Docker):
    return f"""
```env_info
## Image Metadata:
{format_img_metadata(env.img_metadata)}

## Docs:
{format_docs_dir(env.volumes.docs)}

## Agent Tools:
{format_tools_dir(env.volumes.agent_tools)}

## User Tools:
{format_tools_dir(env.volumes.user_tools)}
```
"""


def format_img_metadata(metadata: ImageMetadata): ...


def format_builtin_tools_dir():
    raise NotImplementedError()


def format_docs_dir(docs: Volumes, level: int = 0):
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
                        formatted += format_docs_dir(
                            {
                                str(local_p / subdir): {
                                    "mode": mode,
                                    "bind": subdir,
                                }
                            },
                            level + 1,
                        )
        else:
            formatted += f"{indent}|-{bind_path}  # {mode}\n"

    return formatted


def format_tools_dir(tools: Volumes) -> str:
    names = []
    indent = "    "
    for local_tool_path in tools.keys():
        names.append(f"{Path(tools[local_tool_path]['bind'])}")

    return f"\n{indent}|-".join(names) + "\n"
