from .backend import EnvBackend


# pipx-style backend
class PipXBackend(EnvBackend):
    @property
    def name(self):
        return "pipx"

    def is_mutable(self):
        # pipx installed tools venv is not mutable
        return False

    def has_pip(self):
        # Pipx has pip (even if it shouldn't be used)
        return True
