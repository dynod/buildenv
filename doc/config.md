# Configuration

The **`buildenv`** tool can be configured thanks to a **`buildenv.cfg`**, located in the project root folder.

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

## Parameters list

This table describes all the parameters supported by the **buildenv** tool:

|Name               |Default value          |Usage|
|-                  |-                      |-
|**`venvFolder`**   | `venv`                | Name of the folder where to python virtual env will be created in the project
|**`requirements`** | `requirements.txt`    | Name of the pip requirements file to be installed when creating the python virtual env
|**`prompt`**       | `buildenv`            | Build environment name, to be diplayed on the command line in front of the system prompt, when running the **`buildenv`** shell
|**`windowsPython`**| `python`              | Python command to be used on Windows to create the virtual env
|**`linuxPython`**  | `python3`             | Python command to be used on Linux to create the virtual env
