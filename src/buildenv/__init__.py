"""
Python main module for **buildenv** tool.
"""

from importlib.metadata import version

from .extension import BuildEnvExtension, BuildEnvInfo, BuildEnvProjectTemplate, BuildEnvRenderer

__all__ = ["BuildEnvExtension", "BuildEnvInfo", "BuildEnvProjectTemplate", "BuildEnvRenderer"]

__title__ = "buildenv"
try:
    __version__ = version(__title__)
except Exception:  # pragma: no cover
    __version__ = "unknown"
