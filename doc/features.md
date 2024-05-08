# Features

The purpose of the **`buildenv`** tool is to help projects to setup easily a build environment (based on [Python virtual environment](https://docs.python.org/3/library/venv.html), or "**venv**"), just after clone, with minimal dependencies (i.e. only [**git**](https://git-scm.com/) and [**python**](https://www.python.org/)).

## Simple setup with loading scripts

The main feature of the **`buildenv`** tool is to generate [loading scripts](scripts) in the project root folder, ready to be executed just after the project is cloned, and loading everything so that the project is ready to build (whatever is the used build system).

See [usage instructions](./usage.md) for details.

### New project

Any project can be simply setup to use **`buildenv`** by running a simple standalone python script in the project root folder:
1. download **buildenv** script (python version) -- `wget https://raw.githubusercontent.com/dynod/buildenv/main/buildenv-loader.py`
1. launch it:
    * on Linux: `python3 buildenv-loader.py`
    * on Windows: `python buildenv-loader.py`
1. you're done, the project now also embeds **buildenv** [loading scripts](scripts) for a more convenient day to day use

## Launch build terminal from explorer

By default, the [loading scripts](scripts) are spawning a new shell process. It means that when launched from the OS explorer (Windows/Linux), a build terminal will be launched, initialized with the build environment context, and stay openned to let you entering shell commands.

On Windows, it works with both:
* **buildenv.cmd**: that will open the terminal in a **cmd** window (or better, in [Windows Terminal](https://github.com/microsoft/terminal) if installed)
* **buildenv.sh**: that will open the terminal in a **git bash** window (see [gitforwindows.org](https://gitforwindows.org/))

## Shared venv

You may work on multiple projects, and want to avoid to setup multiple build environments for each project.

The [loading scripts](scripts) automatically looks up in parent git folders to find an existing **venv**.
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
When [loading scripts](scripts) are used in **projectB** or **projectC**, the **venv** of **projectA** will be used.

````{note}
This behavior can be disabled by setting **`lookUp`** parameter to **`false`** in the [configuration file](config.md).\
In this case, the **venv** will always be created in project root folder.
````

## Suggested git files

When the build env manager prepares the build environment, it will verify if some recommended git files exist in current project.
If not, these files will be generated with default content:

* **.gitignore** is configured so that virtual env and **.buildenv** folders are ignored and not pushed to source control
* **.gitattributes** is configured to handle platform-specific files with correct line endings:
  * **.bat** and **.cmd** files must always use **`crlf`** line endings
  * **.sh** files must always use **`lf`** line endings

## Completion

When running on Linux (or in Git bash on Windows), completion is automatically enabled when running in **`buildenv`** shell for following commands:
* **`buildenv`**
* **`pip`**

Completion can be enabled for other commands from **`buildenv`** extensions.

## Extensions

The **`buildenv`** tool behavior can be extended, to perform:
* extra steps during the build environment initialization
* add activation scripts to be executed each time the build environment is loaded

Extensions are contributed by registering classes into the **buildenv_init** entry point in a given python module setup configuration. Referenced class must extend the {py:class}`buildenv.extension.BuildEnvExtension` class.

Example syntax for entry point contribution:
```
[options.entry_points]
buildenv_init = 
	my_extension = my_package.my_module:MyExtensionClass
```

## Limitations

The **`buildenv`** tool refuses to create a venv in a path containing space characters.\
This decision has been made since in this case, some venv scripts (e.g. **register-python-argcomplete**) get their "shebang" line containing spaces, which is not supported.\
It looks to be a limitation only on Linux, but using spaces in paths for development seems to be definitely a bad idea, so **`buildenv`** makes no difference and doesn't support them on all platforms.
