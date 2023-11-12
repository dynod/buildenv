# Features

The purpose of the **`buildenv`** tool is to help projects to setup easily a build environment (based on [Python virtual environment](https://docs.python.org/3/library/venv.html), or "**venv**"), just after clone, with minimal dependencies (i.e. only [**git**](https://git-scm.com/) and [**python**](https://www.python.org/)).

## Simple setup

Any project can be simply setup to use **`buildenv`** by using a simple standalone python script in the project root folder:
1. download **loadme** script (python version) -- `wget https://raw.githubusercontent.com/dynod/buildenv/main/src/buildenv/loadme.py`
1. launch it:
    * on Linux: `python3 loadme.py`
    * on Windows: `python loadme.py`
1. you're done, the project now also embeds **loadme** shell scripts for a more convenient day to day use

## "loadme" scripts

The main feature of the **`buildenv`** tool is to generate "**loadme**" scripts in the project root folder, ready to be executed just after the project is cloned, and loading everything so that the project is ready to build (whatever is the used build system).

In other words, the typical project setup scenario with **`buildenv`** is:
1. clone the project -- `git clone git@github.com:xxx/yyy.git`
1. launch the **loadme** script:
    * on Linux: `source loadme.sh`
    * on Windows: `loadme.cmd`
1. build the project

## Shared venv

You may work on multiple projects, and want to avoid to setup multiple build environments for each project.

The **loadme** script automatically looks up in parent git folders to find an existing **venv**.
If it finds one, it loads it instead of creating a new one in the current project folder.

Example layout:
```
projectA/
  + .git/
  + venv/
  + loadme.*
  + projectB/
  |--+ .git/
  |--+ loadme.*
  + subfolder/
  |--+ projectC/
     |--+ .git/
     |--+ loadme.*
```
When **loadme** scripts are used in **projectB** or **projectC**, the **venv** of **projectA** will be used.

## Suggested git files

When the build env manager prepares the build environment, it will verify if some recommended git files exist in current project:

* **.gitignore** should be configured so that **venv** and **.loadme** folders are ignored and not pushed to source control
* **.gitattributes** should be configured to handle platform-specific files with correct line endings:
  * **.bat** and **.cmd** files must always use **`crlf`** line endings
  * **.sh** files must always use **`lf`** line endings
