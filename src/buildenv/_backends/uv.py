from .backend import EnvBackend


# UV-style backend
class UvProjectBackend(EnvBackend):
    @property
    def name(self):
        return "uv"

    def is_mutable(self):
        # Uv workspace env is mutable
        return True

    def has_pip(self):
        # Uv based env does not have pip
        return False


# UVX-style backend (immutable)
class UvxBackend(UvProjectBackend):
    @property
    def name(self):
        return "uvx"

    def is_mutable(self):
        # Uvx installed tools venv is not mutable
        return False
