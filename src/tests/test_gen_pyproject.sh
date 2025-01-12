#!/bin/bash

uvx --with /home/david/dev/dynod/tools/buildenv/out/artifacts/*.whl \
    --from /home/david/dev/dynod/tools/nmk/out/artifacts/*.whl \
    --with /home/david/dev/dynod/tools/nmk-base/out/artifacts/*.whl \
    --with /home/david/dev/dynod/tools/nmk-vscode/out/artifacts/*.whl \
    --with /home/david/dev/dynod/tools/nmk-python/out/artifacts/*.whl \
    nmk py.project --config pythonUseUvBackend=true -f
