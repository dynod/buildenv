# Loading and activation scripts

The **`buildenv`** tool handle a set of scripts used to load and activate the build environment.

## Loading scripts

Loading scripts are stored in the project root folder. They are typically kept in source control, so that any user can setup the build environment just after having cloned the project, by simply running them.

Following scripts are generated (by **`buildenv install`** [command](cli.md)):

- **`buildenv.cmd`** : wrapper to loading script, for Windows
- **`buildenv.sh`** : wrapper to loading script, for Linux (or git bash on Windows)

When launched, the loading script delegates the venv creation to the selected [backend](backends) and wraps to the [buildenv command](cli).

## Activation scripts

Some [extensions](extensions) may create some extra activation scripts, which will be generated and activated each time the environment is initialized.
