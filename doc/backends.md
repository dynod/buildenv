# Environment backends

The **buildenv** tool relies on existing virtual environment management backends, delegating the environment creation/handling to them.

When a new **buildenv** is installed, you need to select one of the supported backends (see below).

Backends can be considered regarding several properties:

- **immutability**: a backend may create immutable environments; an immutable environment is disposable, only created for a temporary purpose, and not cached in the current project folder.
- **project** type: there is a difference between Python projects, for which it is usual to have the venv cached in the project folder, and other projects (i.e. which don't include any Python source code)
- **requirements** type: to manage a given environment dependencies, requirements shall be listed either using the [pip requirements file format](https://pip.pypa.io/en/stable/reference/requirements-file-format/), or be exclusively base on the [pyproject file](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#writing-pyproject-toml)
- **workspace** handling: for Python projects, it is usually convenient to share a given venv between projects

Supported backends by **buildenv** tool and their properties are described by this table

| Backend | Immutable | Project type | Requirements format   | Workspace handling |
| ------- | --------- | ------------ | --------------------- | ------------------ |
| uv      | ❌        | Python       | pyproject.toml file   | ✅                 |
| uvx     | ✅        | other        | requirements.txt file | ❌                 |
| pip     | ❌        | Python       | requirements.txt file | ❌                 |
| pipx    | ✅        | other        | requirements.txt file | ❌                 |

## uv backend (recommended for Python projects)

The [uv](https://docs.astral.sh/uv/) tool is a fast Python package and project manager.

Using the **uv** backend is recommended for Python projects.

## uvx backend (recommended for other projects)

The [uvx](hhttps://docs.astral.sh/uv/guides/tools/) tool, backed by **uv**, is an utility allowing to easily handle disposable venv for Python-based tools, used for non-Python projects.

Using the **uvx** backend is recommended for non-Python projects.

## pip backend (legacy)

The legacy [pip](https://pip.pypa.io/en/stable/) tool is mainly a package manager, without being a project manager.

It is supported for compatibility with legacy projects, but not recommended for new projects.

## pipx backend (legacy)

Backed either by **pip** or **uv**, (pipx)[https://pipx.pypa.io/stable/] is a legacy disposable venv handling solution, not recommended for new projects.
