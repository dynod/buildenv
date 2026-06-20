# Usage

In order to use **`buildenv`** tool features, please follow these instructions.

## Project already configured with buildenv

Any project already using the **`buildenv`** tool has generated [loading scripts](scripts.md) in its root folder.\
The typical project setup scenario with **`buildenv`** is:

1. clone the project -- `git clone git@github.com:xxx/yyy.git`
1. launch the loading script:
   - on Linux (or git bash): `./buildenv.sh`
   - on Windows: `buildenv.cmd`
1. build the project; the build environment (i.e. python venv + extensions) is now installed and loaded in your terminal

## Install buildenv in a new/existing project

### New projects

The {ref}`buildenv install<install>` command can be used, with ad-hoc templates selection, in install to create a new project from scratch, with ready to use environment for the chosen project type.

The recommended install process is to run the command through an [uvx](hhttps://docs.astral.sh/uv/guides/tools/) command, including templates extensions.

As an example, in order to setup a new [nmk Python](https://nmk-python.readthedocs.io/) project from scratch, you may simply execute the following command:

> `uvx --with nmk-python buildenv install -p /path/to/my/new/project`

### Migrate legacy buildenv projects

For project already using **buildenv** 1.X version, using the {ref}`buildenv install<install>` command will:

- upgrade the [loading scripts](scripts) for **buildenv** 2
- remove the legacy useless files from the project

```{note}
It is important to choose the [backend](backends) when upgrading the scripts. You should run:
* `uvx buildenv install --backend uv` for Python projects
* `uvx buildenv install --backend uvx` for non-Python projects
```
