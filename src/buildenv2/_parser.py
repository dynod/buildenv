from argparse import REMAINDER, ArgumentParser

import argcomplete

from . import __version__
from ._backends.backend import EnvBackend


class BuildEnvParser:
    """
    Command-line interface parser for buildenv manager

    :param backend: build environment backend instance
    """

    def __init__(self, backend: EnvBackend):
        # Setup arguments parser
        self._parser = ArgumentParser(prog="buildenv", description="Build environment manager")

        # Version handling
        self._parser.add_argument("-V", "--version", action="version", version=f"buildenv version {__version__}")
        self._parser.set_defaults(func=None, shell_func=backend.shell, kwargs={})

        # Add subcommands:
        sub_parsers = self._parser.add_subparsers(help="sub-commands:")

        # shell sub-command
        shell_help = "start an interactive shell with loaded build environment"
        shell_parser = sub_parsers.add_parser("shell", help=shell_help, description=shell_help)
        shell_parser.set_defaults(func=backend.shell)

        # run sub-command
        run_help = "run command in build environment"
        run_parser = sub_parsers.add_parser("run", help=run_help, description=run_help)
        run_parser.set_defaults(func=backend.run, kwargs_map={"command": lambda o: " ".join(o.CMD)})
        run_parser.add_argument("CMD", nargs=REMAINDER, help="command and arguments to be executed in build environment")

        # Handle completion
        argcomplete.autocomplete(self._parser)

    def execute(self, args: list[str]):
        """
        Parse incoming arguments list, and execute command callback

        :param args: Incoming arguments list
        """

        # Parse arguments
        options = self._parser.parse_args(args)

        # Prepare keyword args
        kwargs = dict(options.kwargs)
        if hasattr(options, "kwargs_map"):
            kwargs.update({name: mapper(options) for name, mapper in options.kwargs_map.items()})

        # Check for sub-command
        if options.func is None:
            # No sub-command: default command is shell
            options.shell_func(**kwargs)
        else:
            # Delegate to sub-command function
            options.func(**kwargs)
