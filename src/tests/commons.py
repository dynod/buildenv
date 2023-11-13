import shutil
from pathlib import Path

from pytest_multilog import TestHelper


class BuildEnvTestHelper(TestHelper):
    def prepare_config(self, name: str):
        # Create buildenv folder, and copy template config file
        shutil.copyfile(Path(__file__).parent / "templates" / name, self.test_folder / "buildenv.cfg")
