# Download Play handoff investigation

The mod remains unfinished. Current evidence establishes four-player gameplay
on an unmodified melonDS core, but also reproduces intermittent cold-start
failures. Campaign completion and physical hardware have not been verified.

The latest separate-MP-workspace bootstrap passed **5/5** four-console signed
menu cold starts: `/workspace/runtime/separate-mp-work-repeats/result.json`,
ROM SHA256 `a83287a9d8e222da930f35a6e2fafeed5b0325590c8c6e0dd449e4d345ab95f9`.
This is the first repeated-menu acceptance of the buffer correction, not five
campaign passes. Full payload/story repetitions are in
`/workspace/runtime/separate-mp-story-repeats/`; extended course/save acceptance
is in `/workspace/runtime/title-reader-course-save/`.

## Current four-console evidence

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
