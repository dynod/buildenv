"""
Python main module for **buildenv** tool.
"""

from importlib.metadata import version

__title__ = "buildenv"
try:
    __version__ = version(__title__)
except Exception:  # pragma: no cover
    # For debug
    from configparser import ConfigParser
    from pathlib import Path

    try:
        with (Path(__file__).parent.parent.parent / "setup.cfg").open("r") as f:
            c = ConfigParser()
            c.read_file(f.readlines())
            __version__ = c.get("metadata", "version")
    except Exception:
        __version__ = "unknown"

from buildenv.manager import BuildEnvExtension, BuildEnvLoader, BuildEnvManager

__all__ = ("BuildEnvManager", "BuildEnvLoader", "BuildEnvExtension")
