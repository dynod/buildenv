#!/bin/bash

ls /home/david/dev/dynod/tools/buildenv/out/artifacts/*.whl
ls /home/david/dev/dynod/tools/nmk/out/artifacts/*.whl
ls /home/david/dev/dynod/tools/nmk-base/out/artifacts/*.whl
ls /home/david/dev/dynod/tools/nmk-vscode/out/artifacts/*.whl
ls /home/david/dev/dynod/tools/nmk-python/out/artifacts/*.whl

uvx --from /home/david/dev/dynod/tools/buildenv/out/artifacts/*.whl \
    buildenv install --backend uv
