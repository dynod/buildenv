from argparse import REMAINDER, SUPPRESS, ArgumentParser
from pathlib import Path
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
    :param upgrade_cb: Callback for **buildenv upgrade** command
    """

    def __init__(self, init_cb: Callable, shell_cb: Callable, run_cb: Callable, upgrade_cb: Callable):
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
        g = init_parser.add_mutually_exclusive_group()
        g.add_argument("--force", "-f", action="store_true", default=False, help="force buildenv init to be triggered again")
        g.add_argument("--skip", "-s", action="store_true", default=False, help="skip extensions and activation scripts generation")
        init_parser.add_argument(
            "--new", metavar="FOLDER", action="store", type=Path, default=None, help="create a new buildenv in specified folder"
        ).completer = argcomplete.DirectoriesCompleter()

        # shell sub-command
        shell_help = "start an interactive shell with loaded build environment"
        shell_parser = sub_parsers.add_parser("shell", help=shell_help, description=shell_help)
        shell_parser.set_defaults(func=shell_cb)

        # run sub-command
        run_help = "run command in build environment"
        run_parser = sub_parsers.add_parser("run", help=run_help, description=run_help)
        run_parser.set_defaults(func=run_cb)
        run_parser.add_argument("CMD", nargs=REMAINDER, help="command and arguments to be executed in build environment")

        # upgrade sub-command
        upgrade_help = "upgrade python venv installed packages"
        upgrade_parser = sub_parsers.add_parser("upgrade", help=upgrade_help, description=upgrade_help)
        upgrade_parser.set_defaults(func=upgrade_cb)
        upgrade_parser.add_argument("--eager", action="store_true", default=False, help="toggle eager upgrade strategy")

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
