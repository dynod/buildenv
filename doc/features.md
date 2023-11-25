# Features

The purpose of the **`buildenv`** tool is to help projects to setup easily a build environment (based on [Python virtual environment](https://docs.python.org/3/library/venv.html), or "**venv**"), just after clone, with minimal dependencies (i.e. only [**git**](https://git-scm.com/) and [**python**](https://www.python.org/)).

## Simple setup with "buildenv" loading scripts

### Existing project

The main feature of the **`buildenv`** tool is to generate loading scripts in the project root folder, ready to be executed just after the project is cloned, and loading everything so that the project is ready to build (whatever is the used build system).

In other words, the typical project setup scenario with **`buildenv`** is:
1. clone the project -- `git clone git@github.com:xxx/yyy.git`
1. launch the loading script:
    * on Linux: `./buildenv.sh`
    * on Windows: `buildenv.cmd`
1. build the project

### New project

Any project can be simply setup to use **`buildenv`** by running a simple standalone python script in the project root folder:
1. download **buildenv** script (python version) -- `wget https://raw.githubusercontent.com/dynod/buildenv/main/buildenv-loader.py`
1. launch it:
    * on Linux: `python3 buildenv-loader.py`
    * on Windows: `python buildenv-loader.py`
1. you're done, the project now also embeds **buildenv** loading scripts for a more convenient day to day use

## Launch build terminal from explorer

By default, the loading scripts are spawning a new shell process. It means that when launched from the OS explorer (Windows/Linux), a build terminal will be launched, initialized with the build environment context, and stay openned to let you entering shell commands.

On Windows, it works with both:
* **buildenv.cmd**: that will open the terminal in a **cmd** window (or better, in [Windows Terminal](https://github.com/microsoft/terminal) if installed)
* **buildenv.sh**: that will open the terminal in a **git bash** window (see [gitforwindows.org](https://gitforwindows.org/))

## Shared venv

You may work on multiple projects, and want to avoid to setup multiple build environments for each project.

The loading script automatically looks up in parent git folders to find an existing **venv**.
If it finds one, it loads it instead of creating a new one in the current project folder.

Example layout:
```
projectA/
  + .git/
  + venv/
  + buildenv.*
  + projectB/
  |--+ .git/
  |--+ buildenv.*
  + subfolder/
  |--+ projectC/
     |--+ .git/
     |--+ buildenv.*
```
When loading scripts are used in **projectB** or **projectC**, the **venv** of **projectA** will be used.

## Suggested git files

When the build env manager prepares the build environment, it will verify if some recommended git files exist in current project:

* **.gitignore** should be configured so that **venv** and **.buildenv** folders are ignored and not pushed to source control
* **.gitattributes** should be configured to handle platform-specific files with correct line endings:
  * **.bat** and **.cmd** files must always use **`crlf`** line endings
  * **.sh** files must always use **`lf`** line endings

## Completion

When running on Linux (or in Git bash on Windows), completion is automatically enabled when running in **`buildenv`** shell for following commands:
* **`buildenv`**
* **`pip`**

Completion can be enabled for other commands from **`buildenv`** extensions.
