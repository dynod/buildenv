import logging
import sys
from pathlib import Path
from typing import List

from buildenv._internal.parser import BuildEnvParser, RCHolder
from buildenv.loader import logger
from buildenv.manager import BuildEnvManager

# Current directory
_CWD = Path.cwd()


def buildenv(args: List[str], project_path: Path = _CWD, venv_bin_path: Path = None) -> int:
    # This is the "buildenv" command logic

    # Invoke build env manager on current project directory
    b = BuildEnvManager(project_path, venv_bin_path)

    # Prepare parser
    p = BuildEnvParser(
        b.init,  # Init callback
        b.shell,  # Shell callback
        b.run,  # Run callback
        b.upgrade,  # Upgrade callback
    )

    # Execute parser
    try:
        # Delegate execution to parser
        p.execute(args)
        return 0
    except RCHolder as e:
        # Specific return code to be used
        return e.rc
    except Exception as e:
        # An error occurred
        logger.error(str(e))
        return 1


def main() -> int:  # pragma: no cover
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    return buildenv(sys.argv[1:])


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
