import importlib.metadata
import json
import logging
import os
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import psutil

from .._renderers.factory import Keywords, RendererFactory
from .._shells.factory import EnvShell, ShellFactory
from .._utils import LOGGER_NAME, contribute_path, is_ci
from ..completion import ArgCompleteCompletionCommand, CompletionCommand
from ..extension import BuildEnvExtension, BuildEnvInfo


# Installed files templates definition
@dataclass
class _InstalledFileDescriptor:
    template: Path  # Template file sub-path
    lazy: bool = False  # Lazy generation flag (don't generate if already present)
    executable: bool = False  # Generated file shall be executable
    leading_dot: bool = False  # Generated file shall be prefixed with a dot (hidden file on Unix-like systems)
    target: Path | None = None  # Target file path (None to use default path)


# Buildenv extension entry point name
_BUILDENV_EXT = "buildenv_extension"

# Editable suffix for version
_EDITABLE_SUFFIX = " (editable)"


# Backend base implementation
class EnvBackend(ABC):
    def __init__(self, venv_bin: Path, project_path: Path | None = None, verbose_subprocess: bool = True):
        # Logs handling
        self._logger = logging.getLogger(LOGGER_NAME)
        self._verbose_subprocess = verbose_subprocess

        # Remember paths
        self._venv_bin = venv_bin
        self._project_path = project_path

        # Load extensions
        self._info = BuildEnvInfo(venv_bin, project_path)
        self._extensions: dict[str, BuildEnvExtension] = self._parse_extensions(self._info)

        # Detect main version from loading scripts
        self._version = int(os.getenv("BUILDENV_VERSION", "1"))

        # Update current process environment
        os.environ["BUILDENV_LEVEL"] = os.getenv("BUILDENV_LEVEL", "0")
        os.environ["VIRTUAL_ENV"] = str(self._venv_bin.parent)
        os.environ["BUILDENV_VERSION"] = str(self._version)
        contribute_path(cast(dict[str, str], os.environ), self._venv_bin)

        # Prepare shell
        self._shell = ShellFactory.create(self._venv_bin, not self.has_pip(), self.name, self._extensions, self._completions)

    @property
    def version(self) -> int:
        """
        Main version detected from loading scripts
        """

        return self._version

    def subprocess(
        self, args: list[str], check: bool = True, cwd: Path | None = None, env: dict[str, str] | None = None, verbose: bool | None = None
    ) -> subprocess.CompletedProcess[str]:
        """
        Execute subprocess, and logs output/error streams + error code

        :param args: subprocess commands and arguments
        :param check: if True and subprocess return code is not 0, raise an exception
        :param cwd: current working directory for subprocess
        :param env: environment variables map for subprocess
        :param verbose: override verbose subprocess logging for this call (default: use backend setting)
        :return: completed process instance
        """

        # Build args according to verbose option
        verbose_option = verbose if verbose is not None else self._verbose_subprocess
        all_run_args = (
            {"args": args, "check": check, "cwd": cwd, "env": env}
            if verbose_option
            else {"args": args, "check": False, "capture_output": True, "text": True, "encoding": "utf-8", "errors": "ignore", "cwd": cwd, "env": env}
        )

        # Run process
        self._logger.debug(f"Running command: {args}")
        cp = cast(subprocess.CompletedProcess[str], subprocess.run(**all_run_args))  # type: ignore

        # Log output of not verbose
        if not verbose_option:
            self._logger.debug(f">> rc: {cp.returncode}")
            self._logger.debug(">> stdout:")
            list(map(self._logger.debug, cp.stdout.splitlines(keepends=False)))
            self._logger.debug(">> stderr:")
            list(map(self._logger.debug, cp.stderr.splitlines(keepends=False)))
        assert not check or cp.returncode == 0, (
            f"command returned {cp.returncode}" + (f"\n{cp.stdout}" if len(cp.stdout) else "") + (f"\n{cp.stderr}" if len(cp.stderr) else "")
        )
        return cp

    @property
    def venv_name(self) -> str:
        """
        Venv folder name, if any (empty string otherwise)
        """

        # By default, consider there is no venv folder
        return ""

    @property
    def venv_root(self) -> Path:
        """
        Venv root folder path
        """

        # Venv root is parent of venv bin folder
        return self._venv_bin.parent

    @property
    def project_path(self) -> Path:
        """
        Project path

        :return: project path
        """

        assert self._project_path is not None, "Project path is not set"
        return self._project_path

    @property
    def use_requirements(self) -> bool:
        """
        State if this backend uses requirements.txt file
        """
        return False

    @property
    def _completions(self) -> list[CompletionCommand]:
        # Default completions list is only buildenv itself
        return [ArgCompleteCompletionCommand("buildenv2")]

    # Iterate on entry points to load extensions
    def _parse_extensions(self, info: BuildEnvInfo) -> dict[str, BuildEnvExtension]:
        # Build entry points map (to handle duplicate names)
        unfiltered_entry_points: importlib.metadata.SelectableGroups = importlib.metadata.entry_points()
        all_entry_points: dict[str, importlib.metadata.EntryPoint] = {}
        if isinstance(unfiltered_entry_points, dict):  # type: ignore
            # Python <3.10
            for p in unfiltered_entry_points.get(_BUILDENV_EXT, []):
                all_entry_points[p.name] = p
        else:
            # Python >=3.10
            for p in unfiltered_entry_points.select(group=_BUILDENV_EXT):
                all_entry_points[p.name] = p

        out: dict[str, BuildEnvExtension] = {}
        for name, point in all_entry_points.items():
            # Instantiate extension
            try:
                extension_class = point.load()
                assert issubclass(extension_class, BuildEnvExtension), f"{name} extension class is not extending buildenv.BuildEnvExtension"
                extension = extension_class(info)
            except Exception as e:
                raise AssertionError(f"Failed to load {name} extension: {e}") from e
            out[name] = extension

        return out

    @property
    def shell_instance(self) -> EnvShell:
        """
        Get the shell instance used by this backend
        """
        return self._shell

    @property
    @abstractmethod
    def name(self) -> str:  # pragma: no cover
        """
        Environment backend implementation name
        """
        pass

    @property
    def command(self) -> str:
        """
        Backend setup command
        """
        return self.name  # Default implementation: use backend name as command

    @property
    @abstractmethod
    def install_url(self) -> str:  # pragma: no cover
        """
        Environment backend install instructions URL
        """
        pass

    def is_mutable(self) -> bool:
        """
        State if this backend supports installed packages update once created

        :return: True if environment is mutable
        """

        # Default implementation: immutable
        return False

    @abstractmethod
    def has_pip(self) -> bool:  # pragma: no cover
        """
        State if this backend includes pip tool

        :return: True if environment includes pip
        """
        pass

    def init(self, force: bool = False, skip_ext: list[str] | None = None, no_ext: bool = False, show_updates_from: Path | None = None) -> int:
        """
        Initialize the backend extensions

        :param force: Force re-initialization of extensions
        :param skip_ext: List of extensions names to skip
        :param no_ext: Skip all extensions initialization
        :param show_updates_from: Path to a file to show updates from
        :return: always 0
        """

        # Handle updates if requested (+ remove the temporary file)
        if show_updates_from is not None and show_updates_from.is_file():
            self.handle_updates(json.loads(show_updates_from.read_text()))
            show_updates_from.unlink()

        # Handle ignored extensions
        ignored_extensions: set[str] = set(self._extensions.keys()) if no_ext else (set(skip_ext) if skip_ext else set())

        # Iterate over backend extensions (filtering ignored ones)
        for ext_name, extension in filter(lambda item: item[0] not in ignored_extensions, self._extensions.items()):
            # Call extension init method
            try:
                extension.init(force)
            except Exception as e:
                raise AssertionError(f"Error occurred while calling {ext_name} extension init: {e}") from e
        return 0

    def shell(self, show_updates_from: Path | None = None, command: str | None = None) -> int:
        """
        Launch an interractive shell from the backend

        :param show_updates_from: Path to a file to show updates from
        :param command: command to be executed in the shell
        :return: shell exit code
        """

        # Init first
        self.init(show_updates_from=show_updates_from)

        # Run interractive shell (or command if specified)
        return self._shell.run(command)

    def run(self, command: str) -> int:
        """
        Run command in the backend shell

        :param command: command to be executed
        :return: command exit code
        """

        # Init first
        self.init()

        # Run command in shell
        return self._shell.run(command)

    def _get_files_descriptors(self) -> list[_InstalledFileDescriptor]:
        """
        Get the list of files to be installed for this backend

        :return: list of file descriptors
        """

        # Common list for all backends
        return [
            _InstalledFileDescriptor(Path(f"backends/{self.name}/buildenv.sh.jinja"), executable=True),
            _InstalledFileDescriptor(Path(f"backends/{self.name}/buildenv.cmd.jinja")),
            _InstalledFileDescriptor(Path("backends/common/gitattributes.jinja"), lazy=True, leading_dot=True),
        ]

    def _get_ignored_patterns(self) -> list[str]:
        """
        Get the list of ignored patterns for this backend

        :return: list of ignored patterns
        """

        # Common list for all backends
        return [".venv/"]

    # Inner files generation logic
    def _generate_files(
        self,
        descriptors: list[_InstalledFileDescriptor],
        packages: list[str] | None = None,
        extra_keywords: Keywords | None = None,
        log_level: int = logging.INFO,
    ):
        # Handle project-less backend
        assert self._project_path is not None, "Can't generate files without a project path"

        # Prepare keywords
        all_keywords = {
            "packages": packages if packages else [],
            "command": self.command,
            "url": self.install_url,
            "ignored_patterns": self._get_ignored_patterns(),
        } | (extra_keywords if extra_keywords else {})

        # Iterate on these files
        for installed_file in descriptors:
            # Use specified target, or deduce it from template name if not specified
            if installed_file.target is not None:
                project_target_file = installed_file.target
            else:
                project_target_file = self._project_path / f"{'.' if installed_file.leading_dot else ''}{installed_file.template.name.removesuffix('.jinja')}"
            logged_name = (
                str(project_target_file.relative_to(self._project_path)) if project_target_file.is_relative_to(self._project_path) else project_target_file.name
            )

            # Generate target file only if not already present or not lazy
            if (not installed_file.lazy) or (not project_target_file.is_file()):
                self._logger.log(log_level, f"Generate {logged_name}")
                RendererFactory.create(installed_file.template, self.name).render(
                    project_target_file, keywords=all_keywords, executable=installed_file.executable
                )
            else:
                self._logger.log(log_level, f"Skip {logged_name} generation (already exist in this project)")

    def install(self, packages: list[str] | None = None) -> int:
        """
        Install loading scripts for the backend

        :param packages: additional packages to install
        :return: command exit code
        """

        # Delegate to generation logic
        self._generate_files(self._get_files_descriptors(), packages)

        # Everything went well
        return 0

    def add_packages(self, packages: list[str]):
        """
        Add packages to the environment (if mutable)

        :param packages: list of packages to add
        """

        # Check if mutable
        assert self.is_mutable(), f"{self.name} backend is not mutable, can't add packages"

        # Delegate to backend implementation
        self._delegate_add_packages(packages)

    def _delegate_add_packages(self, packages: list[str]) -> None:  # pragma: no cover
        """
        Delegate package addition to the backend implementation, has to be overridden by mutable backends implementation

        :param packages: list of packages to add
        """
        raise NotImplementedError

    @abstractmethod
    def lock(self, log_level: int = logging.INFO) -> int:  # pragma: no cover
        """
        Create a lockfile for this environment, so that next time the environment is loaded, it will be restored to this state

        :param log_level: logging level to use for file generation
        :return: command exit code
        """
        raise NotImplementedError

    def upgrade(self, full: bool = True, only_deps: bool = False) -> int:  # pragma: no cover
        """
        Upgrade all packages in this environment to their latest version.
        Also dumps upgraded versions to the console.

        :param full: if True, check for updates from remote repositories (may be slow); if False, ignore already installed packages
        :param only_deps: if True, upgrade only dependencies (not current project)
        :return: command exit code
        """

        # Remember old packages
        old_packages = self.installed_packages

        # Delegate to backend implementation
        rc = self._delegate_upgrade(full, only_deps)

        # If mutable and upgrade succeeded, print updates
        if rc == 0 and self.is_mutable():
            self.handle_updates(old_packages)

        return rc

    @abstractmethod
    def _delegate_upgrade(self, full: bool = True, only_deps: bool = False) -> int:  # pragma: no cover
        """
        Delegate packages upgrade to the backend implementation
        """
        raise NotImplementedError

    def handle_updates(self, old_packages: dict[str, str]):
        """
        Handle packages updates from previous verions

        :param old_packages: map of old installed packages versions (indexed by package name)
        """

        # By default, just print update
        self.print_updates(old_packages)

    def print_updates(self, old_packages: dict[str, str]):
        """
        Pretty print packages updates to stdout

        :param old_packages: map of old installed packages versions (indexed by package name)
        """

        # Locate changes and print them (if any)
        old_packages_names = set(old_packages.keys())
        new_packages = self.installed_packages
        new_packages_names = set(new_packages.keys())
        changes: dict[str, str] = {}
        for removed_package in old_packages_names - new_packages_names:
            changes[removed_package] = f"removed (was {old_packages[removed_package]})"
        for added_package in new_packages_names - old_packages_names:
            changes[added_package] = f"added ({new_packages[added_package]})"
        for updated_package in {name for name in new_packages_names & old_packages_names if new_packages[name] != old_packages[name]}:
            changes[updated_package] = f"updated (from {old_packages[updated_package]} to {new_packages[updated_package]})"
        if changes:
            self._logger.info("Some packages were updated:")
            self._print_packages(changes)
        else:
            self._logger.info("All packages are already up to date.")

    @property
    def installed_packages(self) -> dict[str, str]:
        """
        List installed packages in this environment

        :return: map of installed packages versions (indexed by package name)
        """

        out: dict[str, str] = {}
        for pkg in importlib.metadata.distributions():
            # Check for editable package
            is_editable = False
            try:
                json_content = pkg.read_text("direct_url.json")
            except FileNotFoundError:  # pragma: no cover
                json_content = None
            if json_content and json.loads(json_content).get("dir_info", {}).get("editable", False):
                is_editable = True

            # Add in output only if not already present in editable mode
            name = pkg.name
            if (name not in out) or (not out[name].endswith(_EDITABLE_SUFFIX)):
                out[pkg.metadata["Name"]] = f"{pkg.version}{_EDITABLE_SUFFIX if is_editable else ''}"
        return out

    def _print_packages(self, packages: dict[str, str]):
        """
        Pretty print packages list to stdout

        :param packages: map of installed packages versions (indexed by package name)
        """

        # Prepare formatting
        biggest_name_length = max((len(name) for name in list(packages.keys()) + ["Package"]), default=0)
        biggest_version_length = max((len(version) for version in list(packages.values()) + ["Version"]), default=0)

        def print_package(name: str, version: str):
            self._logger.info(f"{name.ljust(biggest_name_length)} {version}")

        # Pretty print header
        print_package("Package", "Version")
        self._logger.info(f"{'-' * biggest_name_length} {'-' * biggest_version_length}")

        # Pretty print name+version (sorted by name)
        for name, version in sorted(packages.items(), key=lambda item: item[0].lower()):
            print_package(name, version)

    def list(self) -> int:
        """
        List installed packages in this environment and print them to stdout

        :return: command exit code
        """

        # Pretty print installed packages
        self._print_packages(self.installed_packages)

        return 0

    def dump(self, output_file: Path, log_level: int = logging.INFO):
        """
        Dump installed packages in this environment to a requirements-like file

        :param output_file: path to the output requirements file
        :param log_level: logging level to use for file generation
        """

        # Just dump installed packages to the specified file
        self._generate_files(
            [_InstalledFileDescriptor(template=Path("backends/common/requirements.lock.jinja"), target=output_file)],
            extra_keywords={"installed_packages": self.installed_packages},
            log_level=log_level,
        )


class EnvBackendWithRequirements(EnvBackend):
    @property
    def use_requirements(self) -> bool:
        return True

    @property
    def _lock_file(self) -> Path:
        assert self._project_path is not None, "Project path is not set"
        return self._project_path / "requirements.lock"

    def _get_files_descriptors(self):
        return super()._get_files_descriptors() + [
            _InstalledFileDescriptor(Path("backends/common/requirements.txt.jinja"), lazy=True),
        ]

    def lock(self, log_level: int = logging.INFO) -> int:
        # Use the dump method
        self.dump(self._lock_file, log_level)

        # For CLI
        return 0

    def _backend_upgrade_env(self) -> tuple[str, str] | None:
        """
        Get backend upgrade environment var name + arg, if any
        """

        # Not implemented by default
        return None

    def handle_updates(self, old_packages: dict[str, str]):
        # Super call
        super().handle_updates(old_packages)

        # Refresh lockfile if it exists
        if self._lock_file.is_file():
            self._logger.info(f"Refresh {self._lock_file.name} file...")
            self.lock()

    def _delegate_upgrade(self, full: bool = True, only_deps: bool = False) -> int:
        # Project path is mandatory
        assert self._project_path is not None, "Project path is not set"

        # We can't spawn a subshell in CI
        assert not (is_ci() and self._shell.env_level), "Can't spawn a subshell in CI environment"

        # Force "refresh" option for backend
        env = dict(os.environ)
        backend_env = self._backend_upgrade_env()
        if backend_env is not None:  # pragma: no branch
            env_name, env_arg = backend_env
            env[env_name] = env.get(env_name, "") + f" {env_arg}"

        # Dump current installed packages to a temporary file
        old_packages_dump = self._project_path / "._buildenv_old_packages.json"
        old_packages_dump.write_text(json.dumps(self.installed_packages))

        # Delegate to shell script
        # If already in a shell, spawn a new one, else just init the environment again
        args = [self._shell.script, "shell" if self._shell.env_level else "init", "--show-updates-from", str(old_packages_dump)]
        rc = self.subprocess(args, cwd=self._project_path, check=False, env=env, verbose=True).returncode

        # After having exited the spawned shell, if any, kill parent shell to enforce reloading the environment
        if rc == 0 and self._shell.env_level:  # pragma: no cover
            self._logger.info("Exiting parent shell after upgrade...")
            psutil.Process(os.getppid()).kill()
        return rc


class MutableEnvBackend(EnvBackend):
    def is_mutable(self) -> bool:
        return True

    def _get_files_descriptors(self):
        return super()._get_files_descriptors() + [
            _InstalledFileDescriptor(Path("backends/common/gitignore.jinja"), lazy=True, leading_dot=True),
        ]
