import shutil
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
        activate = self.venv_bin / "activate.d"
        activate.mkdir(parents=True, exist_ok=True)
        (activate / "00_activate.sh").touch()
        (activate / "00_activate.bat").touch()
        return buildenv(args, self.test_folder, self.venv_bin)

    def test_default_cmd_no_loader(self):
        # Default command without loader: init
        rc = self.run_buildenv([])
        assert rc == 0
        assert (self.venv_bin.parent / BUILDENV_OK).is_file()

    def test_default_cmd_with_loader(self, fake_no_venv):
        # Default command without loader: shell
        rc = self.run_buildenv(["--from-loader=xx"])
        assert rc == 100
        assert (self.venv_bin.parent / BUILDENV_OK).is_file()

    def test_shell_cmd_without_loader(self):
        # shell command with loader
        rc = self.run_buildenv(["shell"])
        assert rc == 1
        assert not (self.venv_bin.parent / BUILDENV_OK).is_file()

    def test_run_cmd_with_loader(self, fake_no_venv):
        # run command with loader
        rc = self.run_buildenv(["--from-loader=sh", "run", "true"])
        assert rc > 100
        assert (self.venv_bin.parent / BUILDENV_OK).is_file()
        assert (self.test_folder / ".buildenv" / f"command.{rc}.sh").is_file()

    def test_run_cmd_with_loader_existing_cmd_files(self, fake_no_venv):
        # Touch all possible command files but one
        be = self.test_folder / ".buildenv"
        if be.is_dir():
            shutil.rmtree(be)
        be.mkdir()
        for rc in range(101, 175):
            (be / f"command.{rc}.sh").touch()
        for rc in range(176, 256):
            (be / f"command.{rc}.sh").touch()

        # run command with loader
        rc = self.run_buildenv(["--from-loader=sh", "run", "true"])
        assert rc == 175
        assert (self.venv_bin.parent / BUILDENV_OK).is_file()
        assert (self.test_folder / ".buildenv" / f"command.{rc}.sh").is_file()

        # Next try will return an error (no more candidate IDs)
        rc = self.run_buildenv(["--from-loader=sh", "run", "true"])
        assert rc == 1
