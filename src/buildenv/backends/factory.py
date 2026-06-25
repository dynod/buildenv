import logging
import shutil
import sys
from configparser import ConfigParser
from pathlib import Path

from .._utils import LOGGER_NAME
from ._pip import LegacyPipBackend
from ._pipx import PipXBackend
from ._uv import UvProjectBackend, UvxBackend
from .backend import EnvBackend

_LOGGER = logging.getLogger(LOGGER_NAME)

# Backends class map
_KNOW_BACKENDS = {x.NAME: x for x in [LegacyPipBackend, UvProjectBackend, UvxBackend, PipXBackend]}


# Backend detection factory
class EnvBackendFactory:
    KNOWN_BACKENDS = list(_KNOW_BACKENDS.keys())
    """
    List of known environment backends
    """

    _ENV_BIN = Path(sys.executable).parent.resolve()
    """
    Current environment bin folder
    """

    @staticmethod
    def is_supported(name: str) -> bool:
        """
        Check if backend name is supported

        :param name: backend name
        :return: True if supported, False otherwise
        """

        # Check if backend is known
        assert name in _KNOW_BACKENDS, f"Unknown backend: {name}"

        # Check if matching command is available in current environment
        return shutil.which(name) is not None

    @staticmethod
    def create(name: str, project_path: Path, verbose_subprocess: bool = True, shell_name: str = "bash") -> EnvBackend:
        """
        Create backend instance from name

        :param name: backend name
        :param project_path: project path
        :param verbose_subprocess: if True (default), subprocess calls output is streamed to console
        :param shell_name: name of the shell to use
        :return: created backend implementation instance
        """

        # Check if backend is known
        assert name in _KNOW_BACKENDS, f"Unknown backend: {name}"

        # Create backend instance
        return _KNOW_BACKENDS[name](
            venv_bin=EnvBackendFactory._ENV_BIN, project_path=project_path.resolve(), verbose_subprocess=verbose_subprocess, shell_name=shell_name
        )

    @staticmethod
    def detect(project_path: Path | None = None, verbose_subprocess: bool = True, shell_name: str = "bash") -> EnvBackend:
        """
        Detect backend from running python instance, and return corresponding implementation

        :param project_path: project path
        :param verbose_subprocess: if True (default), subprocess calls output is streamed to console
        :param shell_name: name of the shell to use
        :return: detected backend implementation instance
        """

        # Check env root from current executable
        env_root = EnvBackendFactory._ENV_BIN.parent
        _LOGGER.debug(f"Detected environment: {env_root}")

        # Look for venv config file
        venv_cfg = env_root / "pyvenv.cfg"
        assert venv_cfg.is_file(), f"Can't locate venv config file: {venv_cfg}"

        # Load venv properties
        venv_props = ConfigParser()
        with venv_cfg.open() as f:
            venv_props.read_string("[DEFAULT]\n" + f.read())

        # Prepare to create backend instance
        backend_class = None

        # UV property?
        if venv_props.has_option("", "uv"):
            # UV venv detected
            # Check if:
            # * venv root is relative to a location containing a pyproject file
            # * this location is a parent path of current project path
            root_project_path = env_root.parent
            root_project_file = root_project_path / "pyproject.toml"
            if root_project_file.is_file() and (project_path is not None) and project_path.resolve().is_relative_to(root_project_path):
                # Uv backend
                backend_class = UvProjectBackend
            else:
                # Uvx backend
                backend_class = UvxBackend

        # Pipx json file?
        elif (env_root / "pipx_metadata.json").is_file():
            backend_class = PipXBackend

        # Default: legacy pip backend
        else:
            backend_class = LegacyPipBackend

        # Return backend instance
        return backend_class(
            venv_bin=EnvBackendFactory._ENV_BIN,
            project_path=project_path.resolve() if project_path is not None else None,
            verbose_subprocess=verbose_subprocess,
            shell_name=shell_name,
        )
