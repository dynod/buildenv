# Environment variables

The buildenv tool deals with several environment variables, explained in this chapter. Environment variables are split in two categories:

- those exposed by buildenv
- and those consumed to configure buildenv behavior

## Exposed env vars

The variables listed in this chapter are exposed by buildenv in any spawned shell/subprocess.

---

### `BUILDENV_LEVEL` -- level of shell inception

While discouraged, it is possible to spawn a buildenv shell inside a buildenv shell. The **`BUILDENV_LEVEL`** tracks this level of shell inception:

- first spawned shell has **`BUILDENV_LEVEL`** value of **1**
- if a new shell is spawned from this one, its **`BUILDENV_LEVEL`** value will be **2**
- etc...

Example:

```shell
(buildenv:uv) ❯ echo $BUILDENV_LEVEL
1
(buildenv:uv) ❯ buildenv shell
[WARNING] Spawning a new buildenv!
[WARNING] Even if this is not forbidden, you may prefer exiting the current shell before launching a new one.
Welcome to buildenv shell!
(buildenv:uv*) ❯ echo $BUILDENV_LEVEL
2
```

---

(BUILDENV_VERSION)=

### `BUILDENV_VERSION` -- loading scripts version

As [loading scripts](scripts) are kept in source control in a given buildenv project, their current version is exposed in the **`BUILDENV_VERSION`** variable, in order to help detecting outdated scripts WRT. buildenv version itself.

Evolution of **`BUILDENV_VERSION`** compared to buildenv version is tracked in the [Changelog](changelog).

Example:

```shell
(buildenv:uv) ❯ echo $BUILDENV_VERSION
3
```

---

## Configuration env vars

These variables are used by buildenv for configuration.

---

### `BUILDENV_UV_ARGS` -- uv backend extra args

This variable is used by {ref}`uv backend<uv-b>` loading script to pass extra args to the `uv run buildenv` command.

---

### `BUILDENV_UVX_ARGS` -- uv backend extra args

This variable is used by {ref}`uvx backend<uvx-b>` loading script to pass extra args to the `uvx buildenv` command.
