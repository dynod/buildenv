# Configuration

The **`buildenv`** tool can be configured thanks to a **`buildenv.cfg`** file, located in the project root folder.

If this file doesn't exist, all parameters will be initialized to default values.

## File format

The **`buildenv.cfg`** file uses the [Python's ConfigParser file format](https://docs.python.org/3/library/configparser.html) (AKA **.ini** file format).

## **`[local]`** vs **`[ci]`** sections

The **`buildenv`** tool allows to handle differently local builds and automated builds.

For local builds:
* parameters are read from the **`[local]`** section
* if a parameter doesn't exist in the **`[local]`** section, default value will be used

The **`buildenv`** tool detects a CI ("Continuous Integration") build when the **`CI`** environment variable exists and is not empty.
In this case, in order to enable some parameters to be overridden in automated build context:
* parameters are firstly read from the **`[ci]`** section
* if a given parameter doesn't exist in the **`[ci]`** section, it will be read from the **`[local]`** section
* if it also doesn't exist in the **`[local]`** section, default value will be used

## Environment variables references

Some parameters (identified in the table below) can reference environment variables. To reference a given **VAR** variable, use the **`${VAR}`** syntax in the parameter value.

If **.cmd** scripts are generated with some parameter value referencing an environment variable, any **`${VAR}`** reference will be automatically converted to the **`%VAR%`** **.cmd** syntax.

## Parameters list

This table describes all the parameters supported by the **buildenv** tool:

|Name                   |Default value          |Resolved env vars|Usage|
|-                      |-                      |-                |-
|**`venvFolder`**       | `venv`                | no  | Name of the folder where to python virtual env will be created in the project
|**`requirements`**     | `requirements.txt`    | no  | Name of the pip requirements file to be installed when creating the python virtual env, relative to project root folder
|**`prompt`**           | `buildenv`            | no  | Build environment name, to be diplayed on the command line in front of the system prompt, when running the **`buildenv`** shell
|**`windowsPython`**    | `python`              | yes | Python command to be used on Windows to create the virtual env
|**`linuxPython`**      | `python3`             | yes | Python command to be used on Linux to create the virtual env
|**`pipInstallArgs`**   | empty                 | yes | Extra arguments to be added to all `pip install` commands used to create the virtual env
|**`lookUp`**           | `true`                | no  | Look up for git root folder if not matching with current project root
