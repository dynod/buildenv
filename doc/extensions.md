# Extensions

The **`buildenv`** tool behavior can be extended, with following extension points.

## Init hooks

The **`buildenv`** tool behavior can be extended, in order to:

- handle extra steps during the build environment initialization
- add activation scripts to be executed each time the build environment is loaded
- enable completion for extra commands when a **buildenv** interactive shell is invoked

Such extensions are contributed by registering classes into the **buildenv_init** entry point in a given python module setup configuration. Referenced class must extend the {py:class}`buildenv.extension.BuildEnvExtension` class.

Example syntax for entry point contribution:

```
[options.entry_points]
buildenv_init =
	my_extension = my_package.my_module:MyExtensionClass
```

## Project templates

Another way to extend **buildenv** is to provide project templates, than can be used when setting up a new project thanks to the {ref}`buildenv install<install>` command.

Such extensions are contributed by registering classes into the **buildenv_template** entry point in a given python module setup configuration. Referenced class must extend the {py:class}`buildenv.extension.BuildEnvProjectTemplate` class.
