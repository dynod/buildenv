import pytest

from buildenv.__main__ import buildenv
from buildenv.backends.factory import EnvBackendFactory
from tests.commons2 import PreservedEnvHelper


class TestParser(PreservedEnvHelper):
    def test_unknown_venv_folder(self, monkeypatch: pytest.MonkeyPatch):
        # Fake python executable
        venv_bin = self.test_folder / "fake_venv" / "bin"
        venv_bin.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(EnvBackendFactory, "_ENV_BIN", venv_bin)

        # Try to run in a folder that is not a venv
        rc = buildenv(["run", "true"])
        assert rc == 1
        self.check_logs("Can't locate venv config file")

    def test_legacy_init_new(self):
        # Try deprecated "buildenv init --new" command
        rc = buildenv(["init", "--new"])
        assert rc == 1
        self.check_logs("'buildenv init --new' syntax is deprecated")
