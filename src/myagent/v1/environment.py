from pathlib import Path

from docker import DockerClient
import docker.errors
from docker.models.containers import Container

from myagent.core.messages import Message, SystemMessage
from myagent.v1.errors import InvalidMountError
from myagent.v1.models import Mount, Volumes


class Docker:
    _mnt_dir = "/mnt"
    _sys_prompt_path = Path(__file__).parent.parent / "prompts/docker_agent_sys.txt"
    _artifacts_path = Path("~/.artifacts").expanduser()

    def __init__(
        self,
        mounts: list[Mount],
        messages: list[Message] | None = None,
        client: DockerClient | None = None,
    ):
        self.client = client or DockerClient.from_env()

        self._container: None | Container = None
        self._volumes: Volumes = self._bind_mounts(self._add_artifacts(mounts))

        self.messages: list[Message] = messages or [self._generate_sys_prompt()]

    def _add_artifacts(self, mounts: list[Mount]) -> list[Mount]:
        self._artifacts_path.mkdir(exist_ok=True)
        mounts.append(Mount(self._artifacts_path, mode="rw"))
        return mounts

    def _bind_mounts(self, mounts: list[Mount]) -> Volumes:
        volumes: Volumes = {}

        for mount in mounts:
            if not mount.path.expanduser().exists():
                raise InvalidMountError(str(mount.path))
            volumes[str(mount.path.expanduser())] = {
                "bind": f"{self._mnt_dir}/{mount.path.name}",
                "mode": mount.mode,
            }
        return volumes

    def _generate_sys_prompt(self) -> SystemMessage:
        sys_prompt = self._sys_prompt_path.read_text()
        sys_prompt = (
            sys_prompt.replace(
                "{{FILES}}",
                f"```bash\n{_format_volumes_for_sys_prompt(self._volumes)}\n```",
            )
            .replace("{{MNT_DIR}}", self._mnt_dir)
            .replace("{{ARTIFACTS_DIR}}", self._artifacts_path.name)
        )
        return SystemMessage(content=sys_prompt)

    def run(self, cmd: str):
        try:
            return self.client.containers.run(
                "python:3.12-slim",
                command=["sh", "-c", cmd],
                volumes=self._volumes,  # pyright: ignore[reportArgumentType]
                auto_remove=True,
                stdout=True,
                stderr=True,
            ).decode()
        except docker.errors.APIError as e:
            return e.explanation if e.explanation else str(e)
        except docker.errors.ContainerError as e:
            return str(e)


def _format_volumes_for_sys_prompt(volumes: dict, level: int = 0):
    formatted = ""
    indent = "   " * level

    for mnt in volumes.keys():
        local_p = Path(mnt)
        bind_path = volumes[mnt]["bind"]
        mode = volumes[mnt]["mode"]

        if local_p.is_dir():
            formatted += f"{indent}|-{bind_path}/  # {mode}\n"

            for _, subdirs, filenames in local_p.walk():
                for file in filenames:
                    file_indent = "   " * (level + 1)
                    formatted += f"{file_indent}|-{file}  # {mode}\n"

                if subdirs:
                    for subdir in subdirs:
                        formatted += _format_volumes_for_sys_prompt(
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


if __name__ == "__main__":
    from rich import print, markdown as md

    print(md.Markdown(Docker([]).messages[0].content))
