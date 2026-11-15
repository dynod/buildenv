import os
from pathlib import Path

from ..completion import CompletionCommand, EvalCompletionCommand
from .backend import EnvBackend, EnvBackendWithRequirements, MutableEnvBackend


class _CommonUvImpl(EnvBackend):
    @property
    def install_url(self):
        return "https://docs.astral.sh/uv/"

    def has_pip(self):
        # Uv based env does not have pip
        return False

    @property
    def _completions(self) -> list[CompletionCommand]:
        # Add uv + uvx completion
        return super()._completions + [
            EvalCompletionCommand("uv generate-shell-completion bash"),
            EvalCompletionCommand("uvx --generate-shell-completion bash"),
        ]


# UV-style backend
class UvProjectBackend(_CommonUvImpl, MutableEnvBackend):
    NAME = "uv"

    @property
    def name(self):
        return UvProjectBackend.NAME

    @property
    def venv_name(self) -> str:
        return ".venv"

    @property
    def _extra_args(self) -> list[str]:
        # Get extra args from environment variable
        return [arg for arg in os.getenv("BUILDENV_UV_ARGS", "").split(" ") if arg]

    def subprocess(
        self,
        args: list[str],
        check: bool = True,
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
        verbose: bool | None = None,
        error_msg: str | None = None,
        log_as_cmd: bool = True,
    ):
        # Systematically add uv args to uv subprocess
        return super().subprocess([self.name] + args + self._extra_args, check, cwd, env, verbose, error_msg, log_as_cmd)

    def _delegate_add_packages(self, packages: list[str]):
        # Delegate to uv; assuming uv project is already created, and all packages added through this interface are dev ones
        self.subprocess(["add", "--dev", *packages], check=True, cwd=self._project_path)

    def upgrade(self, full: bool = True, print_updates: bool = True, exact: bool = False) -> int:
        # Force env synchronization
        return self.subprocess(
            ["sync"] + (["--upgrade"] if full else []) + (["--inexact"] if not exact else ["--exact"]),
            check=False,
            cwd=self._project_path,
            verbose=print_updates,
        ).returncode

    @property
    def run_wrapper(self) -> str:
        # Use uv run wrapper
        return "uv run"


# UVX-style backend (immutable)
class UvxBackend(_CommonUvImpl, EnvBackendWithRequirements):
    NAME = "uvx"

    @property
    def name(self):
        return UvxBackend.NAME

    @property
    def run_wrapper(self) -> str:
        # Use uvx wrapper
        return "uvx --with requirements.txt"
