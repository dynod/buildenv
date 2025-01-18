import logging
import sys
from configparser import ConfigParser
from pathlib import Path

from .backend import EnvBackend
from .pip import LegacyPipBackend
from .pipx import PipXBackend
from .uv import UvToolsBackend

_LOGGER = logging.getLogger(__name__)


# Backend detection factory
class EnvBackendFactory:
    @staticmethod
    def create() -> EnvBackend:
        """
        Detect backend from running python instance, and return corresponding implementation

        :return: detected backend implementation instance
        """

        # Check env root from current executable
        env_root = Path(sys.executable).parent.parent
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
        if venv_props.has_option(None, "uv"):
            # UV backend detected
            backend_class = UvToolsBackend

        # Pipx json file?
        elif (env_root / "pipx_metadata.json").is_file():
            backend_class = PipXBackend

        # Default: legacy pip backend
        else:
            backend_class = LegacyPipBackend

        # Return backend instance
        return backend_class(env_root)
