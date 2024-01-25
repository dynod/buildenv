# Usage

In order to use **`buildenv`** tool features, please follow these instructions.

## Project already configured with buildenv

Any project already using the **`buildenv`** tool has generated [loading scripts](scripts.md) in its root folder.\
The typical project setup scenario with **`buildenv`** is:

1. clone the project -- `git clone git@github.com:xxx/yyy.git`
1. launch the loading script:
    * on Linux (or git bash): `./buildenv.sh`
    * on Windows: `buildenv.cmd`
1. build the project; the build environment (i.e. python venv + extensions) is now installed and loaded in your terminal

## Install buildenv in a new/existing project

Any project can be simply setup to use **`buildenv`**, by following one of these methods:

### Script install

1. download [main python loading script](https://raw.githubusercontent.com/dynod/buildenv/main/buildenv-loader.py):
    * use your browser **right-click > save link as** feature on the above link
    * or on Linux, run `wget https://raw.githubusercontent.com/dynod/buildenv/main/buildenv-loader.py`
1. launch the script:
    * on Linux: `python3 buildenv-loader.py`
    * on Windows: `python buildenv-loader.py`
1. you're done, loading scripts are generated in your project

### Bootstrap from an existing python install

If you already have a python environment with **`buildenv`** tool installed, you can use the `buildenv init --new <path>` {ref}`command<init>`
to bootstrap a new build environment in the specified folder.

Then, just run the generated [loading script](./scripts.md) for your preferred shell to load the new build environment.
