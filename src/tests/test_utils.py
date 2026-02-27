import platform

import pytest
from pytest_multilog import TestHelper

from buildenv._utils import is_windows, run_subprocess


class TestUtils(TestHelper):
    def test_is_windows(self):
        assert is_windows() == (platform.system() == "Windows")

    def test_subprocess_error_msg(self):
        cp = run_subprocess(["python", "-c", "import sys; sys.exit(123)"], check=False, error_msg="Expected error message")
        assert cp.returncode == 123
        self.check_logs("Expected error message")

    def test_subprocess_error_check(self):
        with pytest.raises(RuntimeError, match="command returned 123"):
            run_subprocess(["python", "-c", "import sys; sys.exit(123)"])
