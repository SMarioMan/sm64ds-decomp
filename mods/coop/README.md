# Experimental four-player co-op

Four-player castle-grounds gameplay through DS Download Play has passed with
one cartridge parent and three firmware-only melonDS clients. Each console
controls a distinct player, positions synchronize across the party, and shared
pause/resume follows the host. This is still an unfinished campaign mod:
persistent host saves, campaign transitions, stars/keys, cutscenes, deaths,
disconnects and completion need implementation or broader acceptance.

The runtime loads into a persistent ROOT allocation to make room for those
policies. This layout passes four-console story entry, independent movement
and shared pause/resume in `/workspace/runtime/short-handoff-game/result.json`.
Further interaction changes are under wireless regression testing. Earlier
passing evidence is in `/workspace/runtime/frame-progress-game/` and
`/workspace/runtime/appended-files-timeout100/`. Direct stock Download Play
still rejects the modified overlay; the integrated HaxxStation path is required.

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
python mods/coop/tests/local_campaign.py --output /workspace/runtime/local-campaign
```

Outputs are local, ignored files in `build/coop/`. `baseline.nds` is an exact
retail copy, **not** a source rebuild. `sm64ds-coop-experimental.nds` contains
compiled `runtime.cpp` and `install.cpp` hooks; `build.json` records hashes,
cartridge patches, later RAM patches, and the failed authentication audit.
Do not distribute the ROMs, BIOS, firmware, extracted assets, or compiler files.

The builder verifies the input ROM and both proprietary toolchain executables.
It preserves ARM9, ARM7, overlay tables, native file extents and all native files
except the explicit overlay-75 hook ranges. A relocated FAT exposes one appended
runtime module; capacity, used-size and header CRC are updated. Five structural
tests check those limits, hook destinations, zeroed module state and all five
original-instruction trampolines. Gameplay is checked separately in melonDS.

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

That output alone does not supply the game-session handoff. The bootstrap work
below exercises the exploit separately and integrates the signed loader into
the SM64DS parent. Returning its clients to the game's wireless/filesystem
session has passed castle-grounds entry and movement with four consoles.
Campaign progression remains unfinished. The Wii sender needs its Wii runtime.

## Integrated HaxxStation bootstrap experiments

The bootstrap uses the supplied Download Station Volume 1 client without
changing its Nintendo-signed SRL or signature. A heap-loaded parent service
replaces the initial image offered by SM64DS with that signed client, then
implements its ports 13–15 menu and payload transfers. The host remains in the
SM64DS lobby throughout. Four appended raw file IDs hold bootstrap assets;
the native level archives remain intact. A relocated FAT at a fixed offset
keeps probe and game-handoff filesystem headers identical. The original
fixed-extent patch restrictions above apply only to the base experimental ROM,
not this separate bootstrap variant.

```bash
source /workspace/setup/activate.sh
python mods/coop/bootstrap/build_probe.py
python mods/coop/bootstrap/build_host.py
python mods/coop/bootstrap/smoke.py --parent station --probe \
  --output /workspace/runtime/haxxstation-probe
python mods/coop/bootstrap/smoke.py --parent native --probe \
  --clients 3 \
  --output /workspace/runtime/native-haxxstation-probe
```

The first smoke has executed modified SM64DS ARM9 on a cartridge-free client:
RAM `0x02000000` contains `COOP` and `0x02000004` contains boot kind 2. This
establishes unsigned execution through the real exploit, **not gameplay**.
Evidence is in `/workspace/runtime/haxx-boot-probe/full-replay-yes.log`.
The native SM64DS parent has also passed the full unsigned probe on three
firmware-only clients: `/workspace/runtime/native-fast-three/`. All three RAM
snapshots contain `COOP` and boot kind 2. The parent retains its wireless session
while the signed clients reconnect, clears their old multiboot file entries,
and stops MB control packets during application transfers. Each application
packet completes before its buffer is reused for the next one. Boot timing
has shown intermittent failures and remains under investigation. Changing the
sender does not change Nintendo's signature.

An additional builder prepares a game executable with overlay 75's updated
HMAC, preserving verification and checking all 103 overlay hashes before
stripping the files that the parent will eventually serve:

```bash
python mods/coop/bootstrap/build_client.py
python mods/coop/bootstrap/build_host.py \
  --package build/coop/bootstrap/haxxstation-game-client.nds \
  --clients 3 --handoff \
  --output build/coop/bootstrap/sm64ds-haxxstation-game-handoff.nds
python mods/coop/bootstrap/smoke.py --parent native --story --clients 3 \
  --image build/coop/bootstrap/sm64ds-haxxstation-game-handoff.nds \
  --output /workspace/runtime/native-story-acceptance
# Add --shared-menus --castle-entry to exercise dialogue, key and door flow.
```

This image is a handoff experiment, not a playable wireless release. Its files
must come from the matching parent; a successful hash audit does not prove
that the native filesystem session has connected. `game-client.json` records
the parent hash, changed overlay hashes, package hash and audit result. The
handoff builder refuses a package whose overlay-75 digest differs from the
parent's. A pre-crt0 client stub restores SM64DS's game ID in the inherited
Download Play descriptor, retaining the parent's MAC, channel and TGID. The
parent restores its temporary hooks and enters the native player-sync step
before ENTRY can release its scene heap. The downloaded header retains the
parent's FNT, FAT and overlay-table extents: WFS uses these extents to size its
table allocation even though the unsigned payload itself omits those files.
The parent frees the menu, payload and transmit buffers before loading lobby
assets, leaving the small executable bootstrap allocated safely.

For debugging, `COOP_PACKET_LOG=/absolute/path.bin` records actual transmitted
wireless frames without changing or injecting packets. Records contain five
little-endian 32-bit fields (kind, console, byte length, timestamp low/high),
followed by frame bytes. Kinds 1/2/3 are MP commands, replies and ordinary
wireless packets. The log stops after 100,000 records. Driver transcripts,
screenshots, RAM snapshots and register dumps distinguish transfer progress
from successful execution.

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
This is an acceptance failure, not a passing multiplayer test. The current
experimental ROM SHA-256 is recorded by each build in `build/coop/build.json`.

| Check | Observed result |
| --- | --- |
| Existing profile/pin/fingerprint tests | 40 passed |
| New image-integrity/trampoline tests | 5 passed |
| Local story entry and movement | Passed, **one console** |
| Retail native Download Play stage | Passed, four consoles |
| Modified native Download Play stage | **Failed**, three clients in fatal loop |
| Retail overlay HMAC audit | 103/103 valid |
| Modified overlay HMAC audit | 102/103 valid; overlay 75 rejected |
| HaxxStation unsigned ARM9 probe, Download Station parent | Passed, one cartridge-free client |
| Signed Download Station loader/menu, SM64DS parent | Passed, three cartridge-free clients |
| Unsigned ARM9 probe, SM64DS parent | Passed, three cartridge-free clients |
| Modified game-client executable startup | Passed, three cartridge-free clients |
| Native lobby and WFS handoff | Four connected players; filesystem table mounted on all four consoles |
| Four-player story stage and movement | Passed, four consoles, normal pacing; see `frame-progress-game/result.json` |
| Shared pause/resume | Passed, host controls the synchronized shared menu |
| Game-client updated overlay HMAC audit | 103/103 valid; four-player castle gameplay passed |
| Full source-control behavior | **Failed**, white screen |

## Runtime and remaining work

The lobby's result-score/result-initializer code span `0x021165b0..0x02116ad4`
holds a small loader. Ordinary VS results are unsupported. After authentication,
it loads the appended ARM module into ROOT, relocates internal addresses and
external branches, and caches its entry pointer at `0x02004180`. The runtime
survives overlay changes without occupying the parent's bootstrap loader at
`0x02004200`. The lobby start selects story rules, keeps the connected player
count, initializes scratch progress, skips the introduction and requests castle
grounds. Shared scene decisions use the host controller; player behavior and
rendering retain the local controller/camera index.

The interaction hooks also scope actor behavior to the host's player
index, including doors that otherwise select a different local player on each
console. Player behavior selects each actor's own synchronized controller as
usual; the local index is restored after actor behavior. These hooks pass
four-console entry, independent movement and pause/resume at
`/workspace/runtime/actor-policy-timeout25/`. The locked door, Lakitu and rabbit
capture reached the castle-key flag on all four consoles, but a subsequent
position comparison failed: the host's Yoshi differed from the three guests by
about 29 world units. That is a failed synchronization check, not campaign
acceptance. The current follow-up isolates actor random draws using the shared
NET frame and stage-relative actor identity; wireless validation is pending.
Single-console key collection and castle-interior entry passed at
`/workspace/runtime/local-castle-entry/`.
The controller-driven `--castle-key` check follows the locked-door and Lakitu
prerequisite before pursuing the key rabbit. It reads game state and sends
controller input; it does not grant keys or move actors through memory writes.

Story actors overlap the lobby overlay. After ENTRY's normal resource cleanup,
the hook unmounts archives 1–12 **before** its temporary heap is destroyed.
Archive 0 belongs to ROOT on the parent and clients and stays mounted, avoiding
a redundant 320 KB read and wireless transfer at the transition.
At STAGE's level-overlay load it retires overlays 75, 100 and 102 once; the
normal story loader then loads its own object overlays. Reusing cached archives
from the destroyed lobby heap caused a reproduced data abort; clearing pointers
after heap destruction was insufficient because NitroFS still held mounts.

Story loading also needs the main loop to keep exchanging native NET frames.
The runtime services NET while clients wait for asynchronous WFS reads,
preserving native loading flags and the completion barrier. The run in
`/workspace/runtime/net-read-game/` loaded the common/text/castle archives and
story overlays on all clients, then stopped at `0x0201d5cc` with a null message
entry table. Download Play skips BOOT's message-bank initialization; the current
fix loads that bank on the native course worker in the persistent default heap.
The follow-up in `/workspace/runtime/story-text-retry/` creates four players on
every console in level 1, with WFS ready and no outstanding reads. The host
completes initialization while clients remain at the native loading barrier.
The current fix waits for the host's native loading acknowledgement before
initializing STAGE, so stale ENTRY barrier bits cannot release it prematurely.
Running the whole stage initializer on a worker caused rendering to access
incomplete resources and was removed. Keeping ROOT archive 0 mounted and the
native loading acknowledgement produced passing four-console movement tests.

The file-wait hook runs only on the main thread and suppresses recursive NET
servicing while a wait is already active. Background WFS/card threads retain
their normal reads. `COOP_FRAME_US` optionally changes diagnostic pacing
(default 16667); `COOP_MP_TIMEOUT_MS` configures the unmodified LocalMP transport's
wall-clock receive timeout (default 25). Smoke reports record both settings.

Progress stays in RAM. Restart before returning to ordinary adventure play:
the session save guard remains installed until reset. Persistent host-owned
saves, shared star/key decisions, cutscene/warp/death/disconnect policies, deterministic campaign actors and full campaign completion still need acceptance
tests and fixes. Story asset access and four independent inputs have passed the
castle-grounds checks.

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
