from typing import Union

from .backend import EnvBackendWithRequirements


# pipx-style backend
class PipXBackend(EnvBackendWithRequirements):
    NAME = "pipx"

    @property
    def name(self):
        return PipXBackend.NAME

    @property
    def install_url(self):
        return "https://pipx.pypa.io/stable/"

    def has_pip(self):
        # Pipx installed venv doesn't have pip
        return False

    def _backend_upgrade_env(self) -> Union[tuple[str, str], None]:
        # Force "no cache" pipx option on upgrade
        return ("BUILDENV_PIPX_ARGS", "--no-cache")
