# Command line interface

The **buildenv** tools comes with a command-line interface, described on this page.

This interface is supported by the different ways to invoke the **buildenv** tool:

- by calling one of the generated [loading scripts](scripts):
  - on Linux: `./buildenv.sh <args>`
  - on Windows: `buildenv.cmd <args>`
- by calling the **`buildenv`** command once the venv is loaded:
  - in venv: `buildenv <args>`
- by calling through tool wrappers, e.g.:
  - `uvx buildenv <args>` -- [see uvx documentation](https://docs.astral.sh/uv/guides/tools/)
  - `pipx run buildenv <args>` -- [see pipx documentation](https://pipx.pypa.io/stable/)

## General arguments

Here is the general **`buildenv`** command help page:

```{include} snippets/buildenv.txt
:literal:
```

### Common arguments (also usable in sub-commands)

- **`-h`** or **`--help`**: displays the help message and exits; this works for all sub-commands as well.
- **`-V`** or **`--version`**: displays the **`buildenv`** tool version and exits
- **`-p PROJECT`** or **`--project PROJECT`**: identifies the project folder (default is current folder)
- **`--shell SHELL`**: force using specified shell (by default, always spawn a **bash** shell, even on Windows)

### Default command

When invoked without sub-command, the **buildenv** command line interface will execute the **`shell`** sub-command.

(install)=

## `install` sub-command

```{include} snippets/install.txt
:literal:
```

This sub-command allows to:

- create or update the build environment [loading scripts](scripts) in the specified project
- setup a new project using one of the provided templates

### Choosing a backend

By default, the used [environment backend](backends) is detected from the one used to launch the install command; e.g. if the `uvx buildenv install` command is invoked, the selected backend will be **uvx**.

It it possible to override this detection by using the **--backend** option.

### Using templates

The templates related options are described in the [project templates documentation](templates).

(init)=

## `init` sub-command

```{include} snippets/init.txt
:literal:
```

This sub-command creates the venv (if needed) and initializes extensions in the current project folder. It is implicitely called when using the **`shell`** or the **`run`** sub-commands.

If the initialization was previously fully completed, this command has no effect.

The initialization can be performed again only if the **`--force`** option is used.

It is possible to skip some extensions on init, by using the following options:

- **`--skip-ext EXT`**: skip a given extension (by its id)
- **`--no-ext`**: skip all extensions

## `shell` sub-command

```{include} snippets/shell.txt
:literal:
```

This sub-command invokes an interactive shell with the build environment enabled (i.e. original python venv + all enabled extensions provided by **`buildenv`** tool).

Just type **`exit`** to quit this interactive shell.

To be compatible with usual shells interface, it is possible to use the **-c** option to specify the command to be executed; e.g. as you can run `bash -c echo hello`, you can do the same with `buildenv shell -c echo hello`

```{note}
Running either `buildenv shell -c echo hello` command or `buildenv run echo hello` command behave exactly the same way.
```

## `run` sub-command

```{include} snippets/run.txt
:literal:
```

This sub-command invokes the provided command with the build environment enabled (i.e. original python venv + all enabled extensions provided by **`buildenv`** tool), then returns.

## `list` sub-command

```{include} snippets/list.txt
:literal:
```

This sub-command lists all installed packages the current buildenv environment (similarly to `pip list`, except that, depending on used [backend](backends), the `pip` command is not always available).

## `lock` sub-command

```{include} snippets/lock.txt
:literal:
```

This command locks the current build environment. The locking behavior depends on the used [environment backend](backends).

## `unlock` sub-command

```{include} snippets/unlock.txt
:literal:
```

This command unlocks the current build environment. The unlocking behavior depends on the used [environment backend](backends).

## `upgrade` sub-command

```{include} snippets/upgrade.txt
:literal:
```

This sub-command upgrades packages installed in python venv to their latest available version.

```{note}
If the used [environment backend](backends) is immutable, and this command is launched from an interractive shell, it will spawn a new sub-shell with the upgraded venv.
```
