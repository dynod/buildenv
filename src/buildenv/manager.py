import sys
from pathlib import Path
from typing import List

from jinja2 import Template

from buildenv.loadme import BUILDENV_FOLDER

MODULE_FOLDER = Path(__file__).parent
"""Path to buildenv module"""

TEMPLATES_FOLDER = MODULE_FOLDER / "templates"
"""Path to bundled template files"""

COMMENT_PER_TYPE = {".py": "# "}
"""Map of comment styles per file extension"""

NEWLINE_PER_TYPE = {".py": None}
"""Map of newline styles per file extension"""


class BuildEnvManager:
    """
    **buildenv** manager entry point

    :param project_path: Path to the current project root folder
    """

    def __init__(self, project_path: Path):
        self.project_path = project_path  # Current project path
        self.buildenv_path = project_path / BUILDENV_FOLDER  # Current project buildenv path
        self.venv_path = Path(sys.executable).parent.parent  # Current project venv path

    def setup(self):
        """
        Build environment setup.

        This will:

        * copy/update loadme scripts in current project
        * prepare extra venv shell scripts folder
        * invoke extra environment initializers defined by sub-classes
        """
        self._update_scripts()

    def _render_template(self, template: List[Path], target: Path):
        """
        Render template template to target file

        :param template: Path to template file
        :param target: Target file to be generated
        """

        # Check target file suffix
        target_type = target.suffix

        # Iterate on fragments
        generated_content = ""
        for fragment in [TEMPLATES_FOLDER / "warning.jinja", template]:
            # Load template
            with fragment.open() as f:
                t = Template(f.read())
                generated_content += t.render({"comment": COMMENT_PER_TYPE[target_type]})
                generated_content += "\n\n"

        # Generate target
        with target.open("w", newline=NEWLINE_PER_TYPE[target_type]) as f:
            f.write(generated_content)

    def _update_scripts(self):
        """
        Copy/update loadme scripts in project folder
        """

        # Prepare buildenv path
        self.buildenv_path.mkdir(exist_ok=True)

        # Generate python module
        self._render_template(MODULE_FOLDER / "loadme.py", self.buildenv_path / "loadme.py")
