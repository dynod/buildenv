import logging
import sys
from pathlib import Path

from ._backends.factory import EnvBackendFactory
from ._parser import BuildEnvParser

# Current directory
_CWD = Path.cwd()


def buildenv(args: list[str], project_path: Path = _CWD) -> int:
    # This is the "buildenv" command logic

    try:
        # Prepare backend
        b = EnvBackendFactory.create(project_path)

        # Prepare parser
        p = BuildEnvParser(b)

        # Delegate execution to parser
        p.execute(args)
        return 0
    except Exception as e:
        # An error occurred
        logging.error(str(e))
        return 1


def main() -> int:  # pragma: no cover
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    buildenv(sys.argv[1:])


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
