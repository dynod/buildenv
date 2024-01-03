# Loading and activation scripts

The **`buildenv`** tool handle a set of scripts used to load and activate the build environment.

## Loading scripts

Loading scripts are stored in the project root folder. They are typically kept in source control, so that any user can setup the build environment just after having cloned the project, by simply running them.

Following scripts are generated (by **`buildenv init`** [command](cli.md)):
* **`buildenv-loader.py`** : main loading logic (python implementation)
* **`buildenv.cmd`** : wrapper to loading script, for Windows
* **`buildenv.sh`** : wrapper to loading script, for Linux (or git bash on Windows)

When launched, the loading script logic follows these steps:
* Check if python **venv** has already been created in the project, or in parent project folder (in case this project is cloned as a sub-module)
* If **venv** is not found:
    * create it, and enable activation scripts folder (see below)
    * upgrade pip and install buildenv wheel
    * if **`requirements.txt`** file exists in project, also install requirements
* Delegate execution to **`buildenv`** [command](cli.md)

```{note}
When looking up for parent project folder, the loading script looks for parent folders which are git clones (it doesn't simply recursively browse all parents).\
This behavior can be disabled by setting **`lookUp`** parameter to **`false`** in the [configuration file](config.md).\
In this case, the **venv** will always be created in project root folder.
```

## Activation scripts

The **venv** installed by **`buildenv`** tool is slightly modified to allow multiple activation files to be loaded when the **venv** is activated.\
To do this, a **venv/\[bin or Scripts\]/activate.d** folder is created, and main **activate** and **activate.bat** scripts are modified to load all scripts present in this folder.

To load these scripts in expected order, all scripts in this folder are prefixed with an **XX_** number.

Default activation scripts installed by **`buildenv`** are:
* **00_activate.sh** and **00_activate.bat**: original **venv** activate script, moved as basic activation script
* **XX_set_prompt.sh**: configures **VIRTUAL_ENV_PROMPT** env var (as done in **activate.bat**)
* **XX_completion.sh**: enables completion for **pip**, **buildenv**, and all commands contributed through {py:func}`buildenv.manager.BuildEnvManager.register_completion` method.

Extensions can add activation scripts in this folder through {py:func}`buildenv.manager.BuildEnvManager.add_activation_file` method.

All scripts in the activation folder are loaded each time the **venv** is activated:
* with standard **venv** scripts:
    * on Windows: **venv\Scripts\activate.bat**
    * on Linux (or git bash): **source venv/bin/activate**
* with **buildenv** [command](cli.md):
    * invoke an interactive shell: **buildenv shell**
    * run a command in build environment: **buildenv run xxx arg1 arg2...**
