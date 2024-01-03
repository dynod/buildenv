# buildenv
Build environment setup system, based on Python venv

<!-- NMK-BADGES-BEGIN -->
[![License: MPL](https://img.shields.io/github/license/dynod/buildenv?color=green)](https://github.com/dynod/buildenv/blob/main/LICENSE)
[![Checks](https://img.shields.io/github/actions/workflow/status/dynod/buildenv/build.yml?branch=main&label=build%20%26%20u.t.)](https://github.com/dynod/buildenv/actions?query=branch%3Amain)
[![Issues](https://img.shields.io/github/issues-search/dynod/buildenv?label=issues&query=is%3Aopen+is%3Aissue)](https://github.com/dynod/buildenv/issues?q=is%3Aopen+is%3Aissue)
[![Supported python versions](https://img.shields.io/badge/python-3.8%20--%203.11-blue)](https://www.python.org/)
[![PyPI](https://img.shields.io/pypi/v/buildenv)](https://pypi.org/project/buildenv/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Flake8 analysis result](https://img.shields.io/badge/flake8-0-green)](https://flake8.pycqa.org/)
[![Code coverage](https://img.shields.io/codecov/c/github/dynod/buildenv)](https://app.codecov.io/gh/dynod/buildenv)
[![Documentation Status](https://readthedocs.org/projects/buildenv/badge/?version=stable)](https://buildenv.readthedocs.io/)
<!-- NMK-BADGES-END -->

## Features

The **`buildenv`** tool provides following features:
* simple build environment setup through loading scripts generated in your project
* configuration through a simple **`buildenv.cfg`** file
* extendable activation scripts, loaded with the build environment

The whole **`buildenv`** documentation is available at [https://buildenv.readthedocs.io](https://buildenv.readthedocs.io)

## Usage

### Project already configured with buildenv

Any project already using the **`buildenv`** tool has generated loading scripts in its root folder. Setting up the build environment is as easy as:
1. clone the project
1. launch the loading script (**`buildenv.cmd`** or **`buildenv.sh`** depending on your preferred shell)
1. enjoy, build environment (i.e. python venv + extensions) is now installed and loaded in your terminal

### Make a project using buildenv

To install loading scripts in your project:
1. download main python loading script -- `wget https://raw.githubusercontent.com/dynod/buildenv/main/buildenv-loader.py`
1. launch it:
    * on Linux: `python3 buildenv-loader.py`
    * on Windows: `python buildenv-loader.py`
1. you're done, loading scripts are generated in your project

## Local build

If you want to build locally the **`buildenv`** wheel, just:
1. clone the **`buildenv`** project
1. launch the loading script (see above)
1. build the project: `nmk build`
