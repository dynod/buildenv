import sys
from pathlib import Path
from typing import List

from jinja2 import Template

from buildenv.loadme import BUILDENV_OK, LoadMe

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
/.loadme/
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
        self.venv_bin_path = venv_bin_path if venv_bin_path is not None else Path(sys.executable).parent
        self.venv_path = self.venv_bin_path.parent

        # Other initializations
        self.project_path = project_path  # Current project path
        self.project_script_path = self.project_path / ".loadme"  # Current project generated scripts path
        self.loader = LoadMe(self.project_path)  # Loader instance
        self.is_windows = (self.venv_bin_path / "activate.bat").is_file()  # Is Windows venv?

        # Relative venv bin path for local scripts
        try:
            self.relative_venv_bin_path = self.venv_bin_path.relative_to(self.project_path)
        except ValueError:  # pragma: no cover
            # Venv is not relative to project; don't care, use the full path
            self.relative_venv_bin_path = self.venv_bin_path

    def setup(self):
        """
        Build environment setup.

        This will:

        * copy/update loadme scripts in current project
        * verify recommended git files
        * invoke extra environment initializers defined by sub-classes
        * mark buildenv as ready
        """
        self._update_scripts()
        self._verify_git_files()
        self._make_ready()

    def _render_template(self, template: List[Path], target: Path):
        """
        Render template template to target file

        :param template: Path to template file
        :param target: Target file to be generated
        """

        # Create target directory if needed
        target.parent.mkdir(parents=True, exist_ok=True)

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
                        "venvBinPath": str(self.relative_venv_bin_path),
                    }
                )
                generated_content += "\n\n"

        # Generate target
        with target.open("w", newline=_NEWLINE_PER_TYPE[target_type]) as f:
            f.write(generated_content)

    def _update_scripts(self):
        """
        Copy/update loadme scripts in project folder
        """

        # Generate all scripts
        self._render_template(_MODULE_FOLDER / "loadme.py", self.project_path / "loadme.py")
        self._render_template(_TEMPLATES_FOLDER / "loadme.sh.jinja", self.project_path / "loadme.sh")
        self._render_template(_TEMPLATES_FOLDER / "loadme.cmd.jinja", self.project_path / "loadme.cmd")
        self._render_template(_TEMPLATES_FOLDER / "activate.sh.jinja", self.project_script_path / "activate.sh")
        if self.is_windows:
            # Only if venv files are generated for Windows
            self._render_template(_TEMPLATES_FOLDER / "activate.cmd.jinja", self.project_script_path / "activate.cmd")

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
