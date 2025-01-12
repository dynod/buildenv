import pytest
from pytest_multilog import TestHelper

from buildenv2.__main__ import buildenv
from buildenv2._backends.factory import EnvBackendFactory


class TestParser(TestHelper):
    def test_unknown_venv_folder(self, monkeypatch: pytest.MonkeyPatch):
        # Fake python executable
        venv_bin = self.test_folder / "fake_venv" / "bin"
        venv_bin.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(EnvBackendFactory, "_ENV_BIN", venv_bin)

        # Try to run in a folder that is not a venv
        rc = buildenv(["run", "true"])
        assert rc == 1
        self.check_logs("Can't locate venv config file")
