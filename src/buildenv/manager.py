import os
import random
import subprocess
import sys
from argparse import Namespace
from pathlib import Path
from typing import Dict, List

import pkg_resources

from buildenv import __version__
from buildenv._internal.parser import RCHolder
from buildenv._internal.render import RC_START_SHELL, TemplatesRenderer
from buildenv.extension import BuildEnvExtension
from buildenv.loader import BuildEnvLoader, logger

BUILDENV_OK = "buildenvOK"
"""Valid buildenv tag file"""

# Temp buildenv scripts folder
_BUILDENV_TEMP_FOLDER = ".buildenv"

# Path to buildenv module
_MODULE_FOLDER = Path(__file__).parent

# Recommended git files
_RECOMMENDED_GIT_FILES = [".gitignore", ".gitattributes"]

# Return codes
_RC_RUN_CMD = 101  # Start of RC range for running a command
_RC_MAX = 255  # Max RC


class BuildEnvManager:
    """
    **buildenv** manager entry point

    :param project_path: Path to the current project root folder
    :param venv_bin_path: Path to venv binary folder to be used (mainly for test purpose; if None, will use current venv executable)
    """

    def __init__(self, project_path: Path, venv_bin_path: Path = None):
        # Deal with venv paths
        self.venv_bin_path = venv_bin_path if venv_bin_path is not None else Path(sys.executable).parent  # Bin path
        self.venv_path = self.venv_bin_path.parent  # Venv path
        self.venv_root_path = self.venv_path.parent  # Parent project path (may be the current one or a parent folder one)

        # Other initializations
        self.project_path = project_path  # Current project path
        self.project_script_path = self.project_path / _BUILDENV_TEMP_FOLDER  # Current project generated scripts path
        self.loader = BuildEnvLoader(self.project_path)  # Loader instance
        self.is_windows = (self.venv_bin_path / "activate.bat").is_file()  # Is Windows venv?
        self.venv_context = self.loader.setup_venv(self.venv_bin_path.parent)
        self.buildenv_ok = self.venv_path / BUILDENV_OK

        # Private data
        self._completion_commands = set()
        self.register_completion("buildenv")
        self._ignored_patterns = []
        self.register_ignored_pattern(self.venv_path.name + "/")
        self.register_ignored_pattern(_BUILDENV_TEMP_FOLDER + "/")
        self.is_valid_projet = True

        try:
            # Relative venv bin path string for local scripts
            relative_venv_bin_path = self.venv_bin_path.resolve().relative_to(self.project_path.resolve())

            # Venv is relative to current project
            self.is_project_venv = True
        except ValueError:
            # Venv is *not* relative to current project
            self.is_project_venv = False

            try:
                # Venv is not relative to current project: reverse logic
                upper_levels_count = len(self.project_path.resolve().relative_to(self.venv_root_path.resolve()).parts)
                relative_venv_bin_path = Path(os.pardir)
                for part in [os.pardir] * (upper_levels_count - 1) + [self.venv_path.name, self.venv_bin_path.name]:
                    relative_venv_bin_path /= part
            except ValueError:
                # Project and venv are definitely not relative to each other
                # We get in this case when command is executed out of venv/project folder
                relative_venv_bin_path = None
                self.is_valid_projet = False

        # Prepare template renderer
        self.renderer = TemplatesRenderer(self.loader, relative_venv_bin_path, self.project_script_path)

    def init(self, options: Namespace = None):
        """
        Build environment initialization.

        This method generates loading scripts in current project folder (if not invoked from loading scripts; can't update them while they're running).

        If the buildenv is not marked as ready yet, this method also:

        * verify recommended git files
        * invoke extra environment initializers defined by sub-classes
        * mark buildenv as ready

        :param options: Input command line parsed options
        """

        # If --new option is used, spawn a new loader to create a new build environment
        if hasattr(options, "new") and options.new is not None:
            new_folder = options.new if options.new.is_absolute() else Path.cwd() / options.new
            new_folder.mkdir(parents=True, exist_ok=True)
            BuildEnvLoader(new_folder).setup(["init"])
            return

        # Check for valid project
        assert self.is_valid_projet, "Out of project folder!"

        # Update scripts
        self._update_scripts(hasattr(options, "from_loader") and options.from_loader is not None)

        # Stop here if required to skip
        skip = False if not hasattr(options, "skip") else options.skip
        if skip:
            return

        # Prepare entry points
        all_extensions = self._parse_extensions()

        # Refresh buildenv if not done yet
        force = False if not hasattr(options, "force") else options.force
        if force or not self._check_versions(all_extensions):
            # Make sure we're not updating a parent build env
            if not self.is_project_venv:
                logger.warning(f"Can't update a parent project buildenv; please update buildenv in {self.venv_path.parent} folder")
                return

            logger.info("Customizing buildenv...")

            try:
                # Clean existing scripts
                self._clean_activation_files()
            except AssertionError as e:
                # Clean failed: print warning and give up
                logger.warning(str(e))
                return

            # Clean was successful: continue with initialization
            self._run_extensions(all_extensions, force)
            self._add_activation_files()
            self._verify_git_files()
            self._make_ready()

    # Copy/update loading scripts in project folder
    def _update_scripts(self, from_loader: bool):
        # Generate loading scripts (only if not invoked from loading script)
        if not from_loader:
            self.renderer.render(_MODULE_FOLDER / "loader.py", self.project_path / "buildenv-loader.py")
            self.renderer.render("buildenv.sh.jinja", self.project_path / "buildenv.sh", executable=True)
            self.renderer.render("buildenv.cmd.jinja", self.project_path / "buildenv.cmd")

        # Generate temporary scripts for run/shell commands
        self.renderer.render("activate.sh.jinja", self.project_script_path / "activate.sh")
        self.renderer.render("shell.sh.jinja", self.project_script_path / "shell.sh")
        if self.is_windows:
            # Only if venv files are generated for Windows
            self.renderer.render("activate.cmd.jinja", self.project_script_path / "activate.cmd")
            self.renderer.render("shell.cmd.jinja", self.project_script_path / "shell.cmd")

    # Check for recommended git files, and display warning if they're missing
    def _verify_git_files(self):
        for file in _RECOMMENDED_GIT_FILES:
            if not (self.project_path / file).is_file():
                logger.warning(f"Missing {file} file in project; generating a default one")
                self.renderer.render(f"{file[1:]}.jinja", self.project_path / file, keywords={"ignored_patterns": self._ignored_patterns})

    # List activation files
    @property
    def _existing_activation_files(self) -> List[Path]:
        out = list(filter(lambda f: f.is_file(), self.venv_context.activation_scripts_folder.glob("*")))
        assert len(out) > 0, "venv wasn't created by buildenv; can't work on activation scripts"
        return out

    # Clean extra activation files in venv
    def _clean_activation_files(self):
        # Browse existing files (all but initial ones, i.e. those with a prefix greater than 00_)
        for f in filter(lambda f: not f.name.startswith("00_"), self._existing_activation_files):
            f.unlink()

    # Add activation files in venv
    def _add_activation_files(self):
        # Iterate on required activation files
        for name, extensions, templates, keywords in [
            ("set_prompt", [".sh"], ["venv_prompt.sh.jinja"], None),
            ("completion", [".sh"], ["completion.sh.jinja"], {"commands": list(self._completion_commands)}),
        ]:
            # Iterate on extensions and templates
            for extension, template in zip(extensions, templates):
                # Add script to activation folder
                self.add_activation_file(name, extension, template, keywords)

    def register_completion(self, command: str):
        """
        Register a new command for completion in activation scripts.
        This command must be a python entry point supporting argcomplete completion.

        :param command: New command to be registered
        """
        self._completion_commands.add(command)

    def register_ignored_pattern(self, pattern: str):
        """
        Register a new pattern to be added to generated .gitignore file

        :param pattern: New pattern to be ignored
        """
        self._ignored_patterns.append(pattern)

    def add_activation_file(self, name: str, extension: str, template: str, keywords: Dict[str, str] = None):
        """
        Add activation file in venv (in "<venv>/<bin or Script>/activate.d" folder).
        This file will be loaded each time the venv is activated.

        :param name: Name of the activation script
        :param extension: Extension of the activation script
        :param template: Path to Jinja template file to be rendered for this script
        :param keyword: Map of keywords provided to template
        """

        # Find next index for activation script
        next_index = max(int(n.name[0:2]) for n in filter(lambda f: f.name.endswith(extension), self._existing_activation_files)) + 1

        # Build script name
        script_name = self.venv_context.activation_scripts_folder / f"{next_index:02}_{name}{extension}"

        # Generate from template
        self.renderer.render(template, script_name, keywords=keywords)

    # Iterate on entry points to load extensions
    def _parse_extensions(self) -> Dict[str, object]:
        # Build entry points map (to handle duplicate names)
        all_entry_points = {}
        for p in pkg_resources.iter_entry_points("buildenv_init"):
            all_entry_points[p.name] = p

        out = {}
        for name, point in all_entry_points.items():
            # Instantiate extension
            try:
                extension_class = point.load()
                assert issubclass(extension_class, BuildEnvExtension), f"{name} extension class is not extending buildenv.BuildEnvExtension"
                extension = extension_class(self)
            except Exception as e:
                raise AssertionError(f"Failed to load {name} extension: {e}")
            out[name] = extension

        return out

    # Check for persisted versions
    def _check_versions(self, all_extensions: Dict[str, object]) -> bool:
        # Build map of version files
        version_files = {self.buildenv_ok: __version__}
        version_files.update({self.venv_path / f"{n}OK": p.get_version() for n, p in all_extensions.items()})

        # Verify that all persisted versions are in line
        for v_file, v_str in version_files.items():
            # If any file doesn't exist: give up
            if not v_file.is_file():
                return False

            # Check version
            with v_file.open() as f:
                if f.read() != v_str:
                    # Version mismatch: give up
                    return False

        # If we get here, all versions (buildenv + extensions) are OK
        return True

    # Iterate on extensions to delegate init
    def _run_extensions(self, all_extensions: Dict[str, object], force: bool):
        # Iterate on entry points
        for name, extension in all_extensions.items():
            # Get initializer, and verify type
            logger.info(f" - with {name} extension")

            # Call init method
            try:
                extension.init(force)
            except Exception as e:
                raise AssertionError(f"Failed to execute {name} extension init: {e}")

            # Init ok: touch init file
            init_file = self.venv_path / f"{name}OK"
            with init_file.open("w") as f:
                f.write(extension.get_version())

    # Just touch "buildenv ready" file
    def _make_ready(self):
        logger.info("Buildenv is ready!")
        with (self.venv_path / BUILDENV_OK).open("w") as f:
            f.write(__version__)

    # Preliminary checks before env loading
    def _command_checks(self, command: str, options: Namespace):
        # Refuse to execute if already in venv
        assert "VIRTUAL_ENV" not in os.environ, "Already running in build environment shell; just type commands :-)"

        # Refuse to execute if not started from loading script
        assert options.from_loader is not None, f"Can't use {command} command if not invoked from loading script."

        # Always implicitely init
        self.init(options)

    def shell(self, options: Namespace):
        """
        Verify that the context is OK to run a shell, then throws a specific return code
        so that loading script is told to spawn an interactive shell.

        :param options: Input command line parsed options
        """

        # Checks
        self._command_checks("shell", options)

        # Refuse to do anything in CI
        assert not self.loader.is_ci, "Can't use shell command in CI environment."

        # Nothing more to do than telling loading script to spawn an interactive shell
        raise RCHolder(RC_START_SHELL)

    def run(self, options: Namespace):
        """
        Verify that the context is OK to run a command, then:

        * generates command script containing the command to be executed
        * throws a specific return code so that loading script is told to execute the generated command script

        :param options: Input command line parsed options
        """

        # Checks
        self._command_checks("run", options)

        # Verify command is not empty
        assert len(options.CMD) > 0, "no command provided"

        # Find a script name
        script_path = None
        script_index = None
        possible_indexes = list(range(_RC_RUN_CMD, _RC_MAX + 1))
        while script_path is None:
            # Candidate script name
            candidate_index = random.choice(possible_indexes)
            candidate_script = self.project_script_path / f"command.{candidate_index}.{options.from_loader}"

            # Script not already used?
            if not candidate_script.is_file():
                script_path = candidate_script
                script_index = candidate_index
            else:
                # Security to avoid infinite loop
                # Command script is supposed to be deleted by loading script, but "just in case"...
                # (e.g. launched command killed without giving a chance to remove the file)
                possible_indexes.remove(candidate_index)
                assert len(possible_indexes) > 0, "[internal] can't find any available command script number"

        # Generate command script
        self.renderer.render(f"command.{options.from_loader}.jinja", script_path, executable=True, keywords={"command": " ".join(options.CMD)})

        # Tell loading script about command script ID
        raise RCHolder(script_index)

    def upgrade(self, options: Namespace):
        """
        Upgrade python venv installed packages to latest version

        :param options: Input command line parsed options
        """

        # Delegate upgrade to pip
        eager = False if not hasattr(options, "eager") else options.eager

        # Iterate on packages to be installed (default ones + requirement files, if any)
        for to_install in [self.loader.default_packages] + (
            [["-r", self.loader.requirements_file]] if (self.project_path / self.loader.requirements_file).is_file() else []
        ):
            subprocess.run(
                [str(sys.executable), "-m", "pip", "install", "--upgrade"]
                + (["--upgrade-strategy=eager"] if eager else [])  # Change upgrade strategy if specified
                + to_install
                + self.loader.pip_args.split(" "),
                cwd=self.project_path,
                check=True,
            )
