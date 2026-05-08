from buildenv._shells.bash import BashShell
from buildenv._shells.cmd import CmdShell
from buildenv.backends._uv import EnvBackend, UvxBackend
from tests.commons2 import WithBash, WithCmd, WithFunctionalBash, WithFunctionalCmd, WithUvx


class TestUvxBash(WithUvx, WithBash):
    def test_uvx_backend(self, backend: EnvBackend):
        # Test backend type
        assert isinstance(backend, UvxBackend)
        assert isinstance(backend.shell_instance, BashShell)


class TestUvxCmd(WithUvx, WithCmd):
    def test_uvx_backend(self, backend: EnvBackend):
        # Test backend type
        assert isinstance(backend, UvxBackend)
        assert isinstance(backend.shell_instance, CmdShell)


# Updated env for uvx tests
UVX_UPDATED_ENV = {"BUILDENV_UVX_ARGS": "--no-cache"}  # Force re-creating venv from scratch


class TestFunctionalUvxBash(WithFunctionalBash):
    def test_real_life(self, bash: str):
        self.run_real_life_version("uvx", [bash], "buildenv.sh", UVX_UPDATED_ENV)


class TestFunctionalUvxCmd(WithFunctionalCmd):
    def test_real_life(self, cmd: str):
        self.run_real_life_version("uvx", [cmd, "/c"], "buildenv.cmd", UVX_UPDATED_ENV)
