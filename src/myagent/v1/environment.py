from pathlib import Path

from docker import DockerClient
import docker.errors
from docker.models.containers import Container


class Docker:
    _local_artifacts_dir = Path("~/.artifacts").expanduser()
    _remote_artifacts_dir = "/artifacts"

    def __init__(self, client: DockerClient | None = None):
        self.client = client or DockerClient.from_env()
        if not self._local_artifacts_dir.exists():
            self._local_artifacts_dir.mkdir()
        self._container: None | Container = None
        self._volumes = {
            str(self._local_artifacts_dir): {
                "bind": self._remote_artifacts_dir,
                "mode": "rw",
            }
        }

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
            print(f"[INFO] - Starting container")
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
