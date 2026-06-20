# Project templates

Templates can be used when you want to setup from scratch a new project. Templates are provided by **buildenv** [extensions](extensions).

## Templates types

There are two types of templates: _main_ and _extra_ templates:

- _main_ template is the one giving the project structure
- _extra_ templates are used to add options to the _main_ one

```{note}
In the listed templates:
* the default *main* template is the one hightlighted with a `**` decorator
* the default *extra* templates are the ones hightlighted with a simple `*` decorator
```

## Listing templates

You can list available templates using the **--list-templates** option.

e.g. with `uvx --with nmk-python buildenv install --list-templates` command:

```{include} snippets/install-list-1.txt
:literal:
```

## Default templates selection

The selection of used templates is automatic from the contributions you use when invoking the install command thanks to [uvx](hhttps://docs.astral.sh/uv/guides/tools/) tool.

Without any extra option, the default `**` and `*` hightlighted templates will be used.

## Adding packages

If you want to immediately add some package dependencies to your new project, the **--add** option can be used.

e.g.: `uvx buildenv install --add conan`

## No templates

In order to ignore all templates, the **--no-template** option can be used.

e.g.: `uvx buildenv install --no-template`

In this case, only the [loading scripts](scripts) will be created, plus some default generated files:

- a **.gitignore** file, to ignore venv folder for non-immutable [backends](backends)
- a **.gitattributes** file, to handle line endings properly for [loading scripts](scripts)
- a **requirements.txt** file, if **--add** option is used to add extra packages to the project dependencies

## Selecting main template

If several main templates are available, it is possible to select one of them thanks to the **--template** option.

## Including/excluding extra templates

Used extra templates can be controlled with these options:

- **--extra-template** to add an extra template for project creation
- **--ignore-template** to remove an extra template for project creation
