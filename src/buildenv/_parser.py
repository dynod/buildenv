import logging
from argparse import REMAINDER, SUPPRESS, ArgumentParser, Namespace
from pathlib import Path

import argcomplete

from . import __version__
from ._entry_points import parse_project_templates
from ._shells.factory import KNOWN_SHELLS
from ._utils import LOGGER_NAME, StopHereException
from .backends.factory import EnvBackendFactory
from .extension import BuildEnvInfo, BuildEnvProjectTemplate

_LOGGER = logging.getLogger(LOGGER_NAME)

_DEFAULT_SHELL = "bash"


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
            sub_parser.add_argument("--shell", choices=KNOWN_SHELLS, default=_DEFAULT_SHELL, help=f"force using specified shell (default: {_DEFAULT_SHELL})")

        # Common arguments to commands able to dump package upgrades
        def _upgrade_args(sub_parser: ArgumentParser):
            # Hidden argument to show updates from a given file
            sub_parser.add_argument("--show-updates-from", metavar="FILE", default=None, type=Path, help=SUPPRESS)

        # Add subcommands:
        sub_parsers = self._parser.add_subparsers(help="sub-commands:")

        # install sub-command
        install_help = "install build environment loading scripts and setup project from template"
        install_parser = sub_parsers.add_parser("install", help=install_help, description=install_help)
        _common_args(install_parser)
        choices = EnvBackendFactory.KNOWN_BACKENDS
        install_parser.add_argument("--backend", choices=choices, help="force using specified backend")
        install_parser.add_argument(
            "--add",
            action="append",
            dest="packages",
            metavar="PACKAGE",
            default=[],
            help="additional package to install in this environment (can be specified multiple times)",
        )
        whole_templates_group = install_parser.add_argument_group(title="project template options")
        templates_group = whole_templates_group.add_mutually_exclusive_group()
        templates_group.add_argument(
            "--template",
            "-t",
            metavar="TEMPLATE",
            dest="main_template",
            default=None,
            help="main template used to create a new project (overrides default template)",
        )
        templates_group.add_argument("--no-template", action="store_true", default=False, help="forces project install without any template")
        templates_group.add_argument("--list-templates", action="store_true", default=False, help="prints all available project templates and exit")
        whole_templates_group.add_argument(
            "--extra-template",
            "-X",
            action="append",
            metavar="TEMPLATE",
            dest="extra_templates",
            default=[],
            help="adds extra project template support (can be specified multiple times)",
        )
        whole_templates_group.add_argument(
            "--ignore-template",
            "-I",
            action="append",
            metavar="TEMPLATE",
            dest="ignored_templates",
            default=[],
            help="removes extra project template support (can be specified multiple times)",
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
        init_parser.add_argument("--new", dest="old_new_option", action="store_true", default=False, help=SUPPRESS)
        _upgrade_args(init_parser)

        # shell sub-command
        shell_help = "start an interactive shell with loaded build environment (default if no sub-command is specified)"
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

        # unlock sub-command
        unlock_help = "unlock build environment packages versions"
        unlock_parser = sub_parsers.add_parser("unlock", help=unlock_help, description=unlock_help)
        _common_args(unlock_parser)
        unlock_parser.set_defaults(func="unlock")

        # upgrade sub-command
        upgrade_help = "upgrade build environment packages to their latest version"
        upgrade_parser = sub_parsers.add_parser("upgrade", help=upgrade_help, description=upgrade_help)
        _common_args(upgrade_parser)
        upgrade_parser.set_defaults(func="upgrade")

        # Handle completion
        argcomplete.autocomplete(self._parser)

    def handle_install(self, options: Namespace) -> tuple[BuildEnvProjectTemplate | None, list[BuildEnvProjectTemplate]]:
        """
        Handle install command, and return project template if specified

        :param options: parsed arguments namespace
        :return: a tuple containing:
            - project template if specified, None otherwise
            - list of additional project templates, if any
        """

        # Parse project templates
        all_templates = parse_project_templates(BuildEnvInfo(project_root=options.project_folder))
        max_name_length = 0
        max_weight = 0
        main_templates_names: list[str] = []
        extra_templates_names: list[str] = []
        for t in all_templates.values():
            # Check of max name length (for pretty-printing)
            max_name_length = max((len(t.name), max_name_length))

            if t.auto_extra:
                # Just add as a default extra
                extra_templates_names.append(t.name)

            # Handle template wight
            if t.weight == 0:
                # Nothing else to do with non-weighted template
                continue
            if t.weight > max_weight:
                # New default main template
                main_templates_names.clear()
                main_templates_names.append(t.name)
                max_weight = t.weight
            elif t.weight == max_weight:  # pragma: no branch
                # Multiple default main template (user will have to choose)
                main_templates_names.append(t.name)

        # Build templates list
        templates_list = "\n".join(
            map(
                lambda t: (
                    f" - {t}{' ' * (max_name_length - len(t))} "
                    + f"{'**' if t in main_templates_names else ('* ' if all_templates[t].auto_extra else '  ')} "
                    + all_templates[t].description
                ),
                sorted(all_templates.keys()),
            )
        )

        # List command
        if options.list_templates:
            _LOGGER.info(f"Available project templates (**: default main, *: default extra):\n{templates_list}")
            raise StopHereException()

        def validate_template(t_name: str):
            assert main_template in all_templates, f"Unknown project template '{main_template}'\nAvailable templates:\n{templates_list}"

        # Main template
        if options.no_template:
            # No template at all, stop here
            _LOGGER.info("No project template selected")
            return (None, [])
        elif options.main_template:
            # User specified
            main_template = options.main_template
            validate_template(main_template)
        elif len(main_templates_names) == 0:
            # No default main template, stop here
            _LOGGER.info("No default project template")
            return (None, [])
        elif len(main_templates_names) == 1:
            # Use most weighted unique template
            main_template = main_templates_names[0]
        else:
            # More than 1 most weighted main templates
            raise RuntimeError(f"Please choose among the available default main templates: {', '.join(main_templates_names)}")

        # Extra templates
        for to_add in options.extra_templates:
            validate_template(to_add)
            if to_add not in extra_templates_names:
                extra_templates_names.append(to_add)
        for to_remove in options.ignored_templates:
            validate_template(to_remove)
            if to_remove in extra_templates_names:
                extra_templates_names.remove(to_remove)

        # In any case, main template can't be in extra templates
        if main_template in extra_templates_names:
            extra_templates_names.remove(main_template)

        # Ready to go
        _LOGGER.info(f"Main template: {main_template}")
        _LOGGER.info(f"Extra templates: {', '.join(extra_templates_names)}")
        return (all_templates[main_template], [all_templates[t] for t in extra_templates_names])

    def execute(self, args: list[str]) -> int:
        """
        Parse incoming arguments list, and execute command callback

        :param args: Incoming arguments list
        :return: command return code
        """

        # Parse arguments
        options = self._parser.parse_args(args)

        # Backend name
        backend_name: str | None = None
        if hasattr(options, "backend") and options.backend is not None:
            backend_name = options.backend

        # Specific handling for install command:
        template: BuildEnvProjectTemplate | None = None
        extra_templates: list[BuildEnvProjectTemplate] = []
        if options.func == "install":
            template, extra_templates = self.handle_install(options)

            # Check template preferred backend if no backend specified
            if (template is not None) and (backend_name is None) and EnvBackendFactory.is_supported(template.preferred_backend):
                backend_name = template.preferred_backend

        # Legacy stuff handling
        elif options.func == "init" and options.old_new_option:
            raise RuntimeError("Since 2.0, 'buildenv init --new' syntax is deprecated. Please use 'buildenv install' instead.")

        # Prepare project folder + backend
        project_folder: Path = options.project_folder
        project_folder.mkdir(parents=True, exist_ok=True)
        shell_name: str = options.shell if hasattr(options, "shell") else _DEFAULT_SHELL
        backend = (
            EnvBackendFactory.create(backend_name, project_folder, shell_name=shell_name)
            if backend_name is not None
            else EnvBackendFactory.detect(project_folder, shell_name=shell_name)
        )

        # Prepare keyword args
        kwargs = dict(options.kwargs)
        if hasattr(options, "kwargs_map"):
            kwargs.update({name: mapper(options) for name, mapper in options.kwargs_map.items()})
        if template is not None:
            # Refresh selected backend name
            for tmp in [template] + extra_templates:
                tmp.info.backend_name = backend.name
            kwargs.update({"template": template, "extra_templates": extra_templates})

        # Check for sub-command
        if options.func is None:
            # No sub-command: default command is shell
            return getattr(backend, options.shell_func)(**kwargs)
        else:
            # Delegate to sub-command function
            return getattr(backend, options.func)(**kwargs)
