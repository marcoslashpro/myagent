from pathlib import Path

from docker import DockerClient
import docker.errors
from docker.models.containers import Container

from myagent.v1.errors import InvalidMountError
from myagent.v1.models import Mount


class Docker:
    def __init__(
        self,
        mnt_dir: str,
        mounts: list[Mount],
        client: DockerClient | None = None,
    ):
        self.client = client or DockerClient.from_env()
        self._container: None | Container = None
        self._volumes = self._bind_mounts(mnt_dir, mounts)
        self._mnt_dir = mnt_dir

    def _bind_mounts(self, mnt_dir, mounts: list[Mount]):
        volumes = {}

        for mount in mounts:
            if not mount.path.expanduser().exists():
                raise InvalidMountError(str(mount.path))
            volumes[str(mount.path.expanduser())] = {
                "bind": f"{mnt_dir}/{mount.path.name}",
                "mode": mount.mode,
            }
        return volumes

    def run(self, cmd: str):
        try:
            return self.client.containers.run(
                "python:3.12-slim",
                command=["sh", "-c", cmd],
                volumes=self._volumes,
                auto_remove=True,
                stdout=True,
                stderr=True,
            ).decode()
        except docker.errors.APIError as e:
            return e.explanation if e.explanation else str(e)
        except docker.errors.ContainerError as e:
            return str(e)

    def __enter__(self):
        if not self._container:
            print(f"[INFO] - Starting container, mounting: {self._volumes}")
            self.container = self.client.containers.create(
                "python:3.12-slim",
                auto_remove=True,
                volumes=self._volumes,
            )

        return self

    def __exit__(self, exc_type, exc, tb):
        if self._container:
            print(f"[INFO] - Shutting down container")
            self._container.stop()
