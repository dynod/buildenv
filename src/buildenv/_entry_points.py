import importlib.metadata
from typing import TypeVar

from .extension import BuildEnvEntryPoint, BuildEnvExtension, BuildEnvInfo, BuildEnvProjectTemplate

# Buildenv extension entry point name
_BUILDENV_EXT = "buildenv_extension"

# Buildenv project template entry point name
_BUILDENV_TEMPLATE = "buildenv_template"

# Type var for generic entry point loading
_EntryPointClass = TypeVar("_EntryPointClass", bound=BuildEnvEntryPoint)


# Entry points parser
def parse_entrypoints(group_name: str, info: BuildEnvInfo, sample_instance: _EntryPointClass, with_name: bool = False) -> dict[str, _EntryPointClass]:
    # Build entry points map (to handle duplicate names)
    unfiltered_entry_points: importlib.metadata.EntryPoints = importlib.metadata.entry_points(group=group_name)
    all_entry_points: dict[str, importlib.metadata.EntryPoint] = {}
    for p in unfiltered_entry_points:
        all_entry_points[p.name] = p

    out: dict[str, _EntryPointClass] = {}
    for name, point in all_entry_points.items():
        # Instantiate extension
        try:
            # Check type
            extension_class = point.load()
            sample_class = type(sample_instance)
            assert issubclass(extension_class, sample_class), f"{group_name}.{name} entrypoint class is not extending buildenv.{sample_class.__name__}"

            # Create instance with info (and name if required)
            kwargs = {"info": info}
            if with_name:
                kwargs["name"] = name  # type: ignore
            extension = extension_class(**kwargs)
        except Exception as e:
            raise AssertionError(f"Failed to load {name} extension: {e}") from e
        out[name] = extension

    return out


# Iterate on entry points to load extensions
def parse_extensions(info: BuildEnvInfo) -> dict[str, BuildEnvExtension]:
    return parse_entrypoints(_BUILDENV_EXT, info, BuildEnvExtension(info))


# Iterate on entry points to load project templates
def parse_project_templates(info: BuildEnvInfo) -> dict[str, BuildEnvProjectTemplate]:
    return parse_entrypoints(_BUILDENV_TEMPLATE, info, BuildEnvProjectTemplate(info, name=""), with_name=True)
