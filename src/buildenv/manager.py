import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import List

from jinja2 import Template

from buildenv.loader import BuildEnvLoader

BUILDENV_OK = "buildenvOK"
"""Valid buildenv tag file"""

# Path to buildenv module
_MODULE_FOLDER = Path(__file__).parent

# Path to bundled template files
_TEMPLATES_FOLDER = _MODULE_FOLDER / "templates"

# Map of comment styles per file extension
_COMMENT_PER_TYPE = {".py": "# ", ".sh": "# ", ".cmd": ":: "}

# Map of newline styles per file extension
_NEWLINE_PER_TYPE = {".py": None, ".sh": "\n", ".cmd": "\r\n"}

# Map of file header per file extension
_HEADERS_PER_TYPE = {".py": "", ".sh": "#!/usr/bin/bash\n", ".cmd": "@ECHO OFF\n"}

# Recommended git files
_RECOMMENDED_GIT_FILES = {
    ".gitignore": """/venv/
/.buildenv/
""",
    ".gitattributes": """*.sh text eol=lf
*.bat text eol=crlf
*.cmd text eol=crlf
""",
}


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

        try:
            # Relative venv bin path string for local scripts
            self.relative_venv_bin_path = self.venv_bin_path.relative_to(self.project_path)
        except ValueError:
            # Venv is not relative to current project: reverse logic
            upper_levels_count = len(self.project_path.relative_to(self.venv_root_path).parts)
            self.relative_venv_bin_path = Path(os.pardir)
            for part in [os.pardir] * (upper_levels_count - 1) + [self.venv_path.name, self.venv_bin_path.name]:
                self.relative_venv_bin_path /= part

    def setup(self):
        """
        Build environment setup.

        This setup method always generates loading scripts in current project folder.

        If the buildenv is not marked as ready yet, this method also:

        * verify recommended git files
        * invoke extra environment initializers defined by sub-classes
        * mark buildenv as ready

        Finally, this method spawns a new shell with buildenv loaded
        """

        # Always update script
        self._update_scripts()

        # Refresh buildenv if not done yet
        if not ((self.venv_path / BUILDENV_OK)).is_file():
            print(">> Customizing buildenv...")
            self._verify_git_files()
            self._make_ready()

        # Spawn to new shell process
        self._spawn()

    def _render_template(self, template: List[Path], target: Path, executable: bool = False):
        """
        Render template template to target file

        :param template: Path to template file
        :param target: Target file to be generated
        """

        # Check target file suffix
        target_type = target.suffix

        # Iterate on fragments
        generated_content = ""
        for fragment in [_TEMPLATES_FOLDER / "warning.jinja", template]:
            # Load template
            with fragment.open() as f:
                t = Template(f.read())
                generated_content += t.render(
                    {
                        "header": _HEADERS_PER_TYPE[target_type],
                        "comment": _COMMENT_PER_TYPE[target_type],
                        "windowsPython": self.loader.read_config("windowsPython", "python"),
                        "linuxPython": self.loader.read_config("linuxPython", "python3"),
                        "windowsVenvBinPath": str(self.relative_venv_bin_path).replace("/", "\\"),
                        "linuxVenvBinPath": str(self.relative_venv_bin_path).replace("\\", "/"),
                    }
                )
                generated_content += "\n\n"

        # Create target directory if needed
        target.parent.mkdir(parents=True, exist_ok=True)

        # Generate target
        with target.open("w", newline=_NEWLINE_PER_TYPE[target_type]) as f:
            f.write(generated_content)

        # Make script executable if required
        if executable:
            target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    def _update_scripts(self):
        """
        Copy/update loading scripts in project folder
        """

        # Generate all scripts
        self._render_template(_MODULE_FOLDER / "loader.py", self.project_path / "buildenv-loader.py")
        self._render_template(_TEMPLATES_FOLDER / "buildenv.sh.jinja", self.project_path / "buildenv.sh", executable=True)
        self._render_template(_TEMPLATES_FOLDER / "buildenv.cmd.jinja", self.project_path / "buildenv.cmd")
        self._render_template(_TEMPLATES_FOLDER / "activate.sh.jinja", self.project_script_path / "activate.sh")
        self._render_template(_TEMPLATES_FOLDER / "shell.sh.jinja", self.project_script_path / "shell.sh")
        if self.is_windows:
            # Only if venv files are generated for Windows
            self._render_template(_TEMPLATES_FOLDER / "activate.cmd.jinja", self.project_script_path / "activate.cmd")
            self._render_template(_TEMPLATES_FOLDER / "shell.cmd.jinja", self.project_script_path / "shell.cmd")

    def _verify_git_files(self):
        """
        Check for recommended git files, and display warning if they're missing
        """
        for file, content in _RECOMMENDED_GIT_FILES.items():
            if not (self.project_path / file).is_file():
                print(f">> WARNING: missing {file} file in project", "   Recommended content is:", "", content, sep="\n", file=sys.stderr)

    def _make_ready(self):
        """
        Just touch "buildenv ready" file
        """
        print(">> Build venv is ready!")
        (self.venv_path / BUILDENV_OK).touch()

    def _spawn(self):
        """
        Spawn a new shell
        """

        # Prepare shell args
        is_linux_shell = "SHELL" in os.environ
        shell_script = (self.project_script_path / ("shell.sh" if is_linux_shell else "shell.cmd")).relative_to(self.project_path)
        args = [os.environ["SHELL"], "--rcfile", shell_script.as_posix()] if is_linux_shell else ["cmd", "/k", str(shell_script)]

        # Spawn shell subprocess
        subprocess.run(args, cwd=self.project_path, check=False)
