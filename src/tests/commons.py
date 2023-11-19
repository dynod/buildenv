import shutil
from pathlib import Path

from nmk.utils import is_windows
from pytest_multilog import TestHelper

# Venv bin directory
VENV_BIN = "Scripts" if is_windows() else "bin"


class BuildEnvTestHelper(TestHelper):
    def prepare_config(self, name: str):
        # Create buildenv folder, and copy template config file
        shutil.copyfile(Path(__file__).parent / "templates" / name, self.test_folder / "buildenv.cfg")
