# Experimental co-op story-entry hooks

This is an **unfinished mod**, not a four-player co-op release. The compiled
hooks enter castle grounds in story mode through the native VS lobby, retain
the lobby player count, and prevent the scratch session from writing adventure
saves. One local player reaches gameplay. Three Download Play clients discover
the host and download/boot its original executable, but reject the modified
lobby overlay before entering the lobby. Four-player story gameplay has not
passed. Host save persistence, synchronized campaign events, and completion
remain unimplemented/unverified.

Only the supplied **Europe revision 0** cartridge is supported:
`ce5829aaa79f06c67140ed1f45cbca738b0a9d0180538c8c1498472d859db032`.
Other region/revision ROMs are deliberately rejected.

## Build and inspect

```bash
cd /workspace/sm64ds-decomp
source /workspace/setup/activate.sh
python mods/coop/build.py /workspace/inputs/sm64ds-eu.nds --baseline
python mods/coop/build.py /workspace/inputs/sm64ds-eu.nds
python mods/coop/tests/test_image.py
bash mods/coop/tests/build_harness.sh
bash mods/coop/tests/local_story.sh
```

Outputs are local, ignored files in `build/coop/`. `baseline.nds` is an exact
retail copy, **not** a source rebuild. `sm64ds-coop-experimental.nds` contains
compiled `runtime.cpp` and `install.cpp` hooks; `build.json` records hashes,
cartridge patches, later RAM patches, and the failed authentication audit.
Do not distribute the ROMs, BIOS, firmware, extracted assets, or compiler files.

The builder verifies the input ROM and both proprietary toolchain executables,
links against the decompilation's canonical symbols, and changes only the
physical extent of overlay 75. ARM9, ARM7, header, FAT, overlay table, all other
files, and every decoded byte outside the explicit overlay patch ranges remain
unchanged. Five structural tests check those properties, hook destinations,
zeroed runtime state, and both original-instruction trampolines. Those checks
establish patch integrity; they do not establish wireless compatibility.

## Why native Download Play currently fails

There are two independent authentication stages:

1. The Download Play firmware authenticates the initial ARM9/ARM7 image. The
   native SDK also reconstructs secure-area bytes from the parent's **RAM**.
   Installing there during lobby initialization caused clients to stop at the
   Nintendo logo. Installation is now deferred until course loading/start.
2. The game's `func_0205dd9c` verifies each compressed overlay with HMAC-SHA1
   before decompression. Its digest table is embedded in the authenticated ARM9.
   Overlay 75 has changed, so the stock child clears it and calls `Crash()`.

Run the independent audit:

```bash
python mods/coop/audit_download_play.py /workspace/inputs/sm64ds-eu.nds
# Exit 0: all 103 stock overlays pass.
python mods/coop/audit_download_play.py build/coop/sm64ds-coop-experimental.nds
# Expected exit 2: overlay 75 fails. This is a known acceptance failure.
```

The pinned EU HMAC table starts at `0x0209a7ec`; overlay 75's stock digest is
`a107e77ffd6390ce9bfe5bf51f35b4a5e99c9e5a`. The key descriptor is at
`0x0209a04c`. Merely replacing that digest also changes the authenticated boot
image. Clearing the overlay's authentication flag does not help: the child
requires the flag and rejects it otherwise.

HaxxStation bypasses verification through the Download Station exploit; it
**does not sign a new Nintendo RSA signature**. Packaging has been exercised:

```bash
dspatch -s /workspace/inputs/download-station.nds \
  -i build/coop/sm64ds-coop-experimental.nds \
  -o build/coop/haxxstation-package-smoke.nds
```

That output is a packaging experiment. An integrated exploit boot stage must
load a child with updated overlay authentication data and connect it to the
SM64DS parent's wireless/filesystem session. The Download Station server itself
is not an SM64DS co-op host. That handoff is not implemented here. The Wii sender
also needs its Wii runtime; compiling/packaging it alone cannot supply the DS
host handoff.

## Emulator verification

The harness uses the unmodified melonDS 1.1 core at commit
`b86390e4428bf38ce4c1ce0e9ca446d6d25955e8` and its real `LocalMP` packet,
command, reply and acknowledgement transport. It uses software rendering,
interpreter execution, supplied native BIOS/firmware, distinct MACs and RAM-only
save/firmware writes. It does not simulate a client connection or replace the
wireless protocol. The linked core is GPL-3.0-or-later; upstream source and
license are retained in `/workspace/references/melonds`.

```bash
source /workspace/setup/activate.sh
bash mods/coop/tests/build_harness.sh
# Four real emulated DS systems: only the parent carries a cartridge.
python mods/coop/tests/download_play.py /workspace/inputs/sm64ds-eu.nds \
  --expect-mode 1 --output /workspace/runtime/stock-download-play
python mods/coop/tests/download_play.py build/coop/sm64ds-coop-experimental.nds \
  --output /workspace/runtime/mod-download-play
```

The second command is expected to fail until the overlay authentication and
exploit handoff are implemented. The driver records commands, RAM checks,
status, and all four screens. A successful smoke only establishes a four-player
stage in the requested rules mode, not campaign correctness. Fixed per-frame
barriers can stall wireless command/reply exchange; use `COOP_LIVE=1` for
interactive multi-console work, as the driver does.

For manual control:

```bash
COOP_LIVE=1 build/coop/melon-test build/coop/sm64ds-coop-experimental.nds - - -
```

`-` boots actual DS firmware without a cartridge. `COOP_INPUT_DIR` defaults to
`/workspace/inputs` and must contain `bios9.bin`, `bios7.bin`, and
`firmware-original.bin`. Commands include `run 120`, `touch 0 32 170`,
`release 0`, `keys 0 fef`, `screen 0 /tmp/screen.ppm`, `status`, `regs 0`,
`read 0 0209f21c 4`, and `dump 0 /tmp/ram.bin`. Keys use the DS active-low mask;
`fff` releases everything. Index 0 is the parent and 1–3 are clients.

Manual and automated stock testing reached VS gameplay on all four consoles,
with count 4, mode 1 and four player objects on each system. The automated run
passed at `/workspace/runtime/coop-automated-stock-final/`; manual evidence is
in `/workspace/runtime/coop-live/control-game-*.ppm`.
The late-install mod reached the game's loading screen on all clients, then
failed overlay authentication: `/workspace/runtime/coop-late/boot-client.ppm`,
`select-host.ppm`, and `client-ram.bin`. The local story replay and its input
commands are in `/workspace/runtime/coop-late/local-replay.commands` and
`local-stagefix4.log`; `replay-story.ppm` shows castle-grounds gameplay. The
committed `tests/local_story.sh` also passes: right input changes position from
(-1200, 254, 6800) to approximately (-946, 254, 6826) world units, in mode 0
with one player. Its RAM snapshots and screenshots are under `build/coop/`.

The final modified-image replay failed as expected on all three clients at
`0x02014104`/`0x020140fc`, before a story stage. Its complete transcript and all
four fatal-state screens are in `/workspace/runtime/coop-automated-mod-final/`.
This is an acceptance failure, not a passing multiplayer test. The reproducible
experimental ROM SHA-256 is
`400239390a383e5d1ce9b2341fd82a3e87f270126a654621c8aa2289a04a2930`.

| Check | Observed result |
| --- | --- |
| Existing profile/pin/fingerprint tests | 40 passed |
| New image-integrity/trampoline tests | 5 passed |
| Local story entry and movement | Passed, **one console** |
| Retail native Download Play stage | Passed, four consoles |
| Modified native Download Play stage | **Failed**, three clients in fatal loop |
| Retail overlay HMAC audit | 103/103 valid |
| Modified overlay HMAC audit | 102/103 valid; overlay 75 rejected |
| HaxxStation package parsing | Passed; exploit boot/handoff unverified |
| Full source-control behavior | **Failed**, white screen |

## Runtime and remaining work

The lobby's result-score/result-initializer code span `0x021165b0..0x02116ad4`
stores an installer and resident payload. Ordinary VS results are unsupported.
The payload installs at `0x02004100..0x02004800` only after boot authentication.
The lobby start uses `PrepareVsMode` for its existing transition, then selects
story rules, keeps the connected player count, initializes scratch progress,
skips the single-player introduction, and requests castle grounds.

Story actors overlap the lobby overlay. After ENTRY's normal resource cleanup,
the hook unmounts its archives **before** its temporary heap is destroyed.
At STAGE's level-overlay load it retires overlays 75, 100 and 102 once; the
normal story loader then loads its own object overlays. Reusing cached archives
from the destroyed lobby heap caused a reproduced data abort; clearing pointers
after heap destruction was insufficient because NitroFS still held mounts.

Progress stays in RAM. Restart before returning to ordinary adventure play:
the session save guard remains installed until reset. Persistent host-owned
saves, shared star/key decisions, cutscene/warp/death/disconnect policies, client
story-asset access, four independent inputs/cameras, deterministic actors and
full campaign completion all still need acceptance tests and fixes.

## Full source baseline

The user explicitly allowed a nonmatching source baseline if behavior matched.
The full source control compiled 2099 sources and linked, but produced a white
screen after 6720 emulated frames and touch input. Retail reached menus and
castle grounds. Thus the observed source control is not behaviorally equivalent;
the decision to use compiled fixed-address hooks preserves a working retail
baseline without claiming a full source rebuild succeeded. Evidence is under
`/workspace/runtime/baseline-ab/` and `build/tu/_baseline/link/`.

The strict control reports 15/106 exact modules and an ARM9 size increase of
32 bytes. These mismatches remain recorded; fidelity gates were not disabled
and original `src/`, shared headers and matching configuration were not edited.
