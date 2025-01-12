import platform

from pytest_multilog import TestHelper

from buildenv2._utils import is_windows


class TestUtils(TestHelper):
    def test_is_windows(self):
        assert is_windows() == (platform.system() == "Windows")
