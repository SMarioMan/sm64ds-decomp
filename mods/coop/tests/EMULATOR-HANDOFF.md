# Download Play handoff investigation

The mod remains unfinished. Current evidence establishes four-player gameplay
on an unmodified melonDS core. Earlier bootstrap versions reproduced
intermittent cold-start failures; the current cartridge passes three staggered
story cold starts. Campaign completion and physical hardware remain unverified.

The latest separate-MP-workspace bootstrap passed **5/5** four-console signed
menu cold starts: `/workspace/runtime/separate-mp-work-repeats/result.json`,
ROM SHA256 `a83287a9d8e222da930f35a6e2fafeed5b0325590c8c6e0dd449e4d345ab95f9`.
This is the first repeated-menu acceptance of the buffer correction, not five
campaign passes. Full payload/story repetitions are in
`/workspace/runtime/separate-mp-story-repeats/`; extended course/save acceptance
is in `/workspace/runtime/title-reader-course-save/`.

## Star-return ownership and shared coins: latest continuation

The old `0e78e2b0...` image really earned and saved the Chain Chomp star in
`/workspace/runtime/persistent-first-star/`, but failed to restore controls
on Castle return. Keep that failure report: multiple native Player arrival
and tutorial routines were competing over one shared level-clear/dialog state.
Player 0/1 were in Talk and 2/3 in LevelEnter, with identical state on peers.

Runtime hooks now make slot 0 the owner of star/course progression tutorials.
On star/key return, other slots use the normal grounded arrival, retain native
full healing, and wait for the owner's result/dialog to finish. The overlay-2
hooks are applied in RAM after loading; its authenticated disk image stays
intact. The relocatable runtime's builder bound is now 16 KiB, within the
loader's existing 64 KiB limit; ROOT allocates its actual size dynamically.

`/workspace/runtime/story-owner-host.nds`, SHA256
`a8bad15c18c28e4a41d65ec3ef46443a1e5d3f96b133dea416134363437fa532`,
passed the actual four-console star route on its first attempt:
`/workspace/runtime/story-owner-first-star/result.json`. The course bitmap
changed from zero to `80 00…`; Save & Continue persisted it in both host backup
banks, Castle return completed, and all four controllers moved again.
`/workspace/runtime/story-owner-consecutive-save/result.json` then passed a
second save through Pause → Save & Quit with that same live party, retaining
the star in both banks, preserving other files, returning the host to Title,
and cleanly ending all three guests. The persistent server was shut down.

The current source also repairs gold-coin accounting: retail NumCoins sums
individual slots, but its hundred-coin helper checks only the collector's
slot. CoopGiveCoins mirrors a canonical team total, then calls the real helper
with the actual collector; CoopNumCoins exposes the total once. Scene cleanup
propagates the native tally reset. Red/silver aggregation remains unchanged.
Seven Unicorn ARM unit tests execute the compiled hooks and the original
retail counter/trigger routines, observing Actor::Spawn's allocation-failure
path. They prove split retail coins fail to spawn, shared guest coin 100
requests star actor 0xb2 at the guest, clamps, reset, and retail fallbacks.
These are synthetic ARM unit fixtures, not wireless play evidence.

The combined image is `/workspace/runtime/shared-story-host.nds`, SHA256
`ef7a09ef25a3f6c809057996af246added0273b278325c48756e93a013df8587`.
Six structural image checks and all seven ARM coin checks pass. The initial
guest-star regression `/workspace/runtime/guest-star-combined/` FAILED: the
input route fell under the bridge, then its recovery's fixed movement check
failed. A new party at `/workspace/runtime/guest-star-party/` reproduced the
movement failure even with four tested directions. Read-only snapshots show
native tutorial event 7, step 3, message-active=1, on slot 0 on every console;
NoControl was zero. The first movement opens this native tutorial after the
stage-readiness check. The driver now finishes dialogs opened during input
checks and also waits for Player::mEventId to clear. No product patch was made
to dismiss dialogs automatically. Preserve both failed reports.

The new actual four-console run is `/workspace/runtime/guest-coin-star-regression/`,
with immutable drivers and a fresh copy of the controller-earned key-only save.
Guest console 2 first collects a real gold coin from the lower floor beneath
the bridge; guest console 1 then takes the deck route and collects the star.
The test requires mirrored nonzero team counters, two host saves, and restored
Castle controls on every console. Inspect result.json for its final status.
The new bridge bot walks short segments along the deck center and checks Y
against the real ramp height, rejecting a route below the deck immediately.

## Explicit diagnostic stage compatibility checks

`build.py --diagnostic-start-level N` changes only the compile-time initial
native LoadLevelNoReturn target. The integrated builder accepts the same flag
but requires a separate --output, so a diagnostic cannot replace the normal
host cartridge. Runtime metadata records diagnosticStartLevel; smoke.py then
runs stage compatibility checks and rejects campaign/save checkpoints. The
normal compile has no diagnostic override and still enters castle grounds.
These images do not prove progression through doors/paintings, earned stars,
boss victories, unlocks, or the ending.

`tests/local_stage_matrix.py` serializes builds, preserves each image/report and
actual controller-only emulator transcripts, and records every failed case.
The fast mode is an unpaced **single-console** diagnostic, never wireless
acceptance. `/workspace/runtime/later-course-local-matrix/` passed IDs
7,8,10..17,19,20. IDs 9 and 18 initially FAILED movement because directions
alone only turn an underwater Yoshi. The driver now presses B for the native
swimming stroke when Player::mIsUnderwater is set. Fresh reruns of 9 and 18
passed, along with Bowser arena IDs 36,38,40, at
`/workspace/runtime/water-boss-local-matrix/result.json`.

Native SUBLEVEL_LEVEL_TABLE confirms that IDs 6..28 cover the fifteen main
courses including their subareas; stage IDs are not course numbers. The
remaining castle, course, secret and character stages are running at
`/workspace/runtime/remaining-stage-local-matrix/`. The separately built
four-console Bowser diagnostic image is `/workspace/runtime/diagnostic-bowser-host.nds`,
SHA256 `4a228488b25fdf28c0d20072870d3ab0fbc2fc0702d553b136ca03292c5c1972`;
its wireless test has not run yet.

The live controller route now uses each console's outgoing camera angle,
carefully crosses the first bridge, and passes west of the mountain bulge on
the way to the post. Misses are typed ControllerRouteFailure and may retry via
real exits/death recovery only; networking, save, and synchronization failures
are never retried as navigation. Every attempt is retained. A read-only native
input-tick history compares 12 common completed ticks rather than mismatched
VBlank snapshots. COOP_BATCH_INPUT combines actual controller/touch events;
readv batches related observations without freezing or changing the cores.

## Earlier four-console evidence

`/workspace/runtime/native-clock-host.nds`, SHA256
`e761898ad4ce9218c0cae1c888b6c1a8b6c07100f1f0d5cd03df4004a1581171`,
passed these actual one-cartridge/three-firmware-client checks:

- signed Download Station menus and entire game payloads;
- native four-player party and mounted wireless filesystem;
- native green/red/blue/yellow Yoshi palettes;
- distinct controls and synchronized player positions;
- shared host pause/resume;
- controller-earned castle key, completed dialogue and restored controls;
- castle entry and all four interior controllers.

Report: `/workspace/runtime/native-clock-jit-default/result.json`. Menu choices
were staggered by 30, 0 and 10 seconds. The later castle navigation failure also
reproduced locally. The corrected controller route passes through Bob-omb
Battlefield and back at `/workspace/runtime/centered-castle-route/result.json`;
that local pass does not establish wireless course-return acceptance for this
candidate. The older all-green runtime has a separate four-console course-return
pass at `/workspace/runtime/shared-visibility-cache-course-return/result.json`.

The current image failed a cold-start repeat with only one signed menu:
`/workspace/runtime/native-clock-jit-repeat/result.json`. Removing the test
frontend's optional frame-lead cap produced one three-menu pass and another
one-menu failure at `/workspace/runtime/native-clock-unbounded{,-repeat}/`.
Neither a single pass nor the frame-lead setting establishes reliable startup.

## Emulator and control driver

The frontend links unmodified melonDS 1.1 core commit
`b86390e4428bf38ce4c1ce0e9ca446d6d25955e8`. It uses real firmware-only clients,
distinct MAC addresses, the original signed Download Station client, and native
LocalMP. Inputs are controller/touch events; RAM, registers and wireless captures
are read-only. No packets are injected and no captured state is loaded.

`COOP_ENABLE_JIT=ON` in `tests/build_harness.sh` builds the core's standard JIT;
`COOP_JIT=1` selects it in that frontend. The interpreter remains the default.
This is a test frontend, not a custom emulation-core fix required by the ROM.
The current dialogue pass used JIT, 25 ms native receive timeout, 16667 us/frame,
and an optional maximum frame lead of 8. Reports record those settings.

The old driver pressed A before firmware discovery and omitted stock SM64DS's
START touch. It now retries discovery only while the actual BIOS multiboot
marker, read through the `0x023ffc40` mirror, remains different from 2. It stops
retry inputs when each console boots its application. The corrected unmodified
SM64DS control passed four-console VS stage entry with the default 25 ms timeout:
`/workspace/runtime/stock-control-default-timeout/`. It still failed with the
shortened 1 ms timeout; 1 ms is not a reliability baseline.

A temporary native LAN comparison was discarded: upstream identifies peers by
IP, so multiple loopback clients are ambiguous. LAN support is not shipped in
this frontend. No core sources were changed for that experiment.

## Confirmed defects and fixes

The old channel-0 failure was a mod ARM9 data abort, not radio initialization.
The pointer at `0x0209cddc` leads to the native saved exception context, with PC
at offset `0x40`. PC `0x022c0a0c` was `Pump` dereferencing a null WM work pointer.
The pump now requires allocated, initialized, started MP state and no reset
before reading its child bitmap or queueing traffic. `bootstrap_idle.py`
reproduces the old exception and passes initialization plus 600 idle frames on
the guarded image. Reports:
`/workspace/runtime/idle-uninitialized-before/result.json` and
`/workspace/runtime/idle-initialized-after/result.json`.

BOOT accounting originally started after the first native BOOT could already
be queued. More significantly, the later policy that stopped on a type-11 reply
was wrong. In the reconstructed
[child state machine](https://github.com/ntrtwl/NitroSDK/blob/main/libraries/mb/src/mb_child.c#L373),
the first BOOT enters BOOTREQ_ACCEPTED, which sends type 11. Another BOOT is
then required to set `boot_end_flag` and begin MBi_CommEnd. Stopping on type 11
made success depend on another request having been queued before its callback.
The current sender keeps native BOOT active until the firmware's actual WM
disconnection. It preserves native control serialization, specializes only the
station heartbeat, and does not use a fixed attempt limit. Cold-start and save
validation are in `/workspace/runtime/two-phase-boot-first/` and
`/workspace/runtime/two-phase-boot-repeats/`.
A new firmware association clears old BOOT
accounting for its reused AID. Application transfers have their own association
generations so stale callbacks cannot advance a replacement transfer.

The two-phase correction alone passed only 2/5 cold starts in
`/workspace/runtime/two-phase-boot-repeats/result.json`. The read-only client
trace `/workspace/runtime/two-phase-client-states.jsonl` then caught a returning
signed loader advancing from fake-child state 7 (header accepted) through data,
BOOT acceptance and state 11 (boot ready). It shut down and returned to search.
Successful menu captures remain in state 7. This is a second legacy download
cycle, not proof that a timeout setting or emulator patch is needed.

The current candidate records post-firmware WM associations separately. It lets
those fake children receive/acknowledge their header, but refuses subsequent
legacy image/BOOT progression while they initialize their NI menu request.
BOOT remains enabled for the original firmware association until departure.
Cold-start and wireless-save validation of this correction are in
`/workspace/runtime/station-association-repeats/` and
`/workspace/runtime/station-association-save/`.

Role tracking alone did not resolve the failure. Read-only native pointers in
`/workspace/runtime/monotonic-station-repeats/run-1/signed-loader-0.ram` showed
that `WM_WORK->sendBuf` and `data_020a9db8` both pointed to `0x0234c920`.
The retail MB sender aliases its message source with the WM assembly output.
With NI packets in the same MP frame, raw traffic in
`/workspace/runtime/two-phase-boot.bin` showed a port-1 MB message containing
the same first six bytes as a concurrent port-14 menu chunk. A chunk number
could therefore become a legacy MB DATA or BOOT command.

The bootstrap now allocates a separate aligned 1 KB WM send workspace before
WM initialization. Native MB source records and NI source buffers retain their
own storage. It frees that workspace only after the old MB parent has stopped.
The five-menu repeat above passes with this correction, default 25 ms receive
timeout, standard JIT and no frame-lead cap. Earlier failures are retained.

Payload execution terminators wait for every complete body, keeping an early
client from entering the native game connection deadline while another guest
is still downloading. The current four-console pass exercised that barrier.

## Remaining diagnostic lead

Some failed captures show signed applications scanning with `IsMPClient` still
set. After a missing host frame, the pinned core polls LocalMP every eight
emulated microseconds. At 25 ms per poll, one frame can take roughly 52 seconds.
This is a concrete observation, not a proven explanation for every failure.
`dumpwifi` captures this state without changing it.

An optional MP-stop/restart experiment did not resolve startup and is excluded
from the current command example. Forcing native WM_Disconnect after BOOT ACK
sent real parent deauthentication frames but stalled firmware; it was removed.
A separate supported VBlank MP clock diagnostic stalled all three guests and
was removed. An opt-in MP restart gates on actual firmware departures and
requires a fresh association before restarting. Ending MP at the first BOOT
acknowledgement reached two menus twice with one guest but failed with three;
it did not establish correct completion of the firmware's two-phase handshake.

Four-console host-save testing found an actual ordering defect: the native
loading barrier stops MP data sharing, leaving the host on page 1 while every
guest waits for page 1. The current code exchanges the host file before the
barrier and exchanges save results before entering a final barrier. Alternating
result tags distinguish consecutive saves. Local cartridge persistence,
title cleanup and fresh-launch reload still pass at
`/workspace/runtime/save-clock-local/result.json`. The revised wireless path
and Save/quit remain under active test. Stars, deaths,
disconnect recovery, remaining campaign transitions and hardware still need
implementation or acceptance; do not label this a stable finished release.

The four-console test in `/workspace/runtime/station-association-save/` passed
host-file sharing, independent controls, pause, key dialogue and actually wrote
the earned key to host cartridge backup without changing other slots. Save/quit
then exposed a host exception at `0x0203c76c` in `Heap_t::Destroy`, trying to
destroy the VS-only root heap at `0x0211d9c0` after story overlays had overwritten
it. The runtime now destroys that auxiliary heap after ENTRY cleanup and before
loading the overlapping story overlays.

That change got all consoles to TITLE in `/workspace/runtime/retired-vs-heap-save/`,
but guests remained in TITLE initialization: clearing `coopEnabled` in TITLE's
BeforeInit disabled the NET-aware reader before their wireless file reads.
The current runtime retains that reader until TITLE AfterInit succeeds, then
clears the previous session's save policy. Local save/reload and initialized
TITLE checks pass at `/workspace/runtime/title-reader-local-save/result.json`.
The four-console reader-only replay at
`/workspace/runtime/title-reader-save/result.json` still failed: the host
finished TITLE while guests slept in the native NET loading loop. It did
persist the controller-earned key without changing the other adventure slots.
The current candidate adds TITLE to the native loading barrier and holds the
loading advertisement through child-object initialization. Its local save,
initialized TITLE and fresh-launch reload check passes at
`/workspace/runtime/title-barrier-local-save/result.json`; wireless validation
is still pending. Merely reaching scene ID 1 does not pass the quit check.

The separate-buffer story repeat in
`/workspace/runtime/separate-mp-story-repeats/result.json` passed two of three
cold starts. The third failed before signed-menu selection. Thus the five menu
passes alone do not establish reliable startup. A new opt-in
`--restart-station-parent` experiment shuts down and recreates the native MB
parent after all firmware associations have departed, preserving the original
TGID required by the downloaded game's later connection. It gates on protocol
state, without a fixed delay. Its five-menu repeat passes at
`/workspace/runtime/recreated-station-repeats/result.json` (ROM
`4825c7ca426bf95b7320525c42542b4ff33135efaa1f3ab7a149fcfb43865297`).
It remains experimental until full payload and campaign repetitions pass.
These runs use standard melonDS 1.1 JIT, 25 ms LocalMP timeout and no frame-lead
cap. No emulator core change is required.

Read-only bootstrap state in `recreated-station-repeats/restart-state.json`
confirms that the new parent recreation actually ran on every one of those
five starts; it was not merely an enabled but unexercised option.

The four-console replay in `/workspace/runtime/recreated-station-save-bridge/`
passed the key dialogue, file sharing, colors, controls, pause and the host
cartridge write. The added TITLE barrier still stalled. Saved launcher-thread
contexts now distinguish the waits: the host sleeps inside `CARDi_Request`
while rereading minigame backup data during the menu callback, and guests wait
on WFS resources. All four remain in TITLE initialization; no exception was
recorded. The current candidate runs main-thread TITLE backup reads using the
SDK's existing asynchronous card worker and pumps NET until completion,
preserving synchronous caller semantics and buffer lifetime. This is under
wireless test at `/workspace/runtime/async-backup-save/`.

`tests/course_death.py` adds a real-input enemy-death checkpoint, available as
`--course-death` in both the local campaign and Download Play smoke drivers.
It requires health to reach zero, return to initialized castle gameplay and
movement from every controller. Its single-console diagnostic passed at
`/workspace/runtime/local-course-death/result.json`; wireless death recovery
is not yet accepted. No health, position or scene writes are used.

The asynchronous-backup experiment also failed and has been removed. Its
capture at `/workspace/runtime/async-backup-quit-cpu/` finally caught the host
in IRQ mode (`CPSR 0x600000d2`), looping at `0x020601e4` in the card-lock
acquisition routine. The WFS ROM reader wanted lock `0x42` while the interrupted
backup reader held `0x43`. This blocked further interrupts; polling the backup
on another thread could not resolve that lock ordering.

The current quit protocol completes before TITLE resource initialization.
Every peer publishes readiness after its transition overlay reads; the host
commits and guests acknowledge over the ordinary synchronized input stream.
Once every acknowledgement is echoed, native mode 0 resets WM and shuts WFS
down. The host waits for native wireless state 0, clears the co-op policy and
returns to its ordinary one-player file menu. Cartridge-free guests use a
resident session-ended screen and power off, rather than entering a file menu
whose future resources require the departed host. No backup access overlaps
WFS reads and no fixed delay determines the shutdown.

That sequence passes the four-console existing-file diagnostic in
`/workspace/runtime/ordered-quit-fixture/result.json` and the fresh-key route
in `/workspace/runtime/ordered-quit-new-progress/result.json` (ROM
`429dd5f255769c4f19c488a44fcdc40bc323553ecc2de86e47d40221aed771d7`).
The latter earns the key using controllers, persists it on the host and leaves
the other adventure slots unchanged. Local fresh-launch reload passes at
`/workspace/runtime/ordered-quit-local-save/result.json`. The following
candidate replaces the retail failure wording for planned quits with a small
resident "SESSION ENDED" display and adds native-error handling for a lost
guest, including losses during synchronous WFS reads. Unexpected-disconnect
acceptance is running in `/workspace/runtime/session-end-disconnect/`.

Unexpected guest power-off now passes in
`/workspace/runtime/session-end-disconnect/result.json` (ROM
`f9be89e88fd95beac391e2f9a95782051d407b9ed484dbd595b1daa5fe539671`).
The frontend stops the selected console and removes its radio from LocalMP,
as when closing an emulator window; it does not inject game packets, RAM or
register changes into the remaining consoles. They all disable co-op, stop
file sharing and reach the resident error screen without exceptions.

The four-console death checkpoint in `/workspace/runtime/session-end-death-save/`
found a real HUD dependency. The host's player had zero health everywhere.
Its HUD meter reached zero on the host, which began reloading; each guest's
HUD still showed 8 for its own living player. Player 0 therefore remained in
`St_DeadHit_Main`, work state 2, on all guests while the host waited at its
loading barrier. The runtime now substitutes the current player actor's
health for this HUD-dependent simulation read and restores the local meter
after behavior. It also allows only one death transition per stage: native
`SetNextLevel` consumes the return entrance, so a second simultaneous death
must not overwrite the first destination. Game over uses the orderly session
shutdown before the host opens its local scene. Verification is running at
`/workspace/runtime/party-death-save/`.

The local controller-only Chain Chomp route now passes collection of its real
star, Save and Continue, cartridge persistence and restored castle control:
`/workspace/runtime/local-chain-star-v21/result.json`. The course star bitmap
changes from zero to `0x80` and matches the saved file afterward. This is a
single-console diagnostic, not wireless star acceptance. The private initial
fixture contains only the castle key earned in an earlier controller test.


## Restored environment and current regression cartridge

The workspace was restored with source checkpoint `7a3295380`; the two runs
interrupted by environment loss (`party-death-save-correct` and
`party-star-short-route`) had not completed and are not passing evidence.
The matching current cartridge is `/workspace/runtime/party-death-host.nds`,
SHA256 `0e78e2b0bf80e29a02d8f904b45b44955ec65f57cbf6a4dd44a1a80b20437c64`.
The one-command `mods/coop/build_download_play.py` reproduced that image from
the personal EU revision-0 game and USA Download Station Volume 1 dumps.
The canonical `build/coop/bootstrap/sm64ds-haxxstation-game-handoff.nds`
contains the same bytes. Both input hashes are recorded in its JSON.

Host power-off passes on this cartridge in
`/workspace/runtime/party-host-disconnect/result.json`. All three remaining
guests stop co-op and WFS and enter the native resident error screen without
exceptions. This complements the earlier guest power-off check.

The local controller-only star route also passes on the current runtime in
`/workspace/runtime/party-local-star-analog/result.json`: fresh key collection,
castle and first-course entry, real Chain Chomp star, Save and Continue,
matching star flags in both backup banks, and restored castle control.
The approach route now uses shorter bursts and intermediate points so the
camera turn does not send the bot into the eastern mountain wall. A route
failure is not automatically a game failure; preserve its screenshots.

`smoke.py --course-death --death-controller N` now supports an actual guest
controller, using that console's native player-slot mapping and synchronized
camera angle. No emulated position, health, register, scene or packet writes
are used. The death checkpoint records the actual controller and player slot
in `course-death.json`. `--use-key-fixture` explicitly records an existing key
fixture; it does not establish new key persistence.

Fresh four-console regressions after recovery are running in
`/workspace/runtime/restored-guest-death/` (guest death, recovery, Save and Quit),
`/workspace/runtime/restored-party-star/` (star, Save and Continue, Save and Quit),
and `/workspace/runtime/restored-story-repeats/` (three cold starts with differing
menu-selection delays). Consult their final JSON before treating them as passes.


The first restored star attempt failed `castle-input-1` on a 12-unit Y
mismatch, with exactly matching X/Z and adventure data:
`/workspace/runtime/restored-party-star/result.json`. Do not discard it.
The subsequent full RAM snapshots were taken at native input ticks 7764,
7766, 7768 and 7769. They cannot establish equality at the same simulation
time. The frontend now optionally retains read-only, frame-boundary player
positions/progress by native input tick (`COOP_FRAME_SAMPLES=1`, command
`partyhistory`). Workers keep running; the diagnostic neither changes the
core nor pauses one console while its peers await wireless replies.

With sampling enabled, campaign checks require 12 consecutive matching
completed input ticks across all consoles. Horizontal equality and the
existing 1/16-unit vertical tolerance are retained. Each check saves its
comparison in `*-same-tick.json`. The newest two ticks are excluded because
they can still receive actor updates. The diagnostic is enabled in
`/workspace/runtime/same-tick-party-star/` and
`/workspace/runtime/same-tick-guest-death/`; these runs use
`build/coop/melon-test-jit-samples` and the unchanged current cartridge.

The original guest-death route failed before enemy contact by walking off the
upper platform at `(1800,4900)`. The decoded retail KCL shows the western edge
there runs diagonally; the old `(1250,5000)` approach lay on that edge. The
route now crosses east at z=5500, then heads north along x=2000 in shorter
bursts. This is a controller-driver fix, not a change to collision geometry.


The current cartridge passed all three restored story cold starts:
`/workspace/runtime/restored-story-repeats/result.json`. Guest menu schedules
were [0,0,0], [0,600,1800], and [1800,0,600] frames. Every run reached all four
story controllers with green/red/blue/yellow Yoshis and passed shared host
pause/resume. Standard JIT, 25 ms LocalMP, 16667 us pacing, no frame-lead cap;
no emulator core changes. These are story-start regressions, not three full
campaign passes.

The matching-tick diagnostic passes all ten castle/first-course input
checkpoints so far in `same-tick-party-star`. The earlier height failure is
retained; the new run does not retroactively turn that old run into a pass.


`/workspace/runtime/same-tick-guest-death/result.json` now passes end to end on
the current cartridge. Controller 1 mapped to native player slot 3 and reached
actual zero health. All four consoles returned to initialized castle gameplay;
each controller moved again and matching-tick comparisons passed. Host file A
saved, other adventure slots remained unchanged, the host initialized title
with wireless off, and all guests reached planned-session marker 1 with radio
state 0. Both guest screens visibly render the independent "SESSION ENDED"
alphabet correctly (`/workspace/runtime/current-guest-session-ended.png`).
This run uses the previously earned key fixture, not a newly collected key.

The same-tick star run failed when its controller died before completing the
post, after passing castle/course and input checks. The fine-control loop made
many separately locked reads while the live game kept advancing. It now uses
optional batched read-only observations (`readv`) and combined key/stylus
controller events (`input`) in the test frontend. This is not a core change,
RAM write or protocol substitute. The new run is
`/workspace/runtime/batched-party-star/`, using `COOP_BATCH_INPUT=1` and
`build/coop/melon-test-jit-batched`. It logs actual native input ticks, health
and player states during the post sequence. Consult its result before claiming
wireless star acceptance.


Save-slot B and C local persistence regressions both pass, including newly
controller-earned key collection, Save and Quit, fresh-launch reload and
unchanged other adventure slots in both backup banks:
`/workspace/runtime/restored-slot-b-save/result.json` (runtime
`3962ddc231240ac28b96aa656f9cb5e8cd155601917d314dec8779319a8f55fa`) and
`/workspace/runtime/restored-slot-c-save/result.json` (runtime
`27b81c606c16ab566aba84862575d5ebd55ec366913268c755407fabfc1fa78a`).
These are single-console diagnostics, not wireless acceptance of slots B/C.
Six image-structure checks pass with the slot-C build. The base image/report
have been rebuilt for slot A afterward and byte-match the current runtime;
the canonical integrated cartridge still has SHA256 `0e78e2b0...437c64`.


## Persistent controller diagnostics

Repeated first-star attempts still fail in the automated approach; none is a
four-console star acceptance pass. A local first-star/save/return pass with the
batched post controller is in `batched-local-star-north/result.json`. Later
attempts are retained separately. The fast analog ramp passes the four-console
crossing, but long jumps near the mountain can still drift into its collision
wall. Navigation errors now have a distinct `ControllerRouteFailure` type.
Only those can be retried through real course exits or death recovery; network,
synchronization and save failures fail immediately. Attempts retain independent
folders and a `course-star-route-attempts.json` ledger. The painting-room/lobby
re-entry distinction has also been corrected in the controller helper.

`recoverable-party-star` passed a real four-console pause/exit before its
re-entry driver failed: all 14 remaining Goomba simulation states matched and
all four castle controllers recovered. Its failed re-entry targeted the room
directly from the lobby, hitting the wall. Do not turn that overall failed run
into a pass. Frozen driver sources and hashes for the following attempt are in
`/workspace/runtime/analog-approach-party-star/driver/`.

The driver now steers using local outgoing camera angle `0x020a1050`, which
`dCamera_c::Behavior` writes through `func_0203dafc`. The old echoed angle
`0x020a1164 + 36*slot` belongs to an earlier input tick; it is not the angle that
will accompany a newly supplied physical input. This is a controller diagnostic
fix, not a game/network patch. New local verification is in
`/workspace/runtime/outgoing-yaw-local-star/`.

`smoke.py --story --control-socket PATH` keeps the actual emulator session alive
for subsequent controller clients. `tests/session_control.py` exposes
`RemoteEmulators`, reusing the existing input/read helpers through a private
Unix socket. Clients leave the game paused with actual START input; no core
memory, register or packet substitution is introduced. A fresh four-console
session is starting in `/workspace/runtime/persistent-party/`, socket
`/workspace/runtime/persistent-party.sock`. Read `control-session.json` for
readiness before connecting. Its ordinary startup report remains running until
the controller session is explicitly shut down.
