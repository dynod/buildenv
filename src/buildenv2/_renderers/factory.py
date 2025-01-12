import stat
from pathlib import Path
from typing import Union

from jinja2 import Environment

from .renderer import Keywords, Renderer


# Default renderer used for non specific files
class _DefaultRenderer(Renderer):
    @property
    def header(self) -> str:
        return ""

    @property
    def new_line(self) -> str:
        return "\n"

    @property
    def comment_prefix(self) -> str:
        return "# "


# Cmd files renderer
class _CmdRenderer(Renderer):
    @property
    def header(self) -> str:
        return "@ECHO OFF\n"

    @property
    def new_line(self) -> str:
        return "\r\n"

    @property
    def comment_prefix(self) -> str:
        return ":: "


# Sh files renderer
class _ShRenderer(Renderer):
    @property
    def header(self) -> str:
        return "#!/usr/bin/bash\n"

    @property
    def new_line(self) -> str:
        return "\n"

    @property
    def comment_prefix(self) -> str:
        return "# "

    def render(self, target: Path, executable: bool = False, keywords: Union[Keywords, None] = None):
        # Super call
        super().render(target, executable, keywords)

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


# Renderer factory
class RendererFactory:
    @staticmethod
    def create(template: Path, backend_name: str, environment: Union[Environment, None] = None) -> Renderer:
        """
        Create a renderer for the given template

        :param template: Template file to render
        :param backend_name: Backend name
        """
        if template.suffixes == [".cmd", ".jinja"]:
            return _CmdRenderer(template, backend_name, environment)
        elif template.suffixes == [".sh", ".jinja"]:
            return _ShRenderer(template, backend_name, environment)
        else:
            return _DefaultRenderer(template, backend_name, environment)
