import logging
import sys

from ._parser import BuildEnvParser


def buildenv(args: list[str]) -> int:
    # This is the "buildenv" command logic

    try:
        # Delegate execution to parser
        return BuildEnvParser().execute(args)
    except Exception as e:
        # An error occurred
        # logging.exception("An error occurred while executing buildenv")
        logging.error(str(e))
        return 1


def main() -> int:  # pragma: no cover
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    return buildenv(sys.argv[1:])


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
