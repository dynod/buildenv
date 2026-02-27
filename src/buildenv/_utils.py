import logging
import os
import subprocess
from pathlib import Path
from typing import cast

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


def run_subprocess(
    args: list[str],
    check: bool = True,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    verbose: bool | None = None,
    logger: logging.Logger | None = None,
    error_msg: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """
    Execute subprocess, and logs output/error streams + error code

    :param args: subprocess commands and arguments
    :param check: if True and subprocess return code is not 0, raise an exception
    :param cwd: current working directory for subprocess
    :param env: environment variables map for subprocess
    :param verbose: override verbose subprocess logging for this call (default: False)
    :param logger: logger to use for this call (default: use root logger)
    :param error_msg: error message to be logged in case of subprocess failure
    :return: completed process instance
    """

    # Prepare logger
    _logger = logger if logger else logging.getLogger()

    # Check option for subprocess
    sub_check = (error_msg is None) and check

    # Build args according to verbose option
    verbose_option = verbose if verbose is not None else False
    all_run_args = (
        {"args": args, "check": sub_check, "cwd": cwd, "env": env}
        if verbose_option
        else {"args": args, "check": False, "capture_output": True, "text": True, "encoding": "utf-8", "errors": "ignore", "cwd": cwd, "env": env}
    )

    # Run process
    _logger.debug(f"Running command: {args} -- in folder {cwd}")
    cp = cast(subprocess.CompletedProcess[str], subprocess.run(**all_run_args))  # type: ignore

    # Log output of not verbose
    if not verbose_option:
        _logger.debug(f">> rc: {cp.returncode}")
        _logger.debug(">> stdout:")
        list(map(_logger.debug, cp.stdout.splitlines(keepends=False)))
        _logger.debug(">> stderr:")
        list(map(_logger.debug, cp.stderr.splitlines(keepends=False)))

    # Subprocess failed?
    if cp.returncode != 0:
        if error_msg:
            # Just display a warning message
            _logger.warning(error_msg)
        elif check:
            # Fatal
            raise RuntimeError(
                f"command returned {cp.returncode}" + (f"\n{cp.stdout}" if len(cp.stdout) else "") + (f"\n{cp.stderr}" if len(cp.stderr) else "")
            )

    return cp
