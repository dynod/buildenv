from pathlib import Path
from typing import List

from buildenv.__main__ import buildenv
from buildenv.manager import BUILDENV_OK
from tests.commons import VENV_BIN, BuildEnvTestHelper


class TestBuildenvParser(BuildEnvTestHelper):
    @property
    def venv_bin(self) -> Path:
        return self.test_folder / "venv" / VENV_BIN

    def run_buildenv(self, args: List[str]) -> int:
        self.venv_bin.mkdir(parents=True)
        return buildenv(args, self.test_folder, self.venv_bin)

    def test_default_cmd_no_loader(self):
        # Default command without loader: init
        rc = self.run_buildenv([])
        assert rc == 0
        assert (self.venv_bin.parent / BUILDENV_OK).is_file()

    def test_default_cmd_with_loader(self):
        # Default command without loader: shell
        rc = self.run_buildenv(["--from-loader"])
        assert rc == 100
        assert (self.venv_bin.parent / BUILDENV_OK).is_file()

    def test_shell_cmd_with_loader(self):
        # shell command with loader
        rc = self.run_buildenv(["shell"])
        assert rc == 1
        assert not (self.venv_bin.parent / BUILDENV_OK).is_file()
