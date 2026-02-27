#!/bin/bash

uvx --from /home/david/dev/dynod/tools/buildenv/out/artifacts/*.whl \
    buildenv install --backend uvx \
    --with /home/david/dev/dynod/tools/buildenv/out/artifacts/*.whl \
    --with nmk-vscode
