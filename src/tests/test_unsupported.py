import pytest

from .commons2 import EnvBackendFactory, Path, WithVenv


class TestMisc(WithVenv):
    def test_backend(self, fake_venv: Path):
        with pytest.raises(RuntimeError, match="Unsupported venv type"):
            EnvBackendFactory.detect(fake_venv, verbose_subprocess=False)
