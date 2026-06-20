# Features

The purpose of the **`buildenv`** tool is to help projects to setup easily a build environment (based on [Python virtual environment](https://docs.python.org/3/library/venv.html), or "**venv**"), just after clone, with minimal dependencies (i.e. only [**git**](https://git-scm.com/), and the chosen [environment backend](backends)).

## Environment backends

The **`buildenv`** tool is based on [environment backends](backends), which are handling the underlying virtual environments.

## Simple setup with loading scripts

The main feature of the **`buildenv`** tool is to generate [loading scripts](scripts) in the project root folder, ready to be executed just after the project is cloned, and loading everything so that the project is ready to build (whatever is the used build system).

See [usage instructions](./usage.md) for details.

## Launch build terminal from explorer

By default, the [loading scripts](scripts) are spawning a new shell process. It means that when launched from the OS explorer (Windows/Linux), a build terminal will be launched, initialized with the build environment context, and stay openned to let you entering shell commands.

On Windows, it works with both:

- **buildenv.cmd**: that will open the terminal in a **cmd** window (or better, in [Windows Terminal](https://github.com/microsoft/terminal) if installed)
- **buildenv.sh**: that will open the terminal in a **git bash** window (see [gitforwindows.org](https://gitforwindows.org/))

## Command line interface

The **`buildenv`** tool provides a [command line interface](cli) allowing to create, maintain, and globally control your environment.

## Completion

When running on Linux (or in Git bash on Windows), completion is automatically enabled when running in **`buildenv`** shell for following commands (depending on the used [backend](backends)):

- **`buildenv`**
- **`pip`** (only for **pip** backend)
- **`uv`**/**`uvx`** (only for **uv**/**uvx** backends)

Completion can be enabled for other commands from **`buildenv`** extensions.

## Templates

The **`buildenv`** tool provides a [project templates](templates) mechanism easing new project setup "from scratch".

## Extensions

It is possible to extend the **`buildenv`** tool behavior thanks to [extensions](extensions)
