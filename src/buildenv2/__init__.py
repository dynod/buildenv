"""
Python main module for **buildenv** tool.
"""

from importlib.metadata import version

__title__ = "buildenv2"
try:
    __version__ = version(__title__)
except Exception:  # pragma: no cover
    __version__ = "unknown"
