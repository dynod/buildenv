import stat
import subprocess
from pathlib import Path
from typing import Dict

from jinja2 import Template

from buildenv.loader import NEWLINE_PER_TYPE, BuildEnvLoader, logger, to_linux_path, to_windows_path

# Path to bundled template files
_TEMPLATES_FOLDER = Path(__file__).parent.parent / "templates"

# Map of comment styles per file extension
_COMMENT_PER_TYPE = {".py": "# ", ".sh": "# ", ".cmd": ":: "}

# Map of file header per file extension
_HEADERS_PER_TYPE = {".py": "", ".sh": "#!/usr/bin/bash\n", ".cmd": "@ECHO OFF\n"}

# Return codes
RC_START_SHELL = 100  # RC used to tell loading script to spawn an interactive shell


class TemplatesRenderer:
    """
    Build env templates renderer
    """

    def __init__(self, loader: BuildEnvLoader, relative_venv_bin_path: Path, project_script_path: Path) -> None:
        self.loader = loader
        self.relative_venv_bin_path = relative_venv_bin_path
        self.project_script_path = project_script_path
        self.project_path = self.project_script_path.parent

    def render(self, template: Path, target: Path, executable: bool = False, keywords: Dict[str, str] = None):
        """
        Render template template to target file

        :param template: Path to template file
        :param target: Target file to be generated
        :param executable: States if target file as to be set as executable
        :param keyword: Map of keywords provided to template
        """

        # Check target file suffix
        target_type = target.suffix

        # Build keywords map
        windows_python = self.loader.read_config("windowsPython", "python")
        all_keywords = {
            "shWindowsPython": windows_python,
            "cmdWindowsPython": windows_python.replace("${", "%").replace("}", "%"),
            "linuxPython": self.loader.read_config("linuxPython", "python3"),
            "cmdVenvBinPath": to_windows_path(self.relative_venv_bin_path),
            "shVenvBinPath": to_linux_path(self.relative_venv_bin_path),
            "rcStartShell": RC_START_SHELL,
            "buildenvPrompt": self.loader.prompt,
            "venvName": self.relative_venv_bin_path.parent.name,
        }
        if keywords is not None:
            all_keywords.update(keywords)

        # Build fragments list
        fragments = [
            template if (isinstance(template, Path) and template.is_absolute()) else (_TEMPLATES_FOLDER / template),
        ]

        # Check for know type
        if target_type in _HEADERS_PER_TYPE and target_type in _COMMENT_PER_TYPE:
            # Known type: handle header and comments
            all_keywords.update(
                {
                    "header": _HEADERS_PER_TYPE[target_type],
                    "comment": _COMMENT_PER_TYPE[target_type],
                }
            )

            # Add warning header
            fragments.insert(0, _TEMPLATES_FOLDER / "warning.jinja")

        # Iterate on fragments
        generated_content = ""
        for fragment in fragments:
            # Load template
            with fragment.open() as f:
                t = Template(f.read())
                generated_content += t.render(all_keywords)
                generated_content += "\n\n"

        # Create target directory if needed
        target.parent.mkdir(parents=True, exist_ok=True)

        # Generate target
        newline = NEWLINE_PER_TYPE[target_type] if target_type in NEWLINE_PER_TYPE else None
        with target.open("w", newline=newline) as f:
            f.write(generated_content)

        # Make script executable if required
        if executable and target_type == ".sh":
            # System chmod
            target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

            # Git chmod: only if not a .buildenv relative script (not persisted on git)
            try:
                rel_path = target.relative_to(self.project_path)
            except ValueError:  # pragma: no cover
                rel_path = None
            if (target.parent != self.project_script_path) and (rel_path is not None):
                cp = subprocess.run(["git", "update-index", "--chmod=+x", str(rel_path)], capture_output=True, check=False, cwd=self.project_path)
                if cp.returncode != 0:
                    logger.warning(f"Failed to chmod {target.name} file with git (file not in index yet, or maybe git not installed?)")
