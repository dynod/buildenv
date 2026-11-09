# Environment backends

The **buildenv** tool relies on existing virtual environment management backends, delegating the environment creation/handling to them.

When a new **buildenv** is installed, you need to select one of the supported backends (see below).

Backends can be considered regarding several properties:

- **immutability**: a backend may create immutable environments; an immutable environment is disposable, only created for a temporary purpose, and not cached in the current project folder.
- **project** type: there is a difference between Python projects, for which it is usual to have the venv cached in the project folder, and other projects (i.e. which don't include any Python source code)
- **requirements** type: to manage a given environment dependencies, requirements shall be listed either using the [pip requirements file format](https://pip.pypa.io/en/stable/reference/requirements-file-format/), or be exclusively base on the [pyproject file](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#writing-pyproject-toml)
- **workspace** handling: for Python projects, it is usually convenient to share a given venv between projects

Supported backends by **buildenv** tool and their properties are described by this table

| Backend  | Immutable | Project type | Requirements format   | Workspace handling |
| -------- | --------- | ------------ | --------------------- | ------------------ |
| uv       | ❌        | Python       | pyproject.toml file   | ✅                 |
| uvx      | ✅        | other        | requirements.txt file | ❌                 |
| fallback | ✅        | other        | none                  | ❌                 |

## uv backend (recommended for Python projects)

The [uv](https://docs.astral.sh/uv/) tool is a fast Python package and project manager.

Using the **uv** backend is recommended for Python projects.

## uvx backend (recommended for other projects)

The [uvx](hhttps://docs.astral.sh/uv/guides/tools/) tool, backed by **uv**, is an utility allowing to easily handle disposable venv for Python-based tools, used for non-Python projects.

Using the **uvx** backend is recommended for non-Python projects.

(fallback)=

## Fallback backend

When detecting the active backend thanks to {py:class}`buildenv.backends.factory.EnvBackendFactory`, if detection fails (e.g. running from a system-level python install, or from a **pip** installed venv), a fallback backend will be used, unable to perform any package install/upgrade operation.
