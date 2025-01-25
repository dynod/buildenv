import os
import stat
from pathlib import Path

from .shell import EnvShell


# Bash shell implementation
class BashShell(EnvShell):
    def __init__(self, venv_bin: Path, fake_pip: bool, backend_name: str):
        super().__init__(venv_bin, fake_pip, backend_name)
        self._shell_path = os.getenv("SHELL")

    @property
    def name(self) -> str:
        return "bash"

    def get_args_interractive(self, tmp_dir: Path) -> list[str]:
        return [self._shell_path, "--rcfile", str(tmp_dir / "shell.sh")]

    def get_args_command(self, tmp_dir: Path) -> list[str]:
        return [self._shell_path, "-c", str(tmp_dir / "command.sh")]

    def generate_activation_scripts(self, tmp_dir: Path, command: str):
        # Root files
        self.render("bash/activate.sh.jinja", tmp_dir / "activate.sh")  # Main activation file
        if command:
            self.render("bash/command.sh.jinja", tmp_dir / "command.sh", keywords={"command": command}, executable=True)  # Command execution file
        else:
            self.render("bash/shell.sh.jinja", tmp_dir / "shell.sh")  # Shell activation file

        # Completion handling
        self.render(
            "bash/completion.sh.jinja", tmp_dir / "activate" / "completion.sh", keywords={"commands": ["buildenv"]}
        )  # TODO: Handle completion for commands registered from plugins

        # Generate fake pip if required
        if self._fake_pip:
            self.render("bash/pip.sh.jinja", tmp_dir / "bin" / "pip", executable=True)

    @property
    def header(self) -> str:
        return "#!/bin/bash\n"

    @property
    def new_line(self) -> str:
        return "\n"

    @property
    def comment_prefix(self) -> str:
        return "# "

    def render(self, template, target, executable=False, keywords=None):
        # Super call
        super().render(template, target, executable, keywords)

        # Make script executable if required
        if executable:
            # System chmod
            target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

            # TODO Git chmod: only if not a .buildenv relative script (not persisted on git)
            # try:
            #     rel_path = target.relative_to(self.project_path)
            # except ValueError:  # pragma: no cover
            #     rel_path = None
            # if (target.parent != self.project_script_path) and (rel_path is not None):
            #     cp = subprocess.run(["git", "update-index", "--chmod=+x", str(rel_path)], capture_output=True, check=False, cwd=self.project_path)
            #     if cp.returncode != 0:
            #         self._logger.warning(f"Failed to chmod {target.name} file with git (file not in index yet, or maybe git not installed?)")
