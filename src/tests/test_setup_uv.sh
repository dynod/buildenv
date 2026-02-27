#!/bin/bash

ls /home/david/dev/dynod/tools/buildenv/out/artifacts/*.whl

uvx --from /home/david/dev/dynod/tools/buildenv/out/artifacts/*.whl \
    buildenv install --backend uv
