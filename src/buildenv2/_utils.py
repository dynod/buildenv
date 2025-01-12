import os
from pathlib import Path

LOGGER_NAME = "buildenv"
"""
Logger name used throughout the buildenv package
"""


def is_windows() -> bool:
    """
    States if running on Windows

    :return: True if running on Windows, False otherwise
    """
    return "nt" in os.name


def is_ci() -> bool:
    """
    States if running in a CI environment

    :return: True if running in CI, False otherwise
    """
    return os.getenv("CI") is not None


def to_linux_path(path: Path) -> str:
    """
    Turn provided path to a Linux style path.
    On Windows, this means turning drive "X:\" to "/x/" format (git-bash style path)

    :param path: Path to be converted
    :return: Converted path, in Linux style
    """
    p = Path(path)
    return f"/{p.drive[0].lower()}/{p.as_posix()[3:]}" if len(p.drive) else p.as_posix()


def contribute_path(env: dict[str, str], to_contribute: Path):
    """
    Contribute provided folder to PATH if not done yet

    :param env: environment map
    :param to_contribute: path to be added to PATH
    """

    # Turn PATH to a resolved Path objects list
    resolved_paths = set([Path(p).resolve() for p in env["PATH"].split(os.pathsep)])
    resolved_contribution = to_contribute.resolve()

    # If not already in PATH, add it
    if resolved_contribution not in resolved_paths:
        env["PATH"] = f"{resolved_contribution}{os.pathsep}{env['PATH']}"
