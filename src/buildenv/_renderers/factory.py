import logging
import stat
from pathlib import Path

from jinja2 import Environment

from .._utils import run_subprocess
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

    def render(self, target: Path, executable: bool = False, keywords: Keywords | None = None):
        # Super call
        super().render(target, executable, keywords)

        # Make script executable if required
        if executable:
            # System chmod
            target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

            # Got a project root?
            if (self._project_path is not None) and (target.is_relative_to(self._project_path)):
                relative_target = target.relative_to(self._project_path)

                # Git add
                run_subprocess(["git", "add", str(relative_target)], cwd=self._project_path, error_msg=f"Failed to add {relative_target} to git index")

                # Git chmod
                run_subprocess(
                    ["git", "update-index", "--chmod=+x", str(relative_target)],
                    cwd=self._project_path,
                    error_msg=f"Failed to set executable flag for {relative_target} in git index",
                )


# Renderer factory
class RendererFactory:
    @staticmethod
    def create(
        template: Path, backend_name: str, environment: Environment | None = None, project_path: Path | None = None, logger: logging.Logger | None = None
    ) -> Renderer:
        """
        Create a renderer for the given template

        :param template: Template file to render
        :param backend_name: Backend name
        :param environment: Jinja2 environment to use for rendering
        :param project_path: Path to the project root for this rendering operation
        :param logger: Logger to use for this rendering operation
        """
        if template.suffixes == [".cmd", ".jinja"]:
            return _CmdRenderer(template, backend_name, environment, project_path, logger)
        elif template.suffixes == [".sh", ".jinja"]:
            return _ShRenderer(template, backend_name, environment, project_path, logger)
        else:
            return _DefaultRenderer(template, backend_name, environment, project_path, logger)
