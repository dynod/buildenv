# Command line interface

The **buildenv** tools comes with a command-line interface, described on this page.

This interface is supported by the different ways to invoke the **buildenv** tool:
* by calling one of the generated [loading scripts](scripts):
  * on Linux: `./buildenv.sh <args>`
  * on Windows: `buildenv.cmd <args>`
* by calling the **`buildenv`** command once the venv is loaded:
  * in venv: `buildenv <args>`
* by launching manually the python loading script (as described by bootstrap instructions):
  * bootstrap script: `python buildenv-loader.py <args>`

## General arguments

Here is the general **`buildenv`** command help page:

```
> buildenv -h
usage: buildenv [-h] [-V] {init,shell,run} ...

Build environment manager

positional arguments:
  {init,shell,run}  sub-commands:
    init            initialize the build environment and exit
    shell           start an interactive shell with loaded build environment
    run             run command in build environment

optional arguments:
  -h, --help        show this help message and exit
  -V, --version     show program's version number and exit
```

### Arguments

* **`-h`** or **`--help`**: displays the help message and exits; this works for all sub-commands as well.
* **`-V`** or **`--version`**: displays the **`buildenv`** tool version and exits

### Default command

Depending on the calling context (see above), when invoked without sub-command, the **buildenv** command line interface will execute:

* the **`shell`** sub-command if invoked through a [loading script](scripts)
* the **`init`** sub-command otherwise

## `init` sub-command

Usage:
```
> buildenv init -h
usage: buildenv init [-h] [--force | --skip]

initialize the build environment and exit

options:
  -h, --help   show this help message and exit
  --force, -f  force buildenv init to be triggered again
  --skip, -s   skip extensions and activation scripts generation
```

This sub-command generates the [loading and activation scripts](scripts) in the current project folder. It is implicitely called when using the **`shell`** or the **`run`** sub-commands.

If the initialization was previously fully completed, this command has no effect.

The initialization will be performed again only if:
* the **`--force`** option is used
* any version (**`buildenv`** itself one and all extensions ones) has changed since last initialization

The **`--skip`** option can be used to only generate the project loading scripts. It will skip the extensions init, and the activation scripts generation.

## `shell` sub-command

Usage:
```
> buildenv shell -h
usage: buildenv shell [-h]

start an interactive shell with loaded build environment

optional arguments:
  -h, --help  show this help message and exit
```

This sub-command invokes an interactive shell with the build environment enabled (i.e. original python venv + all enabled extensions provided by **`buildenv`** tool).

Just type **`exit`** to quit this interactive shell.

````{warning}
Shell "inception" (i.e. shell within shell) is not supported. \
In other words, **`shell`** sub-command is refused if executed from a running buildenv shell instance.
````

## `run` sub-command

Usage:
```
> buildenv run -h
usage: buildenv run [-h] ...

run command in build environment

positional arguments:
  CMD         command and arguments to be executed in build environment

optional arguments:
  -h, --help  show this help message and exit
```

This sub-command invokes the provided command with the build environment enabled (i.e. original python venv + all enabled extensions provided by **`buildenv`** tool), then returns.

````{warning}
Run "inception" (i.e. run within shell) is not supported. \
In other words, **`run`** sub-command is refused if executed from a running buildenv shell instance.
````
