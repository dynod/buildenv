import logging
import os
import shutil
import subprocess
import sys
from collections.abc import Generator
from pathlib import Path
from tempfile import TemporaryDirectory
from types import TracebackType
from typing import Any

import pytest
from pytest_multilog import TestHelper

import buildenv._shells.cmd as cmd_module
import buildenv._shells.shell as buildenv_shell
from buildenv.__main__ import buildenv
from buildenv._shells.factory import BashShell, ShellFactory
from buildenv._utils import is_windows, run_subprocess, to_linux_path
from buildenv.backends import EnvBackend, EnvBackendFactory
from buildenv.backends.backend import EnvBackendWithRequirements

# Templates path
TEMPLATES = Path(__file__).parent / "templates"


class WithTmpDir(TestHelper):
    @pytest.fixture
    def tmp_dir(self, monkeypatch: pytest.MonkeyPatch, logs: None) -> Generator[Path, Any, Any]:
        # Fake temporary directory handling
        tmp_dir = self.test_folder / "tmp"
        tmp_dir.mkdir()

        class FakeTempDir:
            def __enter__(self):
                return tmp_dir

            def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None):
                pass

        # Patch temporary folder creation
        monkeypatch.setattr(buildenv_shell, "TemporaryDirectory", FakeTempDir)

        yield tmp_dir


class WithVenv(WithTmpDir):
    @pytest.fixture(autouse=True)
    def fake_venv(self, monkeypatch: pytest.MonkeyPatch, logs: None) -> Generator[Path, Any, Any]:
        # Fake python executable
        venv_bin = self.test_folder / "fake_venv" / "bin"
        venv_bin.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(EnvBackendFactory, "_ENV_BIN", venv_bin)

        # Fake venv properties
        venv_root = venv_bin.parent
        venv_cfg = venv_root / "pyvenv.cfg"
        venv_cfg.touch()

        # Restore environment (modified by backend) after test
        orig_env = os.environ.copy()
        try:
            yield venv_root
        finally:
            os.environ.clear()
            os.environ.update(orig_env)


class WithProject(TestHelper):
    def check_created_files(self, project: Path, backend: EnvBackend):
        # Check installation
        assert (project / "buildenv.sh").is_file()
        assert (project / "buildenv.cmd").is_file()
        assert (project / ".gitattributes").is_file()
        assert (project / ".gitignore").is_file() == backend.is_mutable()
        assert (project / "requirements.txt").is_file() == isinstance(backend, EnvBackendWithRequirements)

    @pytest.fixture(autouse=True)
    def fake_buildenv_version(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("BUILDENV_VERSION", "2")
        yield

    def test_version(self, backend: EnvBackend):
        # Test that backend detected version is 2
        assert backend.version == 2

    @pytest.fixture
    def fake_git_parent(self, monkeypatch: pytest.MonkeyPatch, project: Path):
        real_subprocess = subprocess.run

        def fake_run(args: list[str], *posargs: list[Any], **kwargs: dict[str, str]):  # type: ignore
            if args[:2] == ["git", "rev-parse"]:
                return subprocess.CompletedProcess[str](args, 0, stdout=str(project), stderr="")
            return real_subprocess(args, *posargs, **kwargs)  # type: ignore

        # Fake git response for parent git directory detection
        monkeypatch.setattr(subprocess, "run", fake_run)

    def test_install(self, project: Path, backend: EnvBackend, fake_git_parent: None):
        # Test installation from API + check generated files
        backend.install(packages=["sample_package"])
        self.check_created_files(project, backend)

    def test_cli_install(self, project: Path, backend: EnvBackend, fake_git_parent: None):
        # Test CLI installation from CLI + check generated files
        rc = buildenv(["install", "--backend", backend.name, "--project", str(project)])
        assert rc == 0
        self.check_created_files(project, backend)

    def test_cli_install_existing_files(self, project: Path, backend: EnvBackend, fake_git_parent: None):
        # Prepare existing files
        existing_files = (
            [".gitattributes"]
            + ([".gitignore"] if backend.is_mutable() else [])
            + (["requirements.txt"] if isinstance(backend, EnvBackendWithRequirements) else [])
        )
        for f in existing_files:
            (project / f).touch()

        # Install backend
        backend.install(packages=["sample_package"])

        # Verify existing files are still empty
        for f in existing_files:
            assert (project / f).stat().st_size == 0

    def test_lock(self, project: Path, backend: EnvBackend):
        # Test locking from API
        lockfile = backend.lock_file
        lockflag = project / "buildenv.lock"

        # Lock project
        assert not lockfile.is_file()
        assert not lockflag.is_file()
        assert not backend.is_locked
        rc = backend.lock()
        assert rc == 0
        assert lockfile.is_file()
        assert lockflag.is_file()
        assert backend.is_locked

        # Unlock project
        rc = backend.unlock()
        assert rc == 0
        if lockfile.name.startswith("uv"):
            # uv backend does not delete lockfile on unlock
            assert lockfile.is_file()
        else:
            # requirements based backends should delete lockfile on unlock
            assert not lockfile.is_file()
        assert not lockflag.is_file()
        assert not backend.is_locked

    def test_cli_lock(self, project: Path, backend: EnvBackend):
        # Test lock through shell (CLI)
        rc = buildenv(["lock", "-p", str(project)])
        assert rc == 0
        assert backend.lock_file.is_file()

    @pytest.fixture
    def expected_upgrade_cmd(self, backend: EnvBackend, project: Path) -> list[str]:
        script = "buildenv.cmd" if backend.shell_instance.name == "cmd" else "./buildenv.sh"
        return [script, "init", "--show-updates-from", str(project / "._buildenv_old_packages.json")]

    def test_upgrade(self, project: Path, backend: EnvBackend, monkeypatch: pytest.MonkeyPatch, expected_upgrade_cmd: list[str]):
        # Patch subprocess to analyse arguments
        cp: subprocess.CompletedProcess[str] | None = None
        env: dict[str, str] | None = None

        def _remember_cp(args: list[str], **kwargs: dict[str, str]) -> subprocess.CompletedProcess[str]:
            nonlocal cp
            cp = subprocess.CompletedProcess(args, 0, stdout="", stderr="")
            nonlocal env
            env = kwargs.get("env")
            return cp

        monkeypatch.setattr(subprocess, "run", lambda args, **kwargs: _remember_cp(args, **kwargs))  # type: ignore

        # Test upgrade from API
        rc = backend.upgrade()
        assert rc == 0

        # Verify subprocess.run call
        assert cp is not None, "Subprocess was not called"
        assert cp.args == expected_upgrade_cmd, f"Got args: {cp.args} instead of {expected_upgrade_cmd}"
        if hasattr(backend, "_backend_upgrade_env"):
            expected_upgrade_shell_env = backend._backend_upgrade_env()
            if expected_upgrade_shell_env is not None:
                assert env is not None, "No env captured"
                env_name, env_arg = expected_upgrade_shell_env
                assert env_arg in env.get(env_name, ""), f"Bad env: {env.get(env_name, '')}"

    def test_cli_list(self, project: Path):
        # Test listing installed packages through shell (CLI)
        rc = buildenv(["list"])
        assert rc == 0


class WithToolsProject(WithProject):
    @pytest.fixture(autouse=True)
    def project(self) -> Generator[Path, Any, Any]:
        # Fake tools project
        tools_project = self.test_folder / "tools_project"
        tools_project.mkdir(parents=True, exist_ok=True)
        yield tools_project


class WithPythonProject(WithProject):
    @pytest.fixture(autouse=True)
    def project(self) -> Generator[Path, Any, Any]:
        # Test folder is a python project
        shutil.copy(TEMPLATES / "pyproject-simple.toml", self.test_folder / "pyproject.toml")
        yield self.test_folder

    @pytest.fixture
    def expected_project_install_editable_cmd(self, backend: EnvBackend) -> list[str]:
        raise NotImplementedError()

    @pytest.fixture
    def expected_project_install_non_editable_cmd(self, backend: EnvBackend) -> list[str]:
        raise NotImplementedError()


class WithUvVenv(WithVenv):
    @pytest.fixture(autouse=True)
    def with_uv(self, fake_venv: Path):
        # Fake uv property
        with (fake_venv / "pyvenv.cfg").open("w") as f:
            f.write("uv = xxx\n")


class WithUvxVenv(WithUvVenv):
    @pytest.fixture
    def backend(self, project: Path, shell_name: str) -> Generator[EnvBackend, Any, Any]:
        backend = EnvBackendFactory.detect(project, shell_name=shell_name)
        assert backend.venv_name == ""
        assert backend.use_requirements
        yield backend


class WithUvx(WithUvxVenv, WithToolsProject):
    pass


class WithPipxVenv(WithVenv):
    @pytest.fixture(autouse=True)
    def with_pipx(self, fake_venv: Path):
        # Fake pipx metadata
        (fake_venv / "pipx_metadata.json").touch()


class FakeBash(WithTmpDir):
    def get_extra_expected_files(self) -> list[str]:
        # To be overridden by subclasses
        return []

    def _check_generated_files(self, backend: EnvBackend, tmp_dir: Path, specific_files: list[str]):
        # Verify generated files
        expected_files = (
            specific_files
            + ["activate.sh", "activate/completion.sh", "activate/readme.sh"]
            + (["bin/pip"] if not backend.has_pip() else [])
            + self.get_extra_expected_files()
        )
        assert len(list(filter(lambda f: f.is_file(), tmp_dir.rglob("*")))) == len(expected_files)
        for f in expected_files:
            assert (tmp_dir / f).is_file()

        # Check for completion commands
        completion_script_content = (tmp_dir / "activate/completion.sh").read_text().splitlines()
        for cmd in backend._completions:  # type: ignore
            assert cmd.get_command() in completion_script_content

    @pytest.fixture
    def patch_shell_process(self, tmp_dir: Path, backend: EnvBackend, monkeypatch: pytest.MonkeyPatch):
        # Check shell name
        assert backend.shell_instance.name == "bash"

        # Patch subprocess to analyse arguments
        cp: subprocess.CompletedProcess[str] | None = None

        def _remember_cp(args: list[str], **kwargs: dict[str, str]):
            nonlocal cp
            cp = subprocess.CompletedProcess(args, 0, stdout="", stderr="")
            return cp

        monkeypatch.setattr(subprocess, "run", lambda args, **kwargs: _remember_cp(args, **kwargs))  # type: ignore

        # Yield to test
        yield

        # Verify subprocess.run call
        assert isinstance(backend.shell_instance, BashShell)
        bash_path = backend.shell_instance._shell_path  # type: ignore
        assert bash_path.endswith("\\bash.exe" if is_windows() else "/bash"), f"Unexpected shell path: {bash_path}"
        assert cp is not None, "Subprocess was not called"
        assert cp.args == [bash_path, "--rcfile", to_linux_path(tmp_dir / "shell.sh")]

        # Verify generated files
        self._check_generated_files(backend, tmp_dir, ["shell.sh"])

    @pytest.fixture
    def patch_run_process(self, tmp_dir: Path, backend: EnvBackend, monkeypatch: pytest.MonkeyPatch):
        # Patch subprocess to analyse arguments
        cp: subprocess.CompletedProcess[str] | None = None

        def _remember_cp(args: list[str], **kwargs: dict[str, str]) -> subprocess.CompletedProcess[str]:
            nonlocal cp
            cp = subprocess.CompletedProcess(args, 0, stdout="", stderr="")
            return cp

        monkeypatch.setattr(subprocess, "run", lambda args, **kwargs: _remember_cp(args, **kwargs))  # type: ignore

        # Yield to test
        yield

        # Verify subprocess.run call
        assert isinstance(backend.shell_instance, BashShell)
        bash_path = backend.shell_instance._shell_path  # type: ignore
        assert bash_path.endswith("\\bash.exe" if is_windows() else "/bash"), f"Unexpected shell path: {bash_path}"
        assert cp is not None, "Subprocess was not called"
        assert cp.args == [bash_path, "-c", to_linux_path(tmp_dir / "command.sh")]

        # Verify generated files
        self._check_generated_files(backend, tmp_dir, ["command.sh"])


class WithBash(FakeBash):
    @pytest.fixture
    def shell_name(self) -> str:
        return "bash"

    @pytest.fixture
    def fake_multi_level(self):
        # Prepare multi-level buildenv
        old_level = os.getenv("BUILDENV_LEVEL", None)
        os.environ["BUILDENV_LEVEL"] = "2"
        yield
        if old_level is not None:
            os.environ["BUILDENV_LEVEL"] = old_level
        else:
            del os.environ["BUILDENV_LEVEL"]

    def test_multi_level_shell(self, fake_multi_level: None, patch_shell_process: None, backend: EnvBackend):
        # Test interractive shell (API) with multi-level buildenv
        rc = backend.shell()
        assert rc == 0
        self.check_logs("Spawning a new buildenv!")

    def test_shell(self, patch_shell_process: None, backend: EnvBackend):
        # Test interractive shell (API)
        rc = backend.shell()
        assert rc == 0

    def test_cli_shell(self, patch_shell_process: None):
        # Test interractive shell (CLI)
        rc = buildenv(["shell"])
        assert rc == 0

    def test_cli_default(self, patch_shell_process: None):
        # Test interractive shell (CLI default behavior)
        rc = buildenv([])
        assert rc == 0

    def test_command(self, patch_run_process: None, backend: EnvBackend):
        # Test command execution through shell (API)
        rc = backend.run("echo Hello")
        assert rc == 0

    def test_cli_command(self, patch_run_process: None):
        # Test command execution through shell (CLI)
        rc = buildenv(["run", "echo", "Hello"])
        assert rc == 0


class WithCmd(TestHelper):
    @pytest.fixture
    def shell_name(self, monkeypatch: pytest.MonkeyPatch) -> str:
        # Force windows support
        monkeypatch.setattr(cmd_module, "is_windows", lambda: True)

        return "cmd"

    @pytest.fixture
    def patch_shell_process(self, tmp_dir: Path, backend: EnvBackend, monkeypatch: pytest.MonkeyPatch):
        # Check shell name
        assert backend.shell_instance.name == "cmd"

        # Patch subprocess to analyse arguments
        cp: subprocess.CompletedProcess[str] | None = None

        def _remember_cp(args: list[str], **kwargs: dict[str, str]) -> subprocess.CompletedProcess[str]:
            nonlocal cp
            cp = subprocess.CompletedProcess(args, 0, stdout="", stderr="")
            return cp

        monkeypatch.setattr(subprocess, "run", lambda args, **kwargs: _remember_cp(args, **kwargs))  # type: ignore

        # Yield to test
        yield

        # Verify subprocess.run call
        assert cp is not None, "Subprocess was not called"
        assert cp.args == ["cmd", "/k", str(tmp_dir / "shell.cmd")]

        # Verify generated files
        expected_files = ["activate.cmd", "shell.cmd", "activate/readme.cmd"] + (["bin/pip.cmd"] if not backend.has_pip() else [])
        assert len(list(filter(lambda f: f.is_file(), tmp_dir.rglob("*")))) == len(expected_files)
        for f in expected_files:
            assert (tmp_dir / f).is_file()

    def test_shell(self, patch_shell_process: None, backend: EnvBackend):
        # Test interractive shell (API)
        rc = backend.shell()
        assert rc == 0

    def test_cli_shell(self, shell_name: str, patch_shell_process: None):
        # Test interractive shell (CLI)
        rc = buildenv(["shell", "--shell", shell_name])
        assert rc == 0

    @pytest.fixture
    def patch_run_process(self, tmp_dir: Path, backend: EnvBackend, monkeypatch: pytest.MonkeyPatch):
        # Patch subprocess to analyse arguments
        cp: subprocess.CompletedProcess[str] | None = None

        def _remember_cp(args: list[str], **kwargs: dict[str, str]) -> subprocess.CompletedProcess[str]:
            nonlocal cp
            cp = subprocess.CompletedProcess(args, 0, stdout="", stderr="")
            return cp

        monkeypatch.setattr(subprocess, "run", lambda args, **kwargs: _remember_cp(args, **kwargs))  # type: ignore

        # Yield to test
        yield

        # Verify subprocess.run call
        assert cp is not None, "Subprocess was not called"
        assert cp.args == ["cmd", "/c", str(tmp_dir / "command.cmd")]

        # Verify generated files
        expected_files = ["activate.cmd", "command.cmd", "activate/readme.cmd"] + (["bin/pip.cmd"] if not backend.has_pip() else [])
        assert len(list(filter(lambda f: f.is_file(), tmp_dir.rglob("*")))) == len(expected_files)
        for f in expected_files:  # type: ignore
            assert (tmp_dir / f).is_file()

        # Check command is in generated file
        with (tmp_dir / "command.cmd").open() as f:
            assert "echo Hello" in f.read().splitlines()

    def test_command(self, patch_run_process: None, backend: EnvBackend):
        # Test command execution through shell (API)
        rc = backend.run("echo Hello")
        assert rc == 0

    def test_cli_command(self, shell_name: str, patch_run_process: None):
        # Test command execution through shell (CLI)
        rc = buildenv(["run", "--shell", shell_name, "echo", "Hello"])
        assert rc == 0


class WithFunctionalShell(TestHelper):
    @pytest.fixture(autouse=True)
    def no_venv_with_bash(self):
        # Remove any existing virtual environment related env var
        removed_entries: dict[str, str] = {}
        for var in filter(lambda x: x.startswith("VIRTUAL_ENV"), os.environ):
            removed_entries[var] = os.environ[var]
            del os.environ[var]

        # Yield to allow the test to run
        yield

        # Restore the environment
        for var, value in removed_entries.items():
            os.environ[var] = value

    # "Real life" test with installing stuff in temp directory, and run "buildenv --version" command through the installed script
    def run_real_life_version(
        self,
        backend_name: str,
        shell: list[str],
        script: str,
        extra_env: dict[str, str] | None = None,
        patches: dict[str, dict[str, str]] | None = None,
        expect_venv: str = "",
        expect_requirements: bool = True,
        extra_files: list[Path] | None = None,
    ):
        with TemporaryDirectory() as tmp_dir:
            # Run in temporary directory
            project_path = Path(tmp_dir)

            try:
                # Prepare environment (Force using current python executable path (for pipx/uv/uvx detection))
                updated_env = dict(os.environ)
                current_test_venv_bin = Path(sys.executable).parent
                backend_executable = current_test_venv_bin / f"{backend_name}{'.exe' if is_windows() else ''}"
                logging.debug(f"Current test venv bin: {current_test_venv_bin}, looking for backend executable at: {backend_executable}")
                assert backend_executable.is_file(), f"Backend executable not found: {backend_executable}"
                if extra_env:
                    updated_env.update(extra_env)

                # Just make sure the backend executable is found in PATH before going further (to get better error message if not found)
                run_subprocess([backend_executable.name, "--version"], check=True, logger=logging.getLogger())

                # Step 1: install buildenv loading scripts, and check if they are installed
                EnvBackendFactory.create(backend_name, project_path).install()
                for expected_script in [script] + (["requirements.txt"] if expect_requirements else []):
                    assert (project_path / expected_script).is_file(), f"{expected_script} file not found"

                # Step 2: provision test folder with extra files, if any
                if extra_files:
                    for extra_file in extra_files:
                        shutil.copy(extra_file, project_path / extra_file.name)

                # Step 3: apply patches, if any
                if patches:
                    for file_name, patch_data in patches.items():
                        file_path = project_path / file_name
                        with file_path.open("r") as f:
                            content = f.read()
                        for pattern, replacement in patch_data.items():
                            content = content.replace(pattern, replacement)
                        with file_path.open("w") as f:
                            f.write(content)

                # Step 4: run a command through buildenv
                test_command = shell + [
                    str(project_path / script),
                    "run",
                    "--shell",
                    "cmd" if shell[0] == "cmd.exe" else "bash",
                    f"buildenv{'.exe' if is_windows() else ''} --version",
                ]
                cp: subprocess.CompletedProcess[str] = run_subprocess(
                    test_command, cwd=project_path, env=updated_env, check=False, logger=logging.getLogger()
                )  # Just check it runs without error
                assert cp.returncode == 0, f"Command failed with return code {cp.returncode}"
                assert cp.stdout.splitlines()[-1].strip().startswith("buildenv version "), "Unexpected command output"

                # Step 5: check if venv was created
                if expect_venv:
                    assert (project_path / expect_venv).is_dir()
                else:
                    assert not (project_path / "venv").is_dir()
                    assert not (project_path / ".venv").is_dir()

                # Step 6: check if return code is propagated to calling process
                shutil.copy(TEMPLATES / "sample.py", project_path / "sample.py")
                test_command = shell + [
                    str(project_path / script),
                    "run",
                    "--shell",
                    "cmd" if shell[0] == "cmd.exe" else "bash",
                    "python sample.py",
                ]
                cp: subprocess.CompletedProcess[str] = run_subprocess(
                    test_command, cwd=project_path, check=False, logger=logging.getLogger()
                )  # Just check it runs with expected return code
                assert cp.returncode == 135, f"Command failed with return code {cp.returncode}"

            finally:
                # In all cases, copy tree from temp dir to project dir
                shutil.copytree(project_path, self.test_folder, dirs_exist_ok=True, ignore=lambda src, names: [".git"])


class WithFunctionalBash(WithFunctionalShell):
    @pytest.fixture
    def bash(self) -> Generator[str, Any, None]:
        # Use shall factory to detect bash path
        shell = ShellFactory.create("bash", self.test_folder, False, "fake", {}, [])
        assert isinstance(shell, BashShell), f"Expected bash shell, got {type(shell)}"
        yield shell._shell_path  # type: ignore


class WithFunctionalCmd(WithFunctionalShell):
    @pytest.fixture
    def cmd(self) -> Generator[str, Any, None]:
        # Check if we are on Windows
        if not is_windows():
            pytest.skip("This test is only for Windows")

        # Just return the cmd path
        yield "cmd.exe"
