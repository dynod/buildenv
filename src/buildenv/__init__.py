"""
Python main module for **buildenv** tool.
"""

import pkg_resources

__title__ = "buildenv"
try:
    __version__ = pkg_resources.get_distribution(__title__).version
except pkg_resources.DistributionNotFound:  # pragma: no cover
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
