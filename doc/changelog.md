# Changelog

Here are listed all the meaningfull changes done on **`buildenv`**.

```{note}
Only interface and important behavior changes are listed here.

The fully detailed changelog is also available on [Github](https://github.com/dynod/buildenv/releases)
```

## Release 2.0

### Environment creation refactoring

**buildenv** now relies on [environment backends](backends).

### New features

- [project templates](templates) handling
- new **install**, **list**, **lock** and **unlock** sub-commands for [buildenv command](cli)

### Breaking changes from buildenv 1.X

Here are the updates which may break something since **buildenv** 1.X releases

#### <font color="red">Removed buildenv init '--new' option</font>

The **--new** option has been removed from the {ref}`buildenv init<init>` command. The project/environment setup has been moved to a new {ref}`buildenv install<install>` command.

#### <font color="red">No more python loading script</font>

The **`buildenv-loader.py`** script is now deprecated and can be safely removed from any project upgraded to **buildenv** 2.0 or higher.

The loading logic is now simply delegated to [environment backend](backends) through the shell script(s).

#### <font color="red">No more buildenv.cfg file</font>

Related to previous change, **buildenv** doesn't read its configuration from **`buildenv.cfg`** file anymore. Since it now relies on [environment backend](backends), it naturally and simply uses each backend-related configuration system instead of providing its own one.

Any **`buildenv.cfg`** file can be safely removed from any project upgraded to **buildenv** 2.0 or higher.

#### <font color="red">Extensions API redesign</font>

The extension API has be redesigned from zero. Any existing **buildenv** 1.X extension will be ignored by **buildenv** 2.0 or higher, and should be rewritten to plug on the new API (see {py:class}`buildenv.extension.BuildEnvExtension`) and **`buildenv_extension`** entrypoint (instead of **`buildenv_init`** legacy one).

#### <font color="red">No more shared venv with pip backend</font>

The parent **venv** searching logic was part of the **`buildenv-loader.py`** script. Since the new design delegates this part to the used backend, the availability of this feature depends on the backend itself (supported by **`uv`** backend, but not by **`pip`** one).
