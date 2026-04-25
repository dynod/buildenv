import logging
import sys

from ._parser import BuildEnvParser
from ._utils import LOGGER_NAME, StopHereException

_LOGGER = logging.getLogger(LOGGER_NAME)


def buildenv(args: list[str]) -> int:
    # This is the "buildenv" command logic

    try:
        # Delegate execution to parser
        return BuildEnvParser().execute(args)
    except StopHereException:
        # This is not an error, just a way to stop execution of a command callback (e.g. after listing templates)
        return 0
    except Exception as e:
        # An error occurred
        _LOGGER.error(f"An error occurred while executing buildenv: {e}")
        _LOGGER.debug("Error details:", exc_info=e)
        return 1


def main() -> int:  # pragma: no cover
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    return buildenv(sys.argv[1:])


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
