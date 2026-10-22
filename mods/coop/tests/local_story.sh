#!/bin/bash
# Verify actual story entry and movement in one emulated DS, not wireless co-op.
set -euo pipefail
coop_repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
cd "$coop_repo"
env -u COOP_LIVE timeout --kill-after=5 120 build/coop/melon-test \
  build/coop/sm64ds-coop-experimental.nds \
  < mods/coop/tests/local_story.commands > build/coop/local-story.log
python3 - <<'PY'
from pathlib import Path
import struct
positions = []
for name in ('before', 'after'):
    data = Path(f'build/coop/local-{name}.ram').read_bytes()
    assert data[0x9f21c] == 1, 'Expected one local player'
    assert data[0x9f2d8] == 0, 'Expected story rules'
    assert struct.unpack_from('<b', data, 0x9f2f8)[0] == 1, 'Expected castle grounds'
    player = struct.unpack_from('<I', data, 0x9f394)[0]
    assert 0x02000000 <= player < 0x02400000 - 0x768, 'No valid player object'
    positions.append(struct.unpack_from('<iii', data, player - 0x02000000 + 0x5c))
assert positions[0] != positions[1], 'Right input did not move the player'
print('Local castle-grounds story entry and movement passed (one console only).')
print('Positions in world units:', [tuple(round(v/4096, 2) for v in p) for p in positions])
PY
