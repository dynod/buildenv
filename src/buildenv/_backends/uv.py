from .backend import EnvBackend


# UV-style backend
class UvToolsBackend(EnvBackend):
    @property
    def name(self):
        return "uv"

    def is_mutable(self):
        # Uv installed tools venv is not mutable
        return False
