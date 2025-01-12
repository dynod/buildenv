#!/bin/bash

uvx --from /home/david/dev/dynod/tools/buildenv/out/artifacts/*.whl \
    --with /home/david/dev/dynod/tools/nmk/out/artifacts/*.whl \
    --with /home/david/dev/dynod/tools/nmk-base/out/artifacts/*.whl \
    --with /home/david/dev/dynod/tools/nmk-vscode/out/artifacts/*.whl \
    buildenv2 install --backend uvx \
    --with /home/david/dev/dynod/tools/buildenv/out/artifacts/*.whl \
    --with /home/david/dev/dynod/tools/nmk/out/artifacts/*.whl \
    --with /home/david/dev/dynod/tools/nmk-base/out/artifacts/*.whl \
    --with /home/david/dev/dynod/tools/nmk-vscode/out/artifacts/*.whl
