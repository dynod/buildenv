import os
import random
import sys
from argparse import Namespace
from pathlib import Path
from typing import Dict

import pkg_resources

from buildenv._internal.parser import RCHolder
from buildenv._internal.render import RC_START_SHELL, TemplatesRenderer
from buildenv.extension import BuildEnvExtension
from buildenv.loader import BuildEnvLoader

BUILDENV_OK = "buildenvOK"
"""Valid buildenv tag file"""

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
    :param venv_bin_path: Path to venv binary folder to be used (mainly for test purpose; if None, will use current executable venv)
    """

    def __init__(self, project_path: Path, venv_bin_path: Path = None):
        # Deal with venv paths
        self.venv_bin_path = venv_bin_path if venv_bin_path is not None else Path(sys.executable).parent  # Bin path
        self.venv_path = self.venv_bin_path.parent  # Venv path
        self.venv_root_path = self.venv_path.parent  # Parent project path (may be the current one or a parent folder one)

        # Other initializations
        self.project_path = project_path  # Current project path
        self.project_script_path = self.project_path / ".buildenv"  # Current project generated scripts path
        self.loader = BuildEnvLoader(self.project_path)  # Loader instance
        self.is_windows = (self.venv_bin_path / "activate.bat").is_file()  # Is Windows venv?
        self.venv_context = self.loader.setup_venv(self.venv_bin_path.parent)

        # Private data
        self._completion_commands = set()
        self.register_completion("buildenv")

        try:
            # Relative venv bin path string for local scripts
            relative_venv_bin_path = self.venv_bin_path.relative_to(self.project_path)

            # Venv is relative to current project
            self.is_project_venv = True
        except ValueError:
            # Venv is not relative to current project: reverse logic
            upper_levels_count = len(self.project_path.relative_to(self.venv_root_path).parts)
            relative_venv_bin_path = Path(os.pardir)
            for part in [os.pardir] * (upper_levels_count - 1) + [self.venv_path.name, self.venv_bin_path.name]:
                relative_venv_bin_path /= part

            # Venv is *not* relative to current project
            self.is_project_venv = False

        # Prepare template renderer
        self.renderer = TemplatesRenderer(self.loader, relative_venv_bin_path)

    def init(self, options: Namespace = None):
        """
        Build environment initialization.

        This method always generates loading scripts in current project folder.

        If the buildenv is not marked as ready yet, this method also:

        * verify recommended git files
        * invoke extra environment initializers defined by sub-classes
        * mark buildenv as ready

        :param options: Input command line parsed options
        """

        # Always update script
        self._update_scripts()

        # Check for git files if they don't exist
        self._verify_git_files()

        # Make sure we're not updating a parent build env
        assert self.is_project_venv, f"Can't update a parent project buildenv; please update buildenv in {self.venv_path.parent} folder"

        # Handle entry points
        self._run_entry_points()

        # Refresh buildenv if not done yet
        if not (self.venv_path / BUILDENV_OK).is_file():
            print(">> Customizing buildenv...")

            # Delegate to sub-methods
            self._add_activation_files()
            self._make_ready()

    # Copy/update loading scripts in project folder
    def _update_scripts(self):
        # Generate all scripts
        self.renderer.render(_MODULE_FOLDER / "loader.py", self.project_path / "buildenv-loader.py")
        self.renderer.render("buildenv.sh.jinja", self.project_path / "buildenv.sh", executable=True)
        self.renderer.render("buildenv.cmd.jinja", self.project_path / "buildenv.cmd")
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
                print(f">> WARNING: missing {file} file in project; generating a default one")
                self.renderer.render(f"{file[1:]}.jinja", self.project_path / file)

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
        next_index = max(int(n.name[0:2]) for n in self.venv_context.activation_scripts_folder.glob(f"*{extension}")) + 1

        # Build script name
        script_name = self.venv_context.activation_scripts_folder / f"{next_index:02}_{name}{extension}"

        # Generate from template
        self.renderer.render(template, script_name, keywords=keywords)

    # Iterate on entry points to delegate init to buildenv extensions
    def _run_entry_points(self):
        # Build entry points map (to handle duplicate names)
        all_entry_points = {}
        for p in pkg_resources.iter_entry_points("buildenv_init"):
            all_entry_points[p.name] = p

        # Iterate on entry points
        for name, point in all_entry_points.items():
            # Check if init was already done
            init_file = self.venv_path / f"{name}OK"
            if init_file.is_file():
                # Skip this one, already done
                continue

            # Get initializer, and verify type
            print(f"  >> with {name} extension")
            # Instantiate and call init method
            try:
                initializer = point.load()
                assert issubclass(initializer, BuildEnvExtension), f"{name} extension class is not extending buildenv.BuildEnvExtension"
            except Exception as e:
                raise AssertionError(f"Failed to load {name} extension: {e}")

            # Instantiate and call init method
            try:
                initializer(self).init()
            except Exception as e:
                raise AssertionError(f"Failed to execute {name} extension init: {e}")

            # Init ok: touch init file
            init_file.touch()

    # Just touch "buildenv ready" file
    def _make_ready(self):
        print(">> Buildenv is ready!")
        (self.venv_path / BUILDENV_OK).touch()

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
        self.renderer.render(f"command.{options.from_loader}.jinja", script_path, True, {"command": " ".join(options.CMD)})

        # Tell loading script about command script ID
        raise RCHolder(script_index)
