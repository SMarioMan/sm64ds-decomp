# Experimental four-player co-op

One cartridge host and three firmware-only guests can enter the main game
through DS Download Play, using HaxxStation for the signed first stage. The mod
uses the native wireless game protocol and filesystem. Standard melonDS 1.1
runs it; the automated test frontend does not modify the emulation core.

The latest candidate additionally fixes native flight entrances, asymmetric
loading checks, and actor initialization randomness. A four-console33–40 stage
cycle passes movement, shared pause/resume and matching-input-tick comparisons;
Applicable isolated checks pass, including native cannon launch arithmetic
with per-player echoed pitch. Campaign saving on this combined image,
remaining camera cases and boss victories remain open. The user reports
functional physical multiplayer on the pinned89505d400 image (SHA256
`aea94b7b...be4baedf`), with significant slowdown and occasional hitches that
also appear in melonDS. Optimizing full-speed gameplay across all levels is
a priority; newer-image physical acceptance and campaign completion remain open.
The current shadow fix restores native per-camera far-shadow suppression while
keeping AI synchronized. Four-console Bob-omb Battlefield entry now shows all
four Yoshi heads and no geometry overflow; broader rendering and performance
acceptance remain open. See [PERFORMANCE.md](PERFORMANCE.md) for measurements.

Optional performance experiments are documented in
[PERFORMANCE.md](PERFORMANCE.md): `--experimental-animation-cache` targets
repeated synchronous animation reads, and `--diagnostic-player-cost` measures
elapsed native work. `--experimental-collision-broadphase` evaluates an axis
rejection before native cylinder distance calculations. The separate
`--experimental-collision-plan` option instead uses validated ordered spatial
candidates, with bounded incremental refresh and native memory-pressure
fallback. These options require a separate `--output`; none is enabled in the
normal candidate. Optional cache/planner measurements now show predominantly
two-VBlank BoB gameplay, but remaining slow intervals, cold asset hitches and
all-level hardware performance remain unresolved.
`--experimental-lazy-animation-eviction` additionally keeps owned animation
bytes through validated native capacity queries; it requires the animation
cache. Native allocation pressure and growth still reclaim those bytes. This
option passes short four-console stage checks6–16 and return/save/quit, but
remaining hitches and hardware acceptance are open. It is disabled by default.
The common-archive mount-bypass experiment was withdrawn after a guest crash
on6→7 and a slower measured transition. Original archive loading is retained.
The animation cache now also indexes154 direct player animation files, including
the swimming poses responsible for repeated hitches; wireless retesting is ongoing.

The newer local spatial candidate experiment uses
`--experimental-animation-cache --experimental-collision-plan --output PATH`.
Its validated reusable version reduces measured steady BoB collision cost
from9.44–9.67ms to2.16–2.37ms and reaches predominantly2-VBlank input cadence.
Warm movement still has slow intervals. Callback validation and incremental
refresh are under live evaluation. It remains disabled by default; broad stage
and physical performance acceptance are still required.

A further opt-in `--experimental-persistent-animation-cache` (together with
`--experimental-animation-cache`) retains owned compressed animation bytes
across live stage transitions. ROOT pressure, capacity queries and buffer growth
still reclaim them; ended sessions flush them. This targets traced cold reads
after each stage change. Native checks pass, but the live comparison still has cold-read hitches because
ROOT queries and pressure reclaim those bytes. It is not a demonstrated hitch
fix and is not enabled in the normal build.

See [the worklist](WORKLIST.md) for current acceptance gaps and
[the emulator handoff](tests/EMULATOR-HANDOFF.md) for exact image hashes.

Verified four-console behavior includes separate controls, the original
green/red/blue/yellow Yoshi palettes, shared pause, the castle key, castle
interiors, Bob-omb Battlefield, course exit, guest death with party recovery,
and ordered Save & Quit. Startup now closes association entry, advertises the
closure, and waits for both native SDK acknowledgments before booting guests.
It then recreates the game parent and reopens entry. This is the default
`closed-restart-parent` strategy; it requires no human timing window.

That startup path passed five acknowledged four-console signed-menu cold boots
at `/workspace/runtime/closed-entry-v2-menu-repeats/result.json` and three full
story/course-return cold starts at
`/workspace/runtime/closed-entry-course-return-repeats/result.json`. The latter
used guest selection delays [0,0,0], [0,600,1800], and [1800,0,600] frames.
The legacy `restart-parent` strategy remains available as an experimental
control; its repeat failed overall (two passes, one startup failure).

A later fix gives the host ownership of the shared star/key return and
progression dialogs. Without it, several players could reopen one shared
result/dialog state machine and leave everyone without controls. The corrected
build passed real Chain Chomp star collection, Save & Continue, castle return,
and restored controls for all four players at
`/workspace/runtime/story-owner-first-star/result.json`. A second save through
Pause → Save & Quit passed at
`/workspace/runtime/story-owner-consecutive-save/result.json`; the star remained
in both host backup banks and the guests ended cleanly. That image has SHA256
`a8bad15c18c28e4a41d65ec3ef46443a1e5d3f96b133dea416134363437fa532`.

The current source additionally shares the gold coin total, so coins split
among players can trigger the native 100-coin star at the collecting player's
position. Seven isolated ARM unit checks cover the compiled hooks and retail
trigger. These unit checks do not establish a wireless 100-coin-star pass.
Red-coin and silver-star totals retain their native aggregate behavior. The
combined candidate has passed actual guest coin pickups with all four totals
mirrored; guest star collection, Save & Continue, Castle controls, and a consecutive
Save & Quit have also passed on the earlier resource-high cartridge. The newer allocator and archive changes still need their own guest-star/save
regression.

Four-console stage cycling exposed ROOT heap exhaustion entering Hazy Maze
Cave after stages 7–12. The current source preserves native resource sizes
and uses spare GAME heap for particle pools and shared/plain-file buffers when
ROOT cannot fit, tracking the owning heap for release. Ten particle and
twelve model/resource and four plain-file ARM checks reproduce the captured failures and verify fallback,
alignment, model resizing, and release. Live four-console HMC entry, controls, synchronization, and shared pause now
pass. Transitions into the next two stages also pass and release all tracked
resource owners. The wider later-stage cycle remains in progress.

Rainbow Ride exposed another memory peak: neither heap could hold the native
particle arena contiguously, and guests loaded an entire 43 KB NARC for one
member. The current source preserves native particle counts and allocates
whole manager arrays across owner-tracked segments when needed. Uncached NARC
members use direct ROM filesystem views. Six compiled ARM checks cover each
change, including the actual native particle manager/resource parser and every
member of all thirteen archives. All67 isolated checks pass. Physical filesystem
calls in the archive tests use a ROM adapter; actual wireless archive reads are
now proven for four direct reads on every console. That run then exposed a
fragmented particle allocation: the 17408-byte particle array and 10272-byte
resource table could not both fit contiguously. Reserving the entire arena
early moved the failure to skybox decompression. The current source reserves
only the resource table before stage loading, and protects the particle array
from smaller native requests during initialization. Compressed disk loads use
a bounded 512-byte input window instead of holding the entire compressed file
beside its output. Five ARM checks reproduce the native skybox failure, compare
the exact decoded model, and verify repeated release and policy delegation.
Actual wireless acceptance of this combination is in progress.

A real guest coin/star run passed pickup, the shared coin total, star collection
on its first physical route, Save & Continue, and castle return. Its following
Save & Quit FAILED: the host reached title while guests retained native radio
state 4. The current source continues the native teardown and allows only one
Reset request through its asynchronous Reset/Disable/End callback chain.
Native ARM callback tests and the new wireless quit run from the previously
earned star save pass. Do not treat the earlier complete save/quit pass as proof of
this newer combination or report a stable release.

The current normal candidate preserves the retail host ARM9, ARM7, secure
area, and secure-area metadata. Its parent loader lives in the lobby overlay.
This addresses an overwritten secure-area BIOS-wrapper region in the reported
white-screen cartridge. BIOS/firmware boot and four layout checks pass; the
older cartridge also boots under emulation. The user rebuilt commit89505d400
and confirmed the corrected candidate now boots on the New3DS/R4 SDHC2022/Wood
setup. Physical Download Play still needs testing. The report and remaining tasks are recorded in
[WORKLIST.md](WORKLIST.md).

Camera hooks now select the local player's zoom, recenter, field of view,
first-person mode, and return to normal view. Head look uses each player's
wirelessly echoed pitch so shared look-up triggers can remain deterministic.
Eleven compiled ARM camera checks pass. The current normal cartridge also passes
twelve physical-input zoom transitions across four consoles, including first-person
and normal return, with foreign cameras unchanged and synchronized player state.
Recenter, turn, and other personal movement camera modes still need wireless checks.
The newer source also gives sixteen native movement-camera setters local-player
guards and preserves flight/water arrivals that the guest result-pose hook had
been replacing with a grounded arrival. All94 applicable isolated checks pass
(four older prefix-loader checks skip). Twenty later native stage entries pass
on one console; wireless arrival and campaign checks remain in progress. See
the current [handoff](tests/EMULATOR-HANDOFF.md) for exact cartridge identities.

The default ROOT runtime now releases copied common-archive source data before
skybox loading and opens uncached members through ROM-verified offsets. The
four-console diagnostic passed Rainbow Ride (28), stages 29 and 30, including
movement, shared pause, and matching-input-tick synchronization. At stage 31,
controller movement returned all consoles to stage 1 without a native crash;
the remaining cycle is incomplete. The former low-RAM placement experiment
remains historical and is not the current candidate.

Separate diagnostic builds can enter a later native stage for compatibility
checks. Single-console tests have passed multiple course areas, underwater
movement, and all three Bowser arena entries; these do not prove boss wins or
wireless compatibility. The native table gives some courses several stage IDs.
Run the matrix with a fresh output directory and the activated test toolchain:

```bash
COOP_JIT=1 COOP_BATCH_INPUT=1 \
COOP_HARNESS_EXE=/workspace/sm64ds-decomp/build/coop/melon-test-jit-batched \
python mods/coop/tests/local_stage_matrix.py --fast \
  --output /workspace/runtime/new-stage-matrix
```

For a diagnostic Download Play build, explicitly pass both
`--diagnostic-start-level N` and a separate `--output` to
`build_download_play.py`. Diagnostic images must not be used as campaign
acceptance or release images.

**The mod is still experimental.** Full campaign completion, later bosses,
character unlocks, and physical wireless gameplay remain unverified. The checkpoint
reports above do not establish a complete campaign. Detailed earlier evidence
and failed experiments are preserved in [the emulator handoff](tests/EMULATOR-HANDOFF.md).

Only the supplied **Europe revision 0** cartridge is supported:
`ce5829aaa79f06c67140ed1f45cbca738b0a9d0180538c8c1498472d859db032`.
Other region/revision ROMs are deliberately rejected.

The standard multiplayer Yoshi palettes (green, red, blue, yellow) passed a
four-console check at `/workspace/runtime/native-colors-delayed-mp1/yoshi-colors.json`.
That run also launched all three Download Play clients with menu selections
delayed by 0, 10 and 30 seconds. It subsequently exposed a dialogue desync:
the host left the castle-key conversation while guests retained NoControl.
The current candidate wraps `Message::Update` itself with host input, including
calls outside scene behavior. `/workspace/runtime/native-clock-jit-default/result.json`
passed the key conversation, regained control on every console, and entered the
castle with four controllers and the original Yoshi palettes. It used unmodified
melonDS 1.1 with its standard JIT and 25 ms LocalMP timeout. Menu selections
were delayed by 30, 0 and 10 seconds. Its later castle-route failure was also
reproduced locally; the controller bot now aims through the center of the door
and shortens its final D-pad bursts. The corrected local route passes at
`/workspace/runtime/centered-castle-route/result.json`.
The identical multiplayer ROM failed a cold-start repeat at signed-loader
discovery: `/workspace/runtime/native-clock-jit-repeat/result.json`. Neither
that dialogue pass nor the local route proves reliable startup or a completed
campaign.

## Build and inspect

For the New3DS/R4 white-screen report, use the exact command and expected hash
in [BOOT-RETEST.md](BOOT-RETEST.md).

The integrated build takes the personal EU revision-0 game and USA Download
Station Volume 1 dumps and creates the host cartridge plus its matching
Download Play payload in one command. It uses host adventure file A by default;
choose `--save-slot B` or `--save-slot C` for another file. The mod remains under
campaign acceptance testing.

```bash
source /workspace/setup/activate.sh
python mods/coop/build_download_play.py /workspace/inputs/sm64ds-eu.nds \
  --station /workspace/inputs/download-station.nds --save-slot A
```

The default requires four systems: one host and three Download Play guests.
For three systems total, add `--clients 2`; for two systems add `--clients 1`.
The host waits for the configured number of guests. Changing this option
changes the output hash, so retain the adjacent build report with test results.

The output is `build/coop/bootstrap/sm64ds-haxxstation-game-handoff.nds`.

The current default slot-A/four-console build has SHA-256
`35d8be5d8a49681d37c9e05f3b12b991bb6ffff96e165f05223ba46c6d25adc3`.
It includes the verified Bob-omb Battlefield shadow/head rendering fix.
Other save slots and guest counts produce different hashes.
Its adjacent JSON records input hashes, client overlay authentication and
wireless parameters. The adjacent report identifies the exact build. The older regression image
`0e78e2b0bf80e29a02d8f904b45b44955ec65f57cbf6a4dd44a1a80b20437c64`
predates the star-return fix and must not be treated as a release candidate.
The lower-level commands below are useful for individual diagnostics; the
base `build.py` image by itself does not supply the HaxxStation handoff.

```bash
cd /workspace/sm64ds-decomp
source /workspace/setup/activate.sh
python mods/coop/build.py /workspace/inputs/sm64ds-eu.nds --baseline
python mods/coop/build.py /workspace/inputs/sm64ds-eu.nds
python mods/coop/tests/test_image.py
# Optional compiled-ARM coin checks (test dependency only):
# python -m pip install -r mods/coop/tests/requirements-arm.txt
python mods/coop/tests/test_game_counters.py
python mods/coop/tests/test_relocatable.py
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
runtime module; capacity, used-size and header CRC are updated. Six structural
tests check those limits, hook destinations, zeroed module state, the original
original-instruction trampolines and the camera-read wrapper's register
preservation. Gameplay is checked separately in melonDS.

## Why the base image fails stock Download Play

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
  --clients 3 --handoff --channel 1 --beacon-period 100 \
  --output build/coop/bootstrap/sm64ds-haxxstation-game-handoff.nds
COOP_MAX_FRAME_LEAD=0 python mods/coop/bootstrap/smoke.py \
  --parent native --story --shared-menus --course-return --clients 3 --menu-frames 7200 \
  --image build/coop/bootstrap/sm64ds-haxxstation-game-handoff.nds \
  --output /workspace/runtime/native-story-acceptance
# Omit --course-return for the shorter grounds/pause check.
```

These are the experimental parameters used for the extended route. Signed
loader discovery still fails on some boots. This image's files
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
supplied native BIOS/firmware and distinct MACs. The frontend supports the
interpreter and standard JIT; each acceptance report records which was used.
Cartridge saves stay in RAM unless a test explicitly sets `COOP_SAVE_DIR` to a
private backup directory; firmware writes are disabled. It does not simulate a client connection or replace the
wireless protocol. The linked core is GPL-3.0-or-later; upstream source and
license are retained in `/workspace/references/melonds`.
The command driver is a custom headless frontend. These results do not yet
establish equivalent reliability in the standard desktop application or on
physical DS systems; the ROM does not contain an emulator-specific protocol.

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

The historical direct-Download-Play replay of the base image failed as expected
on all three clients at
`0x02014104`/`0x020140fc`, before a story stage. Its complete transcript and all
four fatal-state screens are in `/workspace/runtime/coop-automated-mod-final/`.
That direct-boot path is an acceptance failure; the integrated HaxxStation
path is tested separately. The current experimental ROM SHA-256 is recorded by each build in `build/coop/build.json`.

| Check | Observed result |
| --- | --- |
| Existing profile/pin/fingerprint tests | 40 passed |
| New image-integrity/trampoline tests | 6 passed |
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
acceptance. A follow-up isolates actor random draws using the shared NET frame
and stage-relative actor identity. An earlier checkpoint then reproduced
position divergence after Lakitu, before rabbit pursuit, at
`/workspace/runtime/actor-random-game/`. The native talk state waits for its
local camera's transition to complete; the current follow-up broadcasts the
host's completion bit in unused NET user byte 5 and replaces the two player
talk/event reads with that echoed status. Local movement and six structural
checks pass. Four-console locked-door/Lakitu interaction and castle-key
collection now pass at `/workspace/runtime/shared-camera-game/` and
`/workspace/runtime/end-mp-game/`. Those runs did not pass interior acceptance.
The first interior crash came from native entrance loading: entrance 17 in a
19-record table was consumed as four consecutive player records. The current
adapter preserves nearby compatible four-player spawn groups, and otherwise
copies the selected arrival point into four bounded records. It restores the
original persistent entrance table after the native loader returns.

`/workspace/runtime/entrance-mp-restart-confirmed/` reached four interior player
objects with shared progress, but its initial entry test accepted a loading
fade too early. The current check waits for native scene initialization and
entrance animations, then requires movement from every controller. Independent
snapshots require exact horizontal positions and allow 1/16 world unit in Y
for native slope settling between VBlanks. The stricter run at
`/workspace/runtime/entrance-active-route2/` reached visible interior gameplay
and host movement. Its next serial position read caught a 12-unit vertical
collision adjustment; the subsequent diagnostic dumps show identical positions
on all four consoles. The check now retries the same strict comparison for up
to three additional 60-frame intervals before reporting divergence.

`--first-course` extends the smoke route through the castle's zero-star door
and Bob-omb Battlefield painting, then requires active gameplay and independent
controller movement in course 6. The single-console replay passed at
`/workspace/runtime/local-first-course-route1/result.json`; this is not wireless
acceptance. The four-console run at `/workspace/runtime/first-course-route1/`
passed all interior controls, then failed navigation to the painting. Later
replays identified the 200-unit west landing's vertical side as the obstacle.
The route now approaches its northwest-facing collision ramp from the lobby
and uses actual stylus input for the narrow doorway alignment. Standard-mode
drags must exceed the player's ten-pixel movement threshold, in addition to
the input handler's smaller dead zone. The subsequent shared-visibility build
passed wireless first-course movement and the return trip listed above.

The revised ramp route passed a single-console fast replay at
`/workspace/runtime/local-stairs-first-course/result.json`, including active
Bob-omb Battlefield movement. `local_campaign.py --fast` explicitly reports
that wall-clock pacing is disabled and is never wireless acceptance. Local
replays now also write a failed result with the completed checks if they abort.
`--course-return` implies `--first-course`, selects the host's actual Exit
Course pause-menu row, and requires active castle gameplay and independent
movement after the return. The local fast replay passed at
`/workspace/runtime/local-course-return/result.json`; the later four-console
return trip passed at `/workspace/runtime/shared-visibility-course-return/`.
The return check retains a paused course checkpoint and compares Goomba
positions, angles, states, and simulation timers, keyed by actor type and home
position. Heap pointers and rendering state are excluded. The parser found
15 Goombas in the local checkpoint and matched all 15 across the four-console
shared-visibility replay. The readable records are saved as `*-enemies.json`.

The four-console ramp replay at `/workspace/runtime/stairs-first-course/`
passed the key and all interior controls, climbed the landing, and reached the
painting. It exposed a real loading failure: the host entered the next STAGE
while all three guests remained in StarSelect initialization. Read-only RAM
and DTCM checkpoints (`star-select-stall-*`) show every guest suspended in
`myFS_ReadFile` after a short read from the scene base's `Initialise3dGraphics`
path; the host eventually reported native session error 6. The replay was
interrupted after those checkpoints, and its failed report is retained.
The follow-up applies the native loading advertisement/acknowledgement and
completion barrier to StarSelect, starting before base graphics initialization.
File waits keep NET active for that entire initialization, and menu behavior
waits for all replicas. The builder verifies the replaced retail setup and
completion wrappers. Its local course-and-return replay passed at
`/workspace/runtime/local-menu-barrier/result.json`. Its first wireless retry
reached only one signed menu, before gameplay; the next transition failure is
described below.

That startup failure recorded a 1,512-frame spread between the fastest and
slowest consoles and a native LocalMP packet FIFO overflow. The frontend's
optional `COOP_MAX_FRAME_LEAD` setting limits how far a console can advance
ahead of another running console, while retaining the normal frame period.
It leaves several frames of slack to avoid a per-frame barrier's wireless
deadlock. The default remains 0 (unlimited); smoke reports record the setting.
This is an emulator pacing experiment, not a packet or core modification.
With a limit of 8, one run reached all signed menus and native story gameplay;
`/workspace/runtime/frame-lead8-repeat-menu/result.json` failed at two menus.
Its final console-frame spread was only seven frames, so frame drift alone
does not explain the reconnect failure. Keep this experiment opt-in.
The one-frame limit experiment at `/workspace/runtime/frame-lead1-loader/`
advanced only a few frames per second during firmware transfer and was
interrupted after seven minutes, before signed-menu acceptance.

The StarSelect candidate's four-console run at
`/workspace/runtime/menu-barrier-frame-lead8/` passed the key, interior controls,
and painting route, then failed with native session error 6. Its checkpoints
show a later failure than the preceding build: the guests had queued scene 3
(STAGE), were loading its overlay, and had not reached scene initialization;
the host was already advertising STAGE loading. SDK overlay reads call the
shared reader at `0x0205d688` directly, bypassing `FS_ReadFile`. The current
candidate hooks that shared reader, retains asynchronous/worker-thread calls,
and pumps NET during synchronous main-thread reads only while a scene is
queued or its initialization is running. A reentrancy guard keeps nested
filesystem callbacks on their native path. Normal scene behavior is not run
inside those waits. Its first retry at
`/workspace/runtime/overlay-read-course-return/` stopped at loader discovery;
the later shared-visibility build passed the complete tested route above.
The local replay passed with first-course entry, 15-Goomba checkpoint parsing,
and course return at `/workspace/runtime/local-overlay-read/result.json`.
Its first four-console retry remained at signed-loader discovery before any
gameplay, so it does not establish wireless correctness of the new reader.
`build_host.py --beacon-period 50` is a separate opt-in discovery experiment:
the native parent's interval is 200..219 802.11 time units. The override is
reported as `fixedBeaconPeriodTu`; no client image or signature is modified.
The 50-unit retry remained at signed-loader discovery. A separate candidate
uses channel 1 and a fixed 203-unit interval, matching several earlier passing
boot checkpoints; its first run reached all menus and payload transfer at
`/workspace/runtime/beacon203-course-return/`. These parameters remain opt-in
and do not establish hardware or repeated startup reliability. The identical
repeat at `/workspace/runtime/beacon203-repeat-menu/result.json` failed at two
signed menus; later full-route passes do not erase that startup failure.

An optional `build_host.py --rearm-mp-after-boot` experiment ends MP after the
firmware clients have departed, retains the parent BSS/channel/TGID, and
restarts MP when a signed client actually associates. It requires an empty WM
child bitmap before stopping MP, retired
native MB child states, no signed-loader requests, and at least one queued
BOOT command for each child. The actual departure and empty WM child bitmap
gate the transition; queue acceptance alone does not establish delivery.
Earlier versions reached game startup and the castle key
with three guests; repeated boot reliability remains unverified. Stalled-core
diagnostics capture only peers whose core mutex can be acquired safely.
`/workspace/runtime/interior-controls-recheck/` stalled during firmware handoff
even after the optional MP restart executed, so that experiment does not resolve
the intermittent startup failure.
The current candidate tracks BOOT requests from bootstrap installation,
including native requests before the scene tick changes phase. A later protocol
review found that stopping on the type-11 acknowledgement was itself a defect:
the child needs a second BOOT request after entering BOOTREQ_ACCEPTED. That
second request sets `boot_end_flag` and begins the graceful MB shutdown before
executing the downloaded image. Stopping early made success depend on an extra
request already being queued. The sender now preserves native BOOT retries
until the actual WM disconnection, without an attempt limit or an input-timing
requirement. See the reconstructed
[child state machine](https://github.com/ntrtwl/NitroSDK/blob/main/libraries/mb/src/mb_child.c#L373).
Native control serialization is preserved; only
the signed station's idle heartbeat is specialized. A reconnect starts a new
state-2 association, and actual WM connection events reset the AID's application
transfer generation. Stale send callbacks cannot advance a replacement transfer.
The no-restart candidate reached four-console gameplay, including the dialogue
fix, at `/workspace/runtime/native-clock-jit-default/result.json`. A cold repeat
failed at one signed menu. Removing the test frontend's optional frame-lead cap
produced one three-menu pass and another one-menu failure in
`/workspace/runtime/native-clock-unbounded{,-repeat}/`; the cap alone does not
explain the failure. An acknowledged WM_Disconnect experiment sent real parent
deauthentication frames but stalled firmware; that experiment was removed.
A separate diagnostic of the SDK's once-per-frame MP clock stalled all three
guests and was removed. Neither unsuccessful experiment is a startup fix.
The two-phase BOOT correction is under cold-start and wireless-save validation
at `/workspace/runtime/two-phase-boot-first/` and
`/workspace/runtime/two-phase-boot-repeats/`. `tests/repeat_boot.py` preserves
every result and fails the aggregate if any cold start fails. Its story/course/
save modes also vary real menu-selection delays; menu-only runs establish only
signed-loader discovery, not payload or campaign acceptance.
That correction alone passed 2/5 cold starts. A read-only client trace then
showed failed signed loaders completing an unwanted second fake MB download
and BOOT, while successful menus remained at header-accepted state 7. Returning
associations now retain their station role even when their callback precedes
the scene's phase transition, and do not progress through legacy image/BOOT.
The decisive buffer diagnosis was that `WM_WORK->sendBuf` equalled the MB
message buffer `data_020a9db8`; raw frames showed an MB command containing the
same first bytes as the concurrent NI menu chunk. The bootstrap allocates a
separate aligned 1 KB MP workspace before WM starts and frees it only after
the native MB parent has stopped. The five-menu repeat above passes with this
change; earlier failed candidates remain recorded.

Two callback wrappers also exposed an ABS32 relocation omission for compiler
tail-call veneers targeting appended trampolines. The relocation builder now
recovers those object relocation records even when absolute linker definitions
leave no record in the final ELF. `tests/test_relocatable.py` compiles real
tail and non-tail calls with the pinned compiler to check both cases. This
corrects a concrete callback regression; a corrected four-console retry at
`/workspace/runtime/relocated-callbacks-delayed/result.json` still failed after
only one signed menu, so startup remains unfinished.
Subsequent all-association BOOT retries at
`/workspace/runtime/association-boot-retry/result.json` booted the signed
applications but failed rediscovery. Waiting for a new association before
restarting MP also failed at initial download in
`/workspace/runtime/connected-mp/result.json`. The latest candidate additionally
requires all three current native child states to be header-ready (14) before
asserting START, instead of latching it from a previous frame's roster count.
No latest-candidate startup pass is claimed.
The current comparison and wireless-state evidence are summarized in
[`tests/EMULATOR-HANDOFF.md`](tests/EMULATOR-HANDOFF.md).
The payload-completion barrier candidate failed before radio initialization
completed at `/workspace/runtime/complete-body-barrier/result.json`. Its saved
exception context subsequently identified a null wireless-work read in the
mod's transfer pump. The pump now waits for an initialized, started MP session
before accessing the work buffer. `tests/bootstrap_idle.py` reproduces the old
exception and passes initialization plus 600 idle frames on the guarded ROM at
`/workspace/runtime/idle-initialized-after/result.json`. Four-console handoff
acceptance is still pending. `dumpwifi` serializes
the unmodified core's wireless state for diagnosis and never loads a state.

Read-only native debugger stacks at
`/workspace/runtime/ack-boot-native-stack-symbols.log` locate the stalled guests
in `LocalMP::RecvPacketGeneric`, called by `Wifi::USTimer`. The pinned core
polls every eight emulated microseconds after a missing host frame; a 25 ms
wall-clock wait at each poll can delay one emulated frame by roughly 52 seconds.
The smoke frontend uses `COOP_BOOT_MP_TIMEOUT_MS` (default 25) during boot,
then restores `COOP_MP_TIMEOUT_MS` (default 25) after native party/WFS readiness
and before story entry. The `mptimeout` command locks every core between frames
before updating the native LocalMP setting. Reports record both settings and
whether the gameplay timeout was applied. No core code or packets are changed.
Zero-timeout boot polling kept frames advancing but failed the loader menu;
1 ms polling alone also failed that reconnect. With the revised optional MP
restart, `/workspace/runtime/departed-rearm-first-course/` reached all three
signed menus and unsigned payload transfer, then passed the key and all four
interior controller checks before failing navigation to the first painting.
The signed loader now serves menu requests independently; it still holds
executable data until every guest has selected the game and acknowledged its
length. Execution terminators are additionally held until every guest's entire
payload body has completed, so an uneven transfer cannot boot an early guest
into the game's connection deadline while another guest is still downloading.
Transfer readiness is checked with interrupts disabled alongside queueing.
This barrier executed all three payloads together in the latest four-console
dialogue/interior pass, including staggered menu selections. Repeated startup
reliability remains unresolved.
A fixed-channel option (`--channel 1`, `7`, or `13`) preserves that
channel across firmware and loader handoff. Channel 1 passed a full boot and
interior replay, but a repeat reached only two signed menus. Neither this
option nor the MP restart establishes reliable startup yet.
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

Progress stays in RAM by default. `build.py --save-slot A` (also B or C) enables
an experimental host-owned adventure file. The host loads that file and sends
its 68-byte adventure block through acknowledged NET pages before the stage
loading barrier; guests never write their own cartridge backup. Four-console
testing caught an earlier deadlock: that native barrier stops MP data sharing,
so it cannot enclose the page/result exchange. The current save call waits for
guest readiness while NET runs, publishes the host result with an alternating
transaction tag, and enters the barrier only after each replica consumes that
result. A failed initial
cart read leaves the session in RAM and disables writes. Four-console fresh-key
saving and orderly quit pass at
`/workspace/runtime/ordered-quit-new-progress/result.json`. Broader campaign and
repeated-save acceptance remain in progress, so saving is still opt-in.

The controller-driven single-console persistence test passed at
`/workspace/runtime/host-save-title-guard-test/result.json`: Save and Quit wrote
the earned castle key, a fresh launch loaded it, the other adventure slots
remained unchanged, and the title scene cleared the co-op save policy.
It used ROM SHA256
`7ba04c37cade43072b8f8337035aa5dca946259c53122a0db733c8d4b5640e9a`.
The revised packet-clock ordering also passes the same local save, title,
fresh-launch reload and unchanged-other-slots test at
`/workspace/runtime/save-clock-local/result.json`, ROM SHA256
`ad5b8a07afdd220c401775c12f6a425448f2dfff57e4965491b10f714c4deae7`.
These are local persistence checks, not wireless acceptance. To repeat one,
build with `--save-slot A`, then run:

```bash
python mods/coop/tests/host_save.py \
  --image build/coop/sm64ds-coop-experimental.nds --slot A \
  --output /workspace/runtime/fresh-host-save-check
```

The test writes only a new private backup directory and refuses to replace an
existing test save. Firmware writes remain disabled in the frontend.
`bootstrap/smoke.py --story --host-save` adds a real wireless host Save/quit
check; it requires a host image built with an explicit save slot. It verifies
host-file sharing, earns the key through input, inspects the resulting cartridge
backup and unchanged other slots, requires the host's title menu to finish
initializing, and checks that wireless has stopped on the host and every guest.
Cartridge-free guests display the session-ended screen and turn their DS off.
The default RAM-only candidate also passed the local key, castle, first-course
and course-return route at `/workspace/runtime/local-abs32-dialogue/result.json`
(ROM `f267b373722db88d2802b5a1cb99f7fbc618aac8e336f142d590fe15897eee36`).

The host-health death checkpoint now passes with all four controllers after
recovery, although that run's later save-driver check failed by choosing the
quit-without-saving button. Star progression, further cutscenes/warps, repeated
saves, additional death cases and full campaign completion still need broader
acceptance. See `tests/EMULATOR-HANDOFF.md` for current evidence and failures.

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

The current source adds numbered player1–4 mini-map markers using native story
HUD assets. The local head and direction arrow remain native. Four-console
castle/BoB sprite submissions, motion and shared pause pass; broader map and
character/color matching coverage remains on the worklist.

`--experimental-painting-math` additionally reuses exact continuous-wave painting
coefficients. Native ARM arithmetic tests pass, including signed inputs and
parameter/timer changes; live performance acceptance is pending. It remains
opt-in. It does not reduce mesh detail, wave updates, actor simulation or content.

`--experimental-painting-normals` requires `--experimental-painting-math` and
also remains opt-in. It computes the same regular painting mesh normals using
native normalization, then keeps native border flattening. Seven complete-mesh
ARM comparisons and the247-test suite pass; live timing remains pending.

`--experimental-painting-visibility` additionally requires the normals option.
It avoids a continuous painting's private mesh work only while the native
renderer rejects it; native interaction, sliding and wave timing continue.
Visible vertex identity and shared state pass nine ARM checks; live timing is
pending. It remains opt-in with the other painting experiments.
