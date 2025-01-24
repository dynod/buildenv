from .backend import EnvBackend


# Legacy pip-style backend
class LegacyPipBackend(EnvBackend):
    @property
    def name(self):
        return "pip"

    def is_mutable(self):
        # Pip installed venv is mutable
        return True