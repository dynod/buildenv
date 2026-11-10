# Loading and activation scripts

The **`buildenv`** tool handle a set of scripts used to load and activate the build environment.

## Loading scripts

Loading scripts are stored in the project root folder. They are typically kept in source control, so that any user can setup the build environment just after having cloned the project, by simply running them.

Following scripts are generated (by **`buildenv install`** [command](cli.md)):

- **`buildenv.cmd`** : loading script for Windows **cmd**/**PowerShell** shells
- **`buildenv.sh`** : loading script for Linux (or **git bash** on Windows)

When launched, the loading script delegates the venv creation to the selected [backend](backends) and wraps to the [buildenv command](cli).

Installed loading scripts version is exposed in {ref}`BUILDENV_VERSION<BUILDENV_VERSION>` environment variable in any spawned shell/subprocess.

In {py:class}`~buildenv.backends.backend.EnvBackend` API:

- {py:attr}`~buildenv.backends.backend.EnvBackend.version` property exposes the current buildenv loading scripts version.
- {py:attr}`~buildenv.backends.backend.EnvBackend.scripts_version` property exposes the project’s installed loading scripts version.

Comparing these two properties helps to know if installed loading scripts are outdated WRT. used buildenv version.

## Activation scripts

Some [extensions](extensions) may create some extra activation scripts, which will be generated and activated each time the environment is initialized.
