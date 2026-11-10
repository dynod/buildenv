from .backend import EnvBackend


class FallbackBackend(EnvBackend):
    """A backend that does nothing, used as a fallback when no other backend is available."""

    NAME = "fallback"

    @property
    def name(self):
        return FallbackBackend.NAME

    @property
    def install_url(self) -> str:
        return ""

    def has_pip(self):
        return False

    def _delegate_upgrade(self, full: bool = True, only_deps: bool = False) -> int:
        # Empty implementation, as this backend does not support upgrades
        raise NotImplementedError("Don't know how to upgrade packages for this backend")
