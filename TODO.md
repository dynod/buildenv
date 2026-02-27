[X] pipx: functional test on Windows
[X] pip: functional test on Linux
[X] pip: functional test on Windows
[X] uv: functional test on Linux
[X] uv: functional test on Windows
[X] better pip stub wording with uv (no requirements.txt file)
[X] how to handle "--with" option for install with uv backend?
[X] handle uv/uvx completion in buildenv shell
[X] handle packages install
[X] handle freeze support
[X] ajouter un warning (voire une protection) pour buildenv dans buildenv
[X] update le prompt en (buildenv\*), (buildenv\*\*), etc...
[X] buildenv upgrade:
[x] pipx/uvx : spawn un sous-shell avec argument refresh
_ [X] pip/uv : appeler l'install
_ [X] dumper la liste des versions upgradées
_ [X] kill le shell parent si on spawn un sous-shell
_ [X] si buildenv locké, updater le lockfile
[X] nmk py.venv :
_ [X] si non mutable, stop + message suggérant de faire le buildenv upgrade à la main.
_ [X] sinon appeler l'upgrade du backend
[X] handle backend subprocesses output in log (debug level)
[X] update current env in buildenv process, before calling extensions; so that BUILDENV legacy is correctly detected
[X] make evolutions on nmk\* to support buildenv2 (if present; fallback to buildenv otherwise)
[x] nmk-base: remove .buildenv from gitignore if not legacy backend
_ [X] nmk-vscode: don't exclude venv if non-mutable
_ [X] fix legacy buildenv detection (handle buildenv version in env)
_ [X] nmk-python: make it working with uv backend
_ [X] project file generation + sync
_ [X] install in editable mode
_ [X] build/install the wheel
_ [X] build with uv build (refactor build backend)
_ [X] handle uninstall
_ [X] disable auto venv loading from vscode
_ [X] test uv build backend
\_ [X] nmk: restore model.pip_args wth legacy backend

[X] replace buildenv2 entrypoint everywhere
[X] final nmk-\_ update after rename: nmk / nmk-vscode / nmk-base / nmk-python
[X] handle git init + chmod
[ ] check prompt in cmd (no prefix?)
[ ] handle templating system for install (to setup template projects for nmk-python, etc...)
[ ] fix update message on install (from xxx editable version to a dummy one???)
[ ] consider delivering an alpha version on pypi
[ ] nmk-python uv backend: test uv.lock file behavior
[ ] generate a default pyproject.toml with uv backend? (because uv can't do anything if there is no pyproject.toml)
[ ] Once alpha is ready, check for pipx test on CI
[ ] Once alpha is ready, add constraint to install >=2a version (otherwise it won't work until official 2.0.0)
[ ] workspace handling with uv
[ ] documentation update
[ ] clean old stuff
[ ] clean buildenv-loader.py on install (?)
[ ] 2.0.0!
[ ] on nmk\*, clean buildenv2 support (replace by version detection on buildenv)
[ ] on nmk, add warning about run_pip and model.pip_args access (deprecated stuff) --> remove from nmk 2.0
[ ] se protéger contre le fail : en cas d'upgrade de buildenv ou nmk.
