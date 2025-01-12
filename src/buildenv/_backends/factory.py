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
        _LOGGER.warning(f"Detected environment: {env_root}")

        # Look for venv config file
        venv_cfg = env_root / "pyvenv.cfg"
        assert venv_cfg.is_file(), f"Can't locate venv config file: {venv_cfg}"

        # Load venv properties
        venv_props = ConfigParser()
        with venv_cfg.open() as f:
            venv_props.read_string("[DEFAULT]\n" + f.read())

        # UV property?
        if venv_props.has_option(None, "uv"):
            # UV backend detected
            return UvToolsBackend()

        # Pipx json file?
        if (env_root / "pipx_metadata.json").is_file():
            return PipXBackend()

        # Default: legacy pip backend
        return LegacyPipBackend()
