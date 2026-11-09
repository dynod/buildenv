import pytest

from .commons2 import EnvBackendFactory, Path, WithVenv


class TestMisc(WithVenv):
    def test_backend(self, fake_venv: Path):
        # Basic detection
        backend = EnvBackendFactory.detect(fake_venv, verbose_subprocess=False)
        assert backend.name == "fallback"
        assert backend.install_url == ""
        assert not backend.has_pip()

        # Give a try with package addition
        with pytest.raises(AssertionError, match="fallback backend is not mutable, can't add packages"):
            backend.add_packages(["pytest"])

        # Give a try with updates
        with pytest.raises(NotImplementedError, match="Don't know how to upgrade packages for this backend"):
            backend.upgrade(full=True, only_deps=False)
