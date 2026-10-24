# Download Play handoff investigation

The mod remains unfinished. Four-player gameplay works on an unmodified
melonDS core, but intermittent signed-loader startup and later-stage memory
failures remain under investigation. Campaign completion and physical hardware
remain unverified. Read the current regressions first; later sections preserve
historical checkpoints and failures rather than release acceptance.

## Latest active runs and driver corrections

- Closed-entry V2 is still opt-in. Five acknowledged menu cold boots pass.
  Full course-return repeat 1 passed with simultaneous selections [0,0,0];
  repeat 2 is testing actual delays [0,600,1800] and is still running. Do not
  describe the first run as staggered. Session 4131 owns the 3-run repeat.
- Old-default raw-resource course-return finished FAILED overall: 2/3 passed,
  one signed-menu failure. This confirms the original startup path remains
  unreliable; do not promote it or call the mod complete.
- The initial fast pause driver failed locally because it requested resume
  during the native menu's opening fade. It now observes fade 0x0209f300==0,
  debounce 0x0209f22c==0 and ready menu state 1/3 before sending START.
  `/workspace/runtime/healthy-thi-menu-ready-rerun/result.json` passes on the
  exact same local stage-24 image that failed the earlier driver.
- The direct four-player stage-24 run failed a character comparison. Read-only
  pause inspection at `/workspace/runtime/thi-character-inspection/characters.json`
  shows all replicas identical: a real Wario cap loss converted slot 2 to
  Yoshi. Sequential reads straddled the change. The driver now reads each
  console atomically and retries transient character changes briefly.
- The same party then PASSED healthy four-console stage 24 with the corrected
  driver: `/workspace/runtime/healthy-thi-wireless-continuation/diagnostic-stage.json`.
  Its attempt to continue into 25 FAILED after the party returned to Castle 1;
  do not count 25. There was no Crash flag or exception, and the prior stage-24
  snapshot has slot 2 at health 640. The party has been shut down cleanly.
- A fresh direct-25 run eliminates the prior stage's hazard/queued-death issue:
  `/workspace/runtime/closed-entry-stage25-matrix/`, session 15502, failure socket
  `/workspace/runtime/closed-entry-stage25-matrix.sock`. It runs 15 further
  transitions through 40. Cartridge `closed-entry-stage25-cycle-host.nds` SHA256
  `7c896c841ec4bf0ea316574e01283fbcbc2dc5412768e469628658e314992e08`.
- Remaining secret/castle/early stages 42..51,1..12 (21 transitions) are running
  at `/workspace/runtime/closed-entry-secret-castle-matrix/`, session 1302,
  failure socket `/workspace/runtime/closed-entry-secret-castle-matrix.sock`.
  Cartridge `closed-entry-secret-castle-cycle-host.nds` SHA256
  `b05072ff262af30c74fca819c18d5c8a9993c87ce47ac7ec13f5a09c3852ffdb`.
  Both new runs use frozen drivers and replace blind diagnostic 180-frame
  idle with a short initialization step followed by actual readiness checks.
- No agents, no core patches, no live emulated-memory writes. Do not interrupt
  pending RemoteEmulators RPCs. Source archive includes every untracked test.

## Current work: acknowledged entry closure and healthy stage checks

The mod is still experimental. Do not report a stable/complete release.
The normal memory-fix cartridge `raw-resource-host.nds` failed the first of
three new course-return cold starts before one signed menu. Run 2 passed the
full course-return check; run 3 is still running at
`/workspace/runtime/raw-resource-course-return-repeats/` (exec session 39667).
An opt-in bootstrap now closes associations with WM_SetEntry(0), publishes
closed ENTRY in the MB beacon through WM_SetGameInfo, and waits for both ARM7
acknowledgments before sending the firmware's remaining BOOT requests. It
keeps native BEACON_SENT handling from replacing the pending callback. New
parent recreation then restores ordinary entry acceptance. This tests the
race where a signed app associates while the old parent is being shut down.

`--close-entry-before-boot` requires restart-parent and a separate output;
it is NOT the default. Its first version only gated phase 1 and never ran,
because the control hook starts in phase 3. Three menu passes for that image
are NOT proof of entry closure: `/workspace/runtime/closed-entry-menu-repeats/`.
V2 gates the old parent in phase 1 or 3, before recreation; debug[31]=0x1005
proves both acknowledgments. The smoke check now requires that marker when
this option is enabled. V2 PASSED all five real four-console menu cold starts:
`/workspace/runtime/closed-entry-v2-menu-repeats/result.json`; immutable driver
`/workspace/runtime/closed-entry-v2-driver/`. Cartridge
`/workspace/runtime/closed-entry-host-v2.nds` SHA256
`5b98cafa0a72a96c95e91743cfa12a6a0f7b80cd21d0e004d66c472f3043644c`.
A default reproduction after adding the opt-in feature is byte-identical to
raw-resource (`/workspace/runtime/default-entry-experiment-control.nds`).

V2 full payload/story/course-return is running for 3 cold starts with staggered
signed-menu selection at `/workspace/runtime/closed-entry-course-return-repeats/`,
exec session 4131; frozen drivers `/workspace/runtime/closed-entry-campaign-driver/`.
Do not promote the option until full game handoff and repetitions pass.

The raw-resource HMC diagnostic passed stages 13–23 with all four controllers,
same-tick synchronization and shared pause. Final saved snapshots show full
health on every slot for stages 14–23. Its stage-24 claim is INVALIDATED:
slots 1 and 2 were dead in the saved passed snapshot. The old input check
accepted their death movement, and the party returned normally to Castle 1,
so the requested next stage 25 was never entered. Original reports remain;
`/workspace/runtime/raw-resource-hmc-matrix/stage-24-assessment.json` records
this correction. The retained party was shut down cleanly.

Movement checks now reject dead controllers and wait for decoded button edges.
Diagnostic checks use short 8/12-frame press/release intervals and native START
acknowledgments instead of prolonged idle waits, and reject any dead party
member before, during or after the check. V2 plus the memory fixes is rerunning
stage 24 through 40 (16 transitions) at
`/workspace/runtime/closed-entry-thi-matrix/`, exec session 28553. Failure socket
`/workspace/runtime/closed-entry-thi-matrix.sock`. Its cartridge is
`closed-entry-thi-cycle-host.nds`, SHA256
`5000459590827da6951bdcb238ef82bd17546e037b98ff94b0bcd536207a1c49`.
A one-console fast check of the new healthy/input guards is running at
`/workspace/runtime/healthy-thi-local-rerun/`; this is not wireless acceptance.
The separately prepared old-default stage 42 image is
`raw-resource-secret-castle-cycle-host.nds` SHA256
`c2bab21f8d63453680de095b7f4a946fd816f4fd88de01165b4c5db81ae44f08`.
For remaining stages, rebuild 42 with the acknowledged entry option if V2
passes; then cycle 21 transitions through stage 12, skipping unused 41.

## Latest continuation: plain-file map loader

HEAD is `b3fbc48df` on `co-op-multiplayer`. Source changes are uncommitted;
`.git` is read-only. The source recovery archive/patch are in `/workspace/runtime/`.

Both resource-high stage cycling and resource-owner direct HMC entry FAILED.
The former passed four-console stages 7–12, then failed entering 13. The latter
failed entering 13 directly. Both failed parties were shut down cleanly after
captures. The new failure stack in
`/workspace/runtime/resource-owner-hmc-matrix/story-entry-failed-0.dtcm`
shows `func_0201834c` requesting 17396 bytes for plain LoadFile's result while
its scratch copy is retained. The actual file is FAT 0x55b,
`data/stage/cave/cave_icg.bin`; SharedFilePtr's last-file 0x300 is stale here.
ROOT largest free block is 12372, GAME 64968. No particle/shared-resource
fallback was reached. Physical debug buttons reveal the native heap screen at
`/workspace/runtime/raw-load-crash-inspection/native-crash-0.png`.

The runtime now also hooks plain LoadFile's raw/compressed/archive buffer
allocation sites, scratch free, and the common Deallocate wrapper. The same
ownership table covers all fallback buffers. Four additional ARM tests execute
the failure, native CpuCopy8 with the exact captured map file bytes, negative
alignment, and repeated release. All 41 tests pass: image 7, coin 7, particle 7,
model/resource 12, plain map 4, relocation 2, controller RPC 2. Logs are
`/workspace/runtime/raw-resource-*-tests.log`.

Newest normal cartridge: `/workspace/runtime/raw-resource-host.nds`, SHA256
`d42d379d6567277f0e66efde39c49f6729d4f1986350e800efd26db701c9d38c`.
Newest HMC-cycle diagnostic: `/workspace/runtime/raw-resource-hmc-cycle-host.nds`,
SHA256 `fc40c65afcd4bf7131b3e719feca51acf996eb753d0ee29f4e084afc52c56142`.
Live HMC entry plus 27 further stage transitions is running at
`/workspace/runtime/raw-resource-hmc-matrix/`, exec session 87328; failure socket
`/workspace/runtime/raw-resource-hmc-matrix.sock`. Inspect its final report;
this build has not yet passed live HMC. It uses the new early native Crash flag
check, so allocator failures preserve RAM/DTCM promptly.

The older `/workspace/runtime/resource-high-guest-star/` is still running,
exec session 20353. Its actual guest coin 0→1 mirrored on all four consoles,
and its three successive guest jumps passed with decoded button edges.
Its first two star routes died to Chain Chomp; the third reached one remaining
post hit. Preserve every attempt and inspect the final result. New driver source
approaches from the south, away from the head's initial northern position,
acknowledges B/R release before the post loop, and runs while approaching.
Those last driver changes are not in this frozen running test.

### Live results of the plain-file fix

The new raw-resource diagnostic PASSED actual four-console HMC (13) entry,
all four independent controls, same-tick synchronization, and shared host
pause/resume. Its paused heap report proves particle fallback on every console,
one raw-map fallback on host, and twelve file fallbacks on each guest with
three live model owners. Subsequent stages 14 and 15 also passed. Every resource
owner was released on transition (live count zero on all peers), with GAME's
largest block recovering to 180108 bytes in stage 15. The 27-stage cycle is
still running; initial HMC success does not imply later stages passed.

`/workspace/runtime/resource-high-guest-star/result.json` PASSED. A real guest
coin pickup mirrored 0→1, three repeated guest jumps passed, guest console 1
(native slot 3) earned the Chain Chomp star on its third physical route attempt,
Save & Continue wrote both host banks, Castle returned with all four controls,
and a second Pause → Save & Quit persisted the star and ended all three guests.
First two deaths remain recorded; no savestate or live state injection occurred.
That party ended naturally. Its cartridge is the older resource-high image,
not the newest raw-resource image.

The newest normal raw-resource cartridge is undergoing three cold boots with
staggered signed-menu selections, real castle key/story/course entry, all four
controls, and course return at
`/workspace/runtime/raw-resource-course-return-repeats/` (exec session pending;
inspect process/log). This is real native firmware Download Play throughout.

## Current memory and bootstrap regressions

The mod is not complete or stable. Four-console stage cycling passes native
stages 7–12, then Hazy Maze Cave (13) runs out of ROOT heap. Captured native
allocator execution reproduces two failures: host particle pool 35840 bytes
versus largest free block 35496; guest shared-file raw model 6532 bytes versus
largest aligned block 6488. GAME retains enough spare space. The original
failures remain in `/workspace/runtime/four-player-stage-cycle-continuation/`
and `/workspace/runtime/particle-four-player-matrix/`.

Current source allocates the permanent runtime at ROOT's high end, discards
installation-only relocation records, and falls back to GAME for full-sized
particle pools and SharedFilePtr buffers when ROOT cannot fit. Exact alignment
and owning-heap frees are preserved; a bounded resource ownership map is used.
Seven particle and nine resource ARM unit checks execute native allocation,
free, and heap integrity checks on the private failure captures. These do not
establish a live HMC pass. The latest normal integrated candidate is
`/workspace/runtime/resource-high-host.nds`, SHA256
`b60d91d34a4d303ab32890447c083a1cb3f9959adc27e8a114c127c0509b19c7`.
Its four-console regression is running at
`/workspace/runtime/resource-high-four-player-matrix/` using the separate
`resource-high-stage-cycle-host.nds` image (stage 7 followed by 33 transitions).
The normal guest coin/star/save run is `/workspace/runtime/resource-high-guest-star/`.
Inspect result.json and logs; an active/running test is not a pass. Both retain
failed sessions at the corresponding `/workspace/runtime/<name>.sock` path.
Original failed particle-matrix party has been shut down cleanly.

Serial signed-client boot is an experimental builder option; default remains
restart-parent. Serial menu repeats passed 3/5, with two frontend progress
watchdog failures. A frame lead cap of 8 failed both further repeats (one
incomplete signed-menu download and one 900-second timeout). Do not promote
serial or present the earlier three cold starts as proof of reliability.
An original Download Station sender control passed both of two four-console
cold starts at `/workspace/runtime/native-station-probe-control/result.json`. This isolates the signed-loader transport from the
custom host sender, and verifies all menu bytes before testing probe launch.

Actual guest gold-coin pickups have passed with all four counters mirrored:
`/workspace/runtime/guest-coin-star-retained/shared-coin-pickup.json` and
`/workspace/runtime/guest-star-retained-continuation/shared-coin-pickup.json`.
Guest star navigation has not passed; failed/interrupted attempts remain
recorded. The input driver now waits for decoded button transitions and tests
three successive jumps before its star route. No live RAM writes are allowed.
The persistent controller server now survives disconnected clients; two RPC
unit tests pass. Do not interrupt old RPC clients during pending commands.

### Model-resize ownership correction

Further review found SharedFilePtr models call native `func_02017060` to
shrink their uploaded texture tail. That routine uses the current heap,
so a GAME fallback model would shrink through ROOT. A new isolated ARM
reproduction returns success but permanently loses GAME heap space after
release. The runtime now hooks this trim routine, retains the original
routine for untracked models, and resizes tracked models through their
allocating heap even after co-op policy ends. Resource ARM checks now number
12, including the native leak reproduction and the corrected trim/free cycle.

Newest normal image: `/workspace/runtime/resource-owner-host.nds`, SHA256
`c9f18361860a8f639a50df753ec0faec250cf967dcf3de063ee37da778822369`.
Newest diagnostic cycle: `/workspace/runtime/resource-owner-stage-cycle-host.nds`,
SHA256 `04a2d91fb92b63499310f63a7e4226a9256a66a72e23fb349057390788eba113`.
These supersede resource-high images in source correctness. A new live run
starts directly in HMC and cycles through stages 14–40 at
`/workspace/runtime/resource-owner-hmc-matrix/`, using
`resource-owner-hmc-cycle-host.nds` SHA256
`37122f82f74e59444148f620bd45c552b839e4e680684502517ea0c5a8038752`.
It has not yet passed; inspect its reports and log. The failed-session retention
socket is `/workspace/runtime/resource-owner-hmc-matrix.sock`.
Seven image, seven coin, seven particle, twelve resource, two relocation, and
two controller checks pass (37 total); logs are `/workspace/runtime/resource-owner-*-tests.log`. The resource-high live runs are still useful
for reproducing memory pressure; do not call them the final candidate.

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
