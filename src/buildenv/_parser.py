from argparse import REMAINDER, SUPPRESS, ArgumentParser
from pathlib import Path

import argcomplete

from . import __version__
from .backends.factory import EnvBackendFactory


class BuildEnvParser:
    """
    Command-line interface parser for buildenv manager

    :param backend: build environment backend instance
    """

    def __init__(self):
        # Setup arguments parser
        self._parser = ArgumentParser(prog="buildenv", description="Build environment manager")

        # Version handling
        self._parser.add_argument("-V", "--version", action="version", version=f"buildenv version {__version__}")
        self._parser.add_argument(
            "--from-loader", help=SUPPRESS, default=None, action="store"
        )  # Deprecated, kept for backward compatibility with legacy scripts
        self._parser.set_defaults(func=None, shell_func="shell", kwargs={}, project_folder=Path.cwd())

        # Common arguments to all commands
        def _common_args(sub_parser: ArgumentParser):
            sub_parser.add_argument(
                "--project", "-p", metavar="PROJECT", dest="project_folder", type=Path, default=Path.cwd(), help="project folder (default: .)"
            )

        # Common arguments to commands able to dump package upgrades
        def _upgrade_args(sub_parser: ArgumentParser):
            # Hidden argument to show updates from a given file
            sub_parser.add_argument("--show-updates-from", metavar="FILE", default=None, type=Path, help=SUPPRESS)

        # Add subcommands:
        sub_parsers = self._parser.add_subparsers(help="sub-commands:")

        # install sub-command
        install_help = "install build environment loading scripts"
        install_parser = sub_parsers.add_parser("install", help=install_help, description=install_help)
        _common_args(install_parser)
        choices = EnvBackendFactory.KNOWN_BACKENDS
        install_parser.add_argument("--backend", choices=choices, help="force using specified backend")
        install_parser.add_argument(
            "--with",
            action="append",
            dest="packages",
            metavar="PACKAGE",
            default=[],
            help="additional package to install in this environment (can be specified multiple times)",
        )
        install_parser.set_defaults(func="install", kwargs_map={"packages": lambda o: o.packages})  # type: ignore

        # init sub-command
        init_help = "create venv and initialize extensions (implicitly done with shell and run commands)"
        init_parser = sub_parsers.add_parser("init", help=init_help, description=init_help)
        _common_args(init_parser)
        init_parser.set_defaults(
            func="init",
            kwargs_map={
                "force": lambda o: o.force,  # type: ignore
                "skip_ext": lambda o: o.skipped_extensions,  # type: ignore
                "no_ext": lambda o: o.no_ext,  # type: ignore
                "show_updates_from": lambda o: o.show_updates_from,  # type: ignore
            },
        )
        init_parser.add_argument("--force", "-f", action="store_true", default=False, help="force extensions re-initialization")
        init_parser.add_argument("--no-ext", action="store_true", default=False, help="ignore all extensions on initialization")
        init_parser.add_argument(
            "--skip-ext",
            action="append",
            dest="skipped_extensions",
            default=[],
            help="skip specified extension(s) on initialization (can be specified multiple times)",
        )
        _upgrade_args(init_parser)

        # shell sub-command
        shell_help = "start an interactive shell with loaded build environment"
        shell_parser = sub_parsers.add_parser("shell", help=shell_help, description=shell_help)
        _common_args(shell_parser)
        shell_parser.set_defaults(func="shell", kwargs_map={"show_updates_from": lambda o: o.show_updates_from, "command": lambda o: o.command})  # type: ignore
        shell_parser.add_argument("--command", "-c", metavar="COMMAND", help="command and arguments to be executed in build environment")
        _upgrade_args(shell_parser)

        # run sub-command
        run_help = "run command in build environment"
        run_parser = sub_parsers.add_parser("run", help=run_help, description=run_help)
        _common_args(run_parser)
        run_parser.set_defaults(func="run", kwargs_map={"command": lambda o: " ".join(o.CMD)})  # type: ignore
        run_parser.add_argument("CMD", nargs=REMAINDER, help="command and arguments to be executed in build environment")

        # list sub-command
        list_help = "list installed packages in the current build environment"
        list_parser = sub_parsers.add_parser("list", help=list_help, description=list_help)
        _common_args(list_parser)
        list_parser.set_defaults(func="list")

        # lock sub-command
        lock_help = "lock build environment packages versions"
        lock_parser = sub_parsers.add_parser("lock", help=lock_help, description=lock_help)
        _common_args(lock_parser)
        lock_parser.set_defaults(func="lock")

        # upgrade sub-command
        upgrade_help = "upgrade build environment packages to their latest version"
        upgrade_parser = sub_parsers.add_parser("upgrade", help=upgrade_help, description=upgrade_help)
        _common_args(upgrade_parser)
        upgrade_parser.set_defaults(func="upgrade")

        # Handle completion
        argcomplete.autocomplete(self._parser)

    def execute(self, args: list[str]) -> int:
        """
        Parse incoming arguments list, and execute command callback

        :param args: Incoming arguments list
        :return: command return code
        """

        # Parse arguments
        options = self._parser.parse_args(args)

        # Prepare project folder + backend
        project_folder: Path = options.project_folder
        project_folder.mkdir(parents=True, exist_ok=True)
        backend = (
            EnvBackendFactory.create(options.backend, project_folder)
            if (hasattr(options, "backend") and options.backend is not None)
            else EnvBackendFactory.detect(project_folder)
        )

        # Prepare keyword args
        kwargs = dict(options.kwargs)
        if hasattr(options, "kwargs_map"):
            kwargs.update({name: mapper(options) for name, mapper in options.kwargs_map.items()})

        # Check for sub-command
        if options.func is None:
            # No sub-command: default command is shell
            return getattr(backend, options.shell_func)(**kwargs)
        else:
            # Delegate to sub-command function
            return getattr(backend, options.func)(**kwargs)
