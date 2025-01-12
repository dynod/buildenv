from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union

from jinja2 import Environment, PackageLoader

Keywords = dict[str, Union[str, list[str], bool, dict[str, str]]]
"""
Type for keywords used in templates
"""


class Renderer(ABC):
    """
    Base renderer class, used to render a template to a target file

    :param template: Path to template file
    :param backend_name: Name of the backend
    :param environment: Jinja2 environment to use for rendering
    """

    def __init__(self, template: Path, backend_name: str, environment: Union[Environment, None] = None):
        self._template = template
        self._backend_name = backend_name
        self._environment = environment if environment is not None else Environment(loader=PackageLoader("buildenv2", "_templates"))

    @property
    @abstractmethod
    def header(self) -> str:  # pragma: no cover
        """
        Header string for this renderer
        """
        pass

    @property
    @abstractmethod
    def new_line(self) -> str:  # pragma: no cover
        """
        New line string for this renderer
        """
        pass

    @property
    @abstractmethod
    def comment_prefix(self) -> str:  # pragma: no cover
        """
        Comment prefix string for this renderer
        """
        pass

    def render(self, target: Path, executable: bool = False, keywords: Union[Keywords, None] = None):
        """
        Render template to target file

        :param target: Target file to be generated
        :param executable: States if target file as to be set as executable
        :param keyword: Map of keywords provided to template
        """

        # Build keywords map
        all_keywords: Keywords = {
            "backend": self._backend_name,
            "header": self.header,
            "comment": self.comment_prefix,
        }
        if keywords is not None:
            all_keywords.update(keywords)

        # Render template
        generated_content = self._environment.get_template(self._template.as_posix()).render(all_keywords)

        # Create target directory if needed
        target.parent.mkdir(parents=True, exist_ok=True)

        # Generate target
        with target.open("w", newline=self.new_line) as f:
            f.write(generated_content)
