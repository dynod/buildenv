import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from nmk.utils import is_windows

from buildenv import __version__
from tests.commons import BuildEnvTestHelper


class TestFunctional(BuildEnvTestHelper):
    def check_generated_buildenv(self, buildenv: Path):
        exts = ["cmd", "sh"] if is_windows() else ["sh"]
        dot_buildenv = buildenv / ".buildenv"
        expected = [dot_buildenv / f"{n}.{e}" for n in ["shell", "activate"] for e in exts]
        logging.info(f"expected files: {expected}")
        found = list(filter(lambda f: f.is_file(), dot_buildenv.glob("*")))
        logging.info(f"found files: {found}")
        for exp_file in expected:
            assert exp_file.is_file(), f"expected {exp_file}, but not found in {found}"
        assert len(found) == len(expected)

    @pytest.fixture
    def buildenv(self) -> Path:
        # Test buildenv folder
        buildenv = self.test_folder / "test"
        if buildenv.is_dir():
            shutil.rmtree(buildenv)
        buildenv.mkdir()

        yield buildenv

        # If venv exists, remove it (to avoid having it stored in output archive in CI)
        venv = buildenv / "venv"
        if "CI" in os.environ and venv.is_dir():
            shutil.rmtree(venv)

    def test_main(self, buildenv):
        # Copy loader python script
        src_loader = Path(__file__).parent.parent / "buildenv" / "loader.py"
        tgt_loader = buildenv / "buildenv-loader.py"
        shutil.copy(src_loader, tgt_loader)

        # Copy config to disable git look up
        self.prepare_config("buildenv-dontLookUp.cfg", buildenv)

        # Build requirements file to install built buildenv wheel (not the pypi one)
        buildenv_wheel = Path(__file__).parent.parent.parent / f"out/artifacts/buildenv-{__version__}-py3-none-any.whl"
        assert buildenv_wheel.is_file(), "buildenv wheel not found"
        with (buildenv / "requirements.txt").open("w") as f:
            f.write(str(buildenv_wheel))

        # Setup buildenv
        cp = subprocess.run([sys.executable, str(tgt_loader)], cwd=buildenv, check=False, capture_output=True)
        logging.info("loader stdout:\n" + "\n".join(cp.stdout.decode().splitlines()))
        logging.info("loader stderr:\n" + "\n".join(cp.stderr.decode().splitlines()))
        assert cp.returncode == 0, f"Buildenv setup failed: {cp.returncode}"

        # Check for generated files
        self.check_generated_buildenv(buildenv)

        # Run some command through loading script
        if is_windows():
            args = ["cmd", "/c", f"{buildenv / 'buildenv.cmd'} run echo hello from buildenv"]
        else:
            args = [f"{buildenv / 'buildenv.sh'}", "run", "echo", "hello from buildenv"]
        new_env = dict(os.environ)
        new_env.pop("VIRTUAL_ENV", None)
        cp = subprocess.run(args, cwd=buildenv, check=False, capture_output=True, env=new_env)
        output = cp.stdout.decode().splitlines()
        logging.info("buildenv run stdout:\n" + "\n".join(output))
        logging.info("buildenv run stderr:\n" + "\n".join(cp.stderr.decode().splitlines()))
        assert cp.returncode == 0, f"Buildenv run failed: {cp.returncode}"
        assert "hello from buildenv" in output, f"Hello string not found in {output}"

        # Check for generated files (generated run script shall be removed by loading script)
        self.check_generated_buildenv(buildenv)
