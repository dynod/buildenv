import os
import shutil
from pathlib import Path
from typing import Union

import pytest
from nmk.utils import is_windows
from pytest_multilog import TestHelper

# Venv bin directory
VENV_BIN = "Scripts" if is_windows() else "bin"


class BuildEnvTestHelper(TestHelper):
    def prepare_config(self, name: str, dest: Path = None):
        # Create buildenv folder, and copy template config file
        shutil.copyfile(Path(__file__).parent / "templates" / name, (self.test_folder if dest is None else dest) / "buildenv.cfg")

    def remove_env(self, name: str) -> Union[str, None]:
        # Remove environment var and remember previous value
        if name in os.environ:
            old_value = os.environ[name]
            del os.environ[name]
        else:
            old_value = None
        return old_value

    def set_env(self, name: str, value: str) -> Union[str, None]:
        # Remove environment var and remember previous value
        if name in os.environ:
            old_value = os.environ[name]
        else:
            old_value = None
        os.environ[name] = value
        return old_value

    def restore_env(self, name: str, previous_value: Union[str, None]):
        # Restore previous env value
        if previous_value is not None:
            os.environ[name] = previous_value
        elif name in os.environ:
            del os.environ[name]

    @pytest.fixture
    def fake_no_venv(self):
        # Fake environment without venv
        old_value = self.remove_env("VIRTUAL_ENV")

        # yield to test
        yield

        # Restore previous environment
        self.restore_env("VIRTUAL_ENV", old_value)

    @pytest.fixture
    def fake_venv(self):
        # Fake environment with venv
        old_value = self.set_env("VIRTUAL_ENV", "/foo/bar")

        # yield to test
        yield

        # Restore previous environment
        self.restore_env("VIRTUAL_ENV", old_value)

    @pytest.fixture
    def fake_ci(self):
        # Fake CI environment
        old_value = self.set_env("CI", "true")

        # yield to test
        yield

        # Restore previous environment
        self.restore_env("CI", old_value)

    @pytest.fixture
    def fake_local(self):
        # Fake local environment
        old_value = self.remove_env("CI")

        # yield to test
        yield

        # Restore previous environment
        self.restore_env("CI", old_value)
