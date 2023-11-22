from argparse import REMAINDER, SUPPRESS, ArgumentParser
from typing import Callable, List

import argcomplete

from buildenv import __version__


class RCHolder(Exception):  # NOQA: N818
    """
    Exception holding a return code

    :param rc: Return code to be used
    """

    def __init__(self, rc: int, *args: object):
        # Super call
        super().__init__(*args)

        # Remember provided return code
        self.rc = rc


class BuildEnvParser:
    """
    Command-line interface parser for buildenv manager

    :param init_cb: Callback for **buildenv init** command
    :param shell_cb: Callback for **buildenv shell** command
    :param run_cb: Callback for **buildenv run** command
    """

    def __init__(self, init_cb: Callable, shell_cb: Callable, run_cb: Callable):
        # Setup arguments parser
        self._parser = ArgumentParser(prog="buildenv", description="Build environment manager")

        # Version handling
        self._parser.add_argument("-V", "--version", action="version", version=f"buildenv version {__version__}")
        self._parser.add_argument("--from-loader", help=SUPPRESS, default=None, action="store")
        self._parser.set_defaults(func=None, init_func=init_cb, shell_func=shell_cb)

        # Add subcommands:
        sub_parsers = self._parser.add_subparsers(help="sub-commands:")

        # init sub-command
        init_help = "initialize the build environment and exit"
        init_parser = sub_parsers.add_parser("init", help=init_help, description=init_help)
        init_parser.set_defaults(func=init_cb)

        # shell sub-command
        shell_help = "start an interactive shell with loaded build environment"
        shell_parser = sub_parsers.add_parser("shell", help=shell_help, description=shell_help)
        shell_parser.set_defaults(func=shell_cb)

        # run sub-command
        run_help = "run command in build environment"
        run_parser = sub_parsers.add_parser("run", help=run_help, description=run_help)
        run_parser.set_defaults(func=run_cb)
        run_parser.add_argument("CMD", nargs=REMAINDER, help="Command and arguments to be executed in build environment")

        # Handle completion
        argcomplete.autocomplete(self._parser)

    def execute(self, args: List[str]):
        """
        Parse incoming arguments list, and execute command callback

        :param args: Incoming arguments list
        """

        # Parse arguments
        options = self._parser.parse_args(args)

        # Check for sub-command
        if options.func is None:
            # No sub-command
            if options.from_loader is not None:
                # From loading script: default command is shell
                options.shell_func(options)
            else:
                # Otherwise: default command is init
                options.init_func(options)
        else:
            # Delegate to sub-command function
            options.func(options)
