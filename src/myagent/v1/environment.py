import io
import os
from pathlib import Path

from docker import DockerClient
import docker.errors
from docker.models.containers import Container
from docker.models.images import Image

from myagent.core.messages import Message, SystemMessage
from myagent.v1.actions import Observation
from myagent.v1.errors import (
    AgentEnvironmentError,
    DockerSetupError,
    InvalidDockerFileError,
    InvalidMountError,
)
from myagent.v1.models import ImageMetadata, Mount, Volumes
from myagent.v1.tools import Tool
from myagent.v1.types import RoOrRw


LOCAL_ROOT_DIR = Path("~/.myagent").expanduser()
LOCAL_ROOT_DIR.mkdir(exist_ok=True)


class Docker:
    _mnt_dir = "/mnt"
    _mnt_tools = "/tools"
    _sys_prompt_path = Path(__file__).parent.parent / "prompts/docker_agent_sys.txt"
    _artifacts_path = LOCAL_ROOT_DIR.joinpath("artifacts").expanduser()
    _builtin_tools_path = LOCAL_ROOT_DIR.joinpath("tools").expanduser()
    _img_tag = "agent-env:latest"

    def __init__(
        self,
        tools: list[Tool],
        mounts: list[Mount],
        dockerfile: Path | None = None,
        remote_repo: str | None = None,
        messages: list[Message] | None = None,
        client: DockerClient | None = None,
    ):
        self.client = client or DockerClient.from_env()

        self._tools: Volumes = {**self._bind_tools(tools), **self._bind_builtins()}
        self._volumes: Volumes = self._bind_mounts(self._add_artifacts_to(mounts))

        self._img: Image | str = self._build_img(dockerfile, remote_repo)
        self._img_metadata: ImageMetadata = ImageMetadata.from_img(self._img)
        self._container: Container | None = None
        self.messages: list[Message] = messages or [self._generate_sys_prompt()]

    def _bind_tools(self, tools: list[Tool]) -> Volumes:
        volumes: Volumes = {}

        for tool in tools:
            volumes.update(
                _build_volume(
                    str(tool.path),
                    f"{self._mnt_dir}{self._mnt_tools}/{tool.path.name}",
                    tool.mode,
                )
            )

        return volumes

    def _bind_builtins(self) -> Volumes:
        self._builtin_tools_path.mkdir(exist_ok=True)
        volumes: Volumes = {}

        for builtin_tool in self._builtin_tools_path.iterdir():
            volumes.update(
                _build_volume(
                    str(builtin_tool),
                    f"{self._mnt_dir}{self._mnt_tools}/{builtin_tool.name}",
                    "rw",
                )
            )
        return volumes

    def _bind_mounts(self, mounts: list[Mount]) -> Volumes:
        volumes: Volumes = {}

        for mount in mounts:
            if not mount.path.expanduser().exists():
                raise InvalidMountError(path=str(mount.path))
            volumes.update(
                _build_volume(
                    str(mount.path.expanduser()),
                    f"{self._mnt_dir}/{mount.path.name}",
                    mount.mode,
                )
            )
        return volumes

    def _add_artifacts_to(self, mounts: list[Mount]) -> list[Mount]:
        self._artifacts_path.mkdir(exist_ok=True)
        mounts.append(Mount(self._artifacts_path, mode="rw"))
        return mounts

    def _generate_sys_prompt(self) -> SystemMessage:
        sys_prompt = self._sys_prompt_path.read_text()
        sys_prompt = (
            sys_prompt.replace("{{IMAGE_METADATA}}", str(self._img_metadata))
            .replace("{{SHELL}}", self._img_metadata.shell)
            .replace(
                "{{FILES}}",
                f"```bash\n{_format_volumes_for_sys_prompt(self._volumes)}\n```",
            )
            .replace(
                "{{TOOLS}}",
                f"{_format_tools_for_sys_prompt(
                    f"{self._mnt_dir}{self._mnt_tools}",
                    self._tools)
                }",
            )
            .replace("{{MNT_DIR}}", self._mnt_dir)
            .replace("{{ARTIFACTS_DIR}}", self._artifacts_path.name)
            .replace("{{TOOL_DIR}}", self._mnt_tools)
        )
        return SystemMessage(content=sys_prompt)

    def _build_img(self, dockerfile: Path | None, pull: str | None) -> Image:
        if pull and dockerfile:
            raise DockerSetupError(
                "Cannot create a valid image when provided both "
                "dockerfile and an image to pull from registry. "
                "Please provide only one of the two."
            )

        if dockerfile:
            if not dockerfile.exists():
                raise InvalidDockerFileError(str(dockerfile))

            return self.client.images.build(
                path=str(dockerfile.parent.resolve()),
                dockerfile=dockerfile.name,
                tag=self._img_tag,
                forcerm=True,
            )[0]

        if pull:
            return self.client.images.pull(pull)

        return self.client.images.build(
            fileobj=_write_default_dockerfile(),
            tag=self._img_tag,
            forcerm=True,
        )[0]

    def start(self):
        self._container = self.client.containers.run(
            self._img,
            command=f"{self._img_metadata.shell} -c 'while true; do sleep 1; done'",
            detach=True,
            tty=False,
            volumes={
                **self._volumes,
                **self._tools,
            },  # type: ignore
            cap_drop=["ALL"],  # drop all linux capabilities
            tmpfs={"/tmp": "size=64m"},
            mem_limit="512m",
            nano_cpus=1_000_000_000,
            cap_add=["NET_RAW"],  # add back only what's needed for networking
            security_opt=["no-new-privileges:true"],  # prevent privilege escalation
            pids_limit=100,  # prevent fork bombs
        )

    def run(self, cmd: str) -> Observation:
        try:
            if not self._container:
                raise AgentEnvironmentError(
                    "Cannot run any command in the container unless the container is started first.\n"
                    "Please make sure to use `.start()` method on this instance."
                )

            res = self._container.exec_run(
                cmd=[self._img_metadata.shell, "-c", cmd],
                stdout=True,
                stderr=True,
                demux=True,
            )
            stdout, stderr = res.output
            return Observation(
                content=(stdout.decode() if stdout else stderr.decode()),
                type="observation" if stdout else "observation_error",
                status_code=res.exit_code,
            )
        except docker.errors.APIError as e:
            return Observation(
                content=str(e),
                type="observation_error",
                status_code=e.status_code if e.status_code else 400,
            )
        except docker.errors.ContainerError as e:
            return Observation(
                content=e.stderr if e.stderr else str(e),
                type="observation_error",
                status_code=e.exit_status,
            )

    def stop(self):
        if self._container:
            self._container.stop()
            self._container.remove()


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


def _format_tools_for_sys_prompt(tool_dir: str, tools: Volumes) -> str:
    names = []
    indent = "    "
    for local_tool_path in tools.keys():
        names.append(f"{Path(tools[local_tool_path]['bind'])}")

    return f"```bash\n{tool_dir}\n{indent}|-" + f"\n{indent}|-".join(names) + "\n```"


def _build_volume(_from: str, to: str, mode: RoOrRw) -> Volumes:
    return {_from: {"bind": to, "mode": mode}}


def _write_default_dockerfile():
    return io.BytesIO(
        """
FROM python:3.12-slim
LABEL agent.shell='bash'
LABEL agent.description="Bash environment with python pre-installed"
LABEL agent.base_img='python:3.12-slim'
""".encode()
    )


if __name__ == "__main__":
    from rich import print, markdown as md

    print(md.Markdown(Docker([], []).messages[0].content))
