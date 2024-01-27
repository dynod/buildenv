import subprocess
import sys
from pathlib import Path

from nmk.model.builder import NmkTaskBuilder


class RefreshBuilder(NmkTaskBuilder):
    def build(self):
        """
        Simple builder implementation to force build scripts update after new version install
        """
        subprocess.run([str(Path(sys.executable).parent / "buildenv"), "init", "--skip"], check=True)
