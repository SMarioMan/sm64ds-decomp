# Download Play handoff investigation

The mod remains unfinished. Four-player gameplay works on an unmodified
melonDS core, with acknowledged startup now passing repeat tests. Later-stage memory
fixes are still undergoing live validation. The user reports functional physical
multiplayer with emulator parity on89505d400/aea94b7b, but significant slowdown
and occasional hitches, worse on hardware. Prioritize native performance across
all levels. The tested party size and campaign coverage were not specified;
newer-image physical acceptance and campaign completion remain open. Read the current regressions first; later sections preserve
historical checkpoints and failures rather than release acceptance.

## Active native-menu-readiness regression

- Latest pushed sourcefd9c67fb3 includes actual native touch initialization
  waits and its ARM proof. The normal ROM remains fbb2262d.
- CLOSED `acknowledged-course-return-normal/` plus continuation
  `native-input-readiness-regression/`: steady/warm movement and fresh guest2
  shared coin PASS. Acknowledged pause opens,15 Goomba states match. The exit
  touch was sent while native opening cooldown0209f300 was10; PS state3 ignores
  such touches. Later timeout shows all consoles healthy NET4, still paused in
  BoB, cooldown0. This establishes no successful course exit/reentry.
- New course-return driver waits for native PS state3, draw state3,
  zero opening cooldown/menu animation, then holds the fourth-row touch until
  native state leaves3. It acknowledges host touch release first. Two actual
  retail PS_Update ARM tests prove cooldown rejection and ready touch->action19;
  only presentation callbacks are replaced in those isolated tests.
- ACTIVE normal fbb party `native-menu-readiness-normal/`, exec96332, socket
  `native-menu-readiness-normal.sock`, full-profiles stock-core frontend.
- ACTIVE continuation `native-menu-readiness-regression/`, exec61114, waits for
  parent's normal castle/BoB route, then tests steady/warm movement, guest2 coin,
  acknowledged pause/menu Exit and native course reentry. Latest frozen sources
  include the native menu readiness waits. It closes on success and retains
  the physically paused party on failure for inspection; NEVER start another
  wireless party before closing this one.
- Prior waiting continuations were explicitly replaced before any controller
  connection, recorded in their result files. No live memory/packet writes or
  savestate restores are used. Full current isolated suite is running under
  `native-menu-readiness-all-tests.log` PASS:149 discovered,145 executed,4 obsolete
  prefix-only skips. The two new actual ARM menu tests pass.

## Current performance investigation

- Normal candidate remains fbb2262d below. Default rebuild
  `frame-clock-default-unchanged-host.nds` reproduces it byte-for-byte.
- Retail Adventure/file-A castle:299 intervals all exactly2 native VBlanks.
  Earlier VS-practice automation is invalid as an Adventure baseline.
- REJECTED timer experiment14ab0ad99/afa982ae: no useful matched BoB gain.
  BoB median/p95 remain3 VBlanks; cold-inclusive mean3.588 versus baseline3.577.
  Steady600-frame sample has202 intervals averaging~3.005, predominantly main
  phase4, which includes BOTH behavior and rendering. Do not label it a pure
  Behavior CPU profile. Optional runtime/builder/test code is removed; historical
  commit and frozen test sources retain the experiment.
- CLOSED experimental party `bob-wireless-frame-clock/`, image afa982ae.
  Normal startup, independent inputs, castle/BoB entry and warm locomotion PASS.
  Fresh600-frame steady BoB capture in `wireless-frame-clock-regression/`.
  Zoom initially falsely failed because slots0,1,3,2 were treated as console
  indexes; the first correction also missed two assertions. Corrected
  `wireless-frame-clock-camera-fixed/` PASSES all zoom/mixed controls and20
  shared pause cycles. Fresh guest3 coin FAILED: no pickup, totals remain0;
  the controller ended above the lower-floor coin atY347.7. Subsequent
  `coin-north-approach/` also FAILED navigation; no pickup acceptance. Native
  state0211013c resolves to St_Walk, not a confirmed ledge/hang state. The party
  was shut down cleanly afterward. Course exit/reentry checks did not execute.
- CLOSED NORMAL party `bob-native-process-profile/`, exec61040, socket
  `bob-native-process-profile.sock`, image fbb2262d. Frozen source snapshot,
  key-only fixture and stock core. The process-observer frontend records native
  process phase/current owner profile within main phase4. This initial build
  records IDs0..353 with stride354; BoB profile observations are supported.
  Current source/full-profiles binary supports the391-entry registry using
  high16 phase/low16 profile keys; Python also accepts the older stride format.
  Continuation `bob-native-process-steady/`, exec31506, PASSES600-frame steady
  BoB, warm movement on all four consoles and fresh guest2 shared coin. Course
  return then FAILED to open pause on all four consoles; captured NET4/radio
  healthy, pause flags0, no shared dialogue. Fixed24-frame START pulse does not
  prove native input acknowledgement/menu readiness. Course-return driver now
  uses the same readiness/echo-based toggle helper as the20-cycle check; live
  course-return retest is still required. No course reentry acceptance. The
  continuation shut the party down cleanly; NO wireless party is active.
  Steady sample:204 intervals, mean3.010 VBlanks. Main phase4 process samples
  include behavior283,render249,scene-tree79. Profile191 is verified PLAYER
  from the original overlay descriptor (factory020e6c0c,render order18).
  Player Behavior has204 boundary observations; stage Render104; other actors
  contribute to both phases. These are periodic samples, not CPU cycle costs.
  Warm movement mean3.628 includes cold stalls.
- New full-profiles frontend builds successfully; actual offline retail
  Adventure/file-A castle replay remains299 intervals all2 VBlanks. The300
  samples within main phase4 are ALL process phase5 (Render), proving main
  phase4 alone must not be classified as Behavior. Actual output and parser
  results: `performance-processes-retail/retail-adventure-full-profiles-performance.json`.
- Current normal isolated suite PASS:146 discovered,142 executed,4 obsolete
  prefix skips (`slot-aware-camera-all-tests.log`). Default game code/runtime
  is restored to the independently verified fbb candidate; timer experiment
  removal affects only experimental builds.

## Current candidate: local shadow visibility and geometry exhaustion

- User reports exact pinned89505d400/aea94 baseline physical multiplayer is
  functional with emulator parity, but significant slowdown/hitches, worse on
  hardware. User also reports missing objects/parts immediately on BoB entry,
  including a Yoshi head, with no first-person view; movement may restore it.
- Exact baseline reproduction `bob-head-aea94-baseline/` reaches native2048
  polygons and raises geometry overflow on every console. Normal four-Yoshi
  entry uses controller-earned key-only fixture, not synthetic stage entry.
- Native diagnostic d31380ff `bob-native-render-cost/` traces terrain/body/head
  draws with FIFO drains (NOT a cadence benchmark). About365 opaque terrain
  polygons are followed by953 shadow polygons,6 transparent polygons, then
  bodies125–128 and heads80–89 each. Slot3 body fills remaining RAM; its head
  submits0 polygons.99 stage shadows were registered. Both native shadow
  helpers check actor flags10, which AI synchronization temporarily clears.
- New normal `local-shadow-visibility-host.nds`, SHA256
  `fbb2262d6dbacd6c92e8f585bde99941d587ed8e323bde280f598e91e69abd2d`,
  independently reproduced by `local-shadow-visibility-rebuilt-host.nds`.
  Only the two native shadow flags reads recover the saved local far clip;
  AI still sees neutral flags. Native early returns, shadow shape/scale,
  original model/level assets, and boot/secure bytes remain intact.
- Native suite PASS:146 discovered,142 executed,4 obsolete prefix-only skips
  (`local-shadow-all-tests.log`). Six new ARM checks reproduce unwanted far
  shadow registration and verify both retail helpers, visible matrix/scales/
  stack opacity, offline/disabled/other-actor parity, explicit actor suppression
  and argument/CPSR preservation. Read-hook instructions/signatures are checked
  against the verified input. FIFO-drain measurement code is compiled out of
  normal images.
- Normal `bob-local-shadow-visibility/` passes startup, independent controls,
  castle/BoB entry and movement with matching input ticks. All four heads are
  visible. Entry shadows99→8, entry peak1621 polygons, movement peak1796;
  no observed overflow on any console. Cadence remains similar (~3.58 VBlanks
  per input tick including cold reads). Do not claim performance completion.
- CLOSED continuation `local-shadow-guest-star-save/`, exec60302, used that
  same party/socket `bob-local-shadow-visibility.sock`. Fresh guest2 coin PASS.
  Guest1 star/save/quit FAILED navigation: attempt1 missed(-1500,5500), then
  attempts2/3 missed(-4000,4500) while re-establishing coins after real exits.
  Captures show NET4/radio3,4,4,4, no message/celebration lock and all players
  alive. No new star or save acceptance. The party was shut down through
  `local-shadow-star-failed-close/`; that party is no longer active.
  Frozen driver sources/hashes are retained. The parent's frontend still has
 16 phase counters; the new32-phase executable is for subsequent sessions.
- Baseline aea94, planar-quad prototype02a8a8e1 and native-cost d31380ff parties
  were captured and shut down before each successor. The planar prototype still
  overflowed and had similar cadence; no optimized level/model assets are in
  the normal candidate. Its source/tests are archived privately under
  `planar-quad-experiment-source/`.
- Independent `painting-normal-render-observer-proof-host.nds` reproduces the
  prior3500 image before adding the shadow fix. Optional native render-cost
  instrumentation alone therefore does not change normal cartridge bytes.
- See PERFORMANCE.md for native-cadence/overflow definitions and remaining
  synchronous animation-read stalls. No full-speed hardware acceptance yet;
  campaign completion, newer-image physical wireless, remaining stage/mission
  regressions and one-build2–4-player support remain open.

The sections below are historical checkpoints; their ACTIVE labels have been
superseded by the current single party above.

## Current candidate: painting mesh allocation pressure

- The f14 all-stage run passed1..12, then FAILED12→13 with native Crash()
  on all3 guests: `castle-owner-stage1-through40-wireless/cycle-12/`.
  Captured actor307 is daPicGate_c (overlay80), with20x20 native cells.
  Its9600-byte mesh allocation had only4084 contiguous ROOT bytes available;
  the321KB common archive source was still resident. The normal campaign
  queue correctly stopped instead of starting another wireless party. Failed
  matrix party was captured and shut down.
- New normal image `painting-cache-pressure-host.nds`, SHA256
  `3500c6f00096639373c6af38132b93d56b028af726fdb1a6cbc8e2c7ab145110`.
  `painting-cache-pressure-rebuilt-host.nds` independently reproduces it.
  The mesh allocation releases that source cache only if ROOT cannot fit the
  original allocation. This call precedes PicGate's texture load; prior file
  views have closed and models own their copies. Later archive members use
  the already verified streaming path. Mesh dimensions, native allocator and
  native ROOT cleanup remain intact. No additional heap or smaller mesh.
- Object overlays overlap addresses. Builder checks the entire16-byte mesh
  call signature is UNIQUE to overlay80 among all ROM overlays; runtime checks
  it before installing the call after object overlays load. Other resident
  overlays and offline/private-heap allocations keep native behavior.
- Full isolated suite PASS:140 discovered,136 executed,4 obsolete prefix-only
  skips (`painting-cache-pressure-all-tests.log`). Seven new checks reproduce
  the native allocation failure; execute retail size calculation, allocation,
  mCells store and CleanupResources; preserve cell bytes and heap integrity;
  and cover cache-fit/offline/private-heap and matching/nonmatching overlay
  guards. Existing copied-member/cache-lifetime checks also pass.
- The4-console12..40 run `painting-cache-stage12-through40-wireless/`
  PASSED12..25, then FAILED26 during host pause/resume. Entry, movement and
  matching-input-tick checks had passed26 before resume. All consoles later
  showed NET0/radio0, error0x101, menu-closing pause2. There were no reply FIFO
  overflow warnings in this run. Native heap-integrity audit of completed
  captures passes (`native-heap-integrity-audit.json`). The failed party was
  captured in `stage26-pause-inspection/` and shut down before the next run.
  ROM `painting-cache-stage12-cycle-host.nds`, SHA256
  `b69979acd2324dc7ea5bc8b2d6b344ebe9da22c4c31fa2c8b25ea09c50b5a977`.
- The normal guest-star/save queue `painting-normal-guest-star/` is BLOCKED
  by that failure and has exited. It has not tested a coin, star or save.
- Diagnostic26 trace `pause-io-trace-stage26-wireless/` is testing first-cause
  connection errors and synchronous gameplay read/burst durations measured by
  native SDK VBlank time. This is observation only: the original gameplay
  reader remains synchronous. ROM `pause-io-trace-stage26-host.nds`, SHA256
  `09f6e864bd2cfb2a2eacbef7e767f5ca592d35825ef3e647c25101d72f91d425`.
  It starts26 directly, so cannot establish earned campaign progression.
  Diagnostic counters are compiled out of normal images; independent rebuild
  `painting-normal-final-diagnostic-proof-host.nds` still reproduces3500 above.
  A controller stress checks50 host pause/resume cycles after initial
  checks, stopping on the first actual native wireless failure. See
  `pause-io-trace-stage26-stress-ready/result.json`.
  The ready-state controller stress PASSED all50 cycles. The earlier stress
  stopped because it pressed START during the native post-resume cooldown;
  NET/radio and player synchronization remained healthy. That failed driver
  attempt is preserved separately; it does not reproduce the prior disconnect.
  Continuation `pause-io-trace-stage27-through26-wireless/` PASSED27..38,
  then FAILED the39 request: the party reached native stage1 instead, still
  NET4/radio3,4,4,4 and with no recorded connection failure. Do not count39
  or the intended remainder as tested. This party was captured and shut down.
- ACTIVE normal baseline reproduction `bob-head-aea94-baseline/`, socket
  `bob-head-aea94-baseline.sock`, uses the exact user-tested aea94 image,
  controller-earned key-only fixture and normal four-Yoshi course navigation.
  Frozen sources include native-cadence and geometry observations in the
  stock-core test frontend. `COOP_CAPTURE_COURSE_ARRIVAL=1` takes screenshots,
  RAM and performance counters before first-course movement checks. Target
  missing heads immediately on Bob-omb Battlefield entry, with no first-person
  view. Performance/rendering causes are unproved. See PERFORMANCE.md for
  read-only measurement definitions; never clear native overflow flags or
  change core limits to make a test pass. There is one live wireless party.
  Each run retains frozen driver hashes.

## Current candidate: ordinary castle celebration ownership

- Normal cartridge `castle-celebration-owner-host.nds`, SHA256
  `f14f4e3a6b61ac036a708d39ccd65aa56943d772c7adeaa36a8efb037103112a`.
  `castle-celebration-owner-rebuilt-host.nds` independently reproduces it.
- The packet-logged cannon-pitch retry passed startup and stages1..2, then
  FAILED stage3 (`cannon-pitch-stage1-cold-retry/cycle-02/dialogue-failed-*`).
  NET4 and radios remained active; guests2/3 stayed in native celebration8
  with control disabled, while a shared tally was open. The ordinary entrance
  had transition reason0, so the previous result-only normalization did not
  apply. This failed party was captured and shut down normally.
- New policy additionally reserves celebration8 for the leader on ordinary
  reason0 transitions. Other ordinary poses, death, water, flight and offline
  arrivals are preserved. The leader retains the native celebration.
- Full isolated suite PASS:133 discovered,129 executed,4 obsolete prefix-only
  skips (`castle-celebration-native-all-tests.log`). Three new checks execute
  the ORIGINAL model and ground initializer in the actual captured castle RAM,
  without adapting callees: old guest enters8/work5, corrected guests2/3 enter
  grounded0/work2 on the actual floor, host retains8/work5.
- Historical four-console run `castle-owner-stage1-through40-wireless/`, exec73107,
  driver frozen under driver/, packets.bin records real traffic (frontend trace
  is capped at100000 packets). It has passed stages1,2 AND the previously
  deadlocked3, including all4 movements, same-input-tick synchronization and
  shared pause/resume. The rest of1..40 is still running, not a pass.
  Diagnostic ROM `castle-owner-stage1-cycle-host.nds`, SHA256
  `3bdd721417bf3b84e12ed208020af039d276712ad407ee4edb8f578a3f084ea6`.
  Failure socket same output path plus`.sock`. Do not run another wireless party
  concurrently or overwrite this run. Earlier runners are closed.
- QUEUED normal campaign regression: `castle-owner-normal-guest-star/`, launcher
  `/workspace/runtime/queue-castle-owner-normal-star.py`, exec40203. It waits
  for the matrix's PASSED result and the actual previous driver PID100824 to
  exit before creating another wireless party. If the matrix fails it exits
  blocked instead. It uses normal f14 image, the previously earned key-only
  save (37bdc0cc...), real guest2 coin, guest1 Chain Chomp star, Save & Continue
  and consecutive host Save & Quit. Frozen driver and fixture provenance are
  already saved. Do not treat waiting/running as a pass or start another party.
- Two small controller-driver refinements await that normal regression: analog
  walking can stop after an observed native pickup (still requiring equal
  increased totals afterward), and the narrow castle-door route stops once it
  actually reaches the next room instead of insisting on a blocked endpoint.
  Native ROM source is published at6137000fd; these driver changes do not
  change f14 cartridge bytes.
- Normal-game star/save, boss wins, unlocks, ending, physical Download Play,
  the intermittent signed-menu failure and long-idle loss remain unverified or
  unresolved. Do not label this candidate complete/stable.

## Active reliability follow-up after full42–51 pass

- All10 stages42..51 PASS on the combined cannon-pitch diagnostic image
  `cannon-pitch-stage42-cycle-host.nds`, SHA256
  `a6cc9723e233676327937eb450e4e672e06902c34e36657852fe936dd3a1d6ee`.
  Results: `cannon-pitch-stage42-wireless/diagnostic-cycle.json`, plus initial42.
  Movement, matching-input-tick comparisons and shared pause/resume passed.
- The retained party later ended during a long idle interval. A continuation
  could not request51→1 because all consoles already had NET0/radio0,
  coopEnabled0, coopSessionEnded3, native error0x101. Private captures:
  `stage51-idle-loss-inspection/result.json` and RAM/ITCM/register dumps.
  The frontend logged REPLY FIFO OVERFLOW warnings after the completed checks.
  Do not infer that stage51 caused the loss or that this is resolved. Native
  SDK/transport versus frontend pacing needs isolation. Ended party shut down.
- `cannon-pitch-stage1-through40-continuation/result.json` remains FAILED;
  no additional stage passed in that continuation. Diagnostic tests now require
  NET4 and the native radio role (host3, guests4), and reject NET0 as well as6
  during transitions. The new guard rejected the actual ended party and
  accepted all23 retained stage checkpoints (28..32,33..40,42..51), all4
  consoles, using their actual captured RAM. Audit:
  `completed-stage-wireless-state-audit.json`.
- A fresh cold run then FAILED before gameplay:
  `cannon-pitch-stage1-through40-cold/result.json`. One signed Download Station
  guest displayed connection lost while the other two received menus; parent
  peer phases0/4/4, closed-entry acknowledgments0x1005. Preserve this failure:
  it is evidence that earlier successful repeat batches do not prove stable
  startup. Its cores were shut down after capturing RAM, WiFi and screens.
- ACTIVE fresh retry with packet logging:
  `/workspace/runtime/cannon-pitch-stage1-cold-retry/`, exec83694.
  Native1..40 cycle requested (39 transitions); packet trace packets.bin,
  frozen corrected driver in driver/, failure socket same path plus`.sock`.
  ROM `cannon-pitch-stage1-cycle-host.nds`, SHA256
  `3f1720278c5521e3ec440c416e8b65aabf1ad8795e13a839e79138ada7e9b29a`.
  This is a separate attempt, not a replacement for either failed run. It has
  now completed signed startup and stage1 with the new connection guard; the
  rest of1..40 remains running. Failed-parent RAM shows stationRestarted1 and
  stationAssociations0xE, so the menu failure was not simply an old parent
  preventing restart. Do not patch that hypothesis without further evidence.
- The queued connected-continuation runner30298 exited without touching the
  cold party after detecting the unexpected menu failure. There is only one
  active wireless party. Current native source remains0abb880b9/e20f35da5;
  only the connection-validation driver and this handoff changed since then.
  Normal combined image was rebuilt identically again as
  `cannon-echoed-pitch-final-host.nds` (64b5c9cc...).

## Additional user requirement: variable party size in one build

The user can currently test3 physical systems and will follow up with results.
For their pinned af50a63b7 test they were told to add --clients2 (host plus2
Download Play guests), so the output hash differs from the four-system f641
image. They also requested eventual support for2–4 players with one build.
This is now an explicit worklist item; it is NOT implemented or verified.
Audit found hardcoded COOP_EXPECTED_CLIENTS gates in bootstrap/host.cpp for
lobby readiness, BOOT, restart, transfer and native roster restoration. A proper
change needs a host-selected ready bitmap frozen before closing association
entry, with every later barrier consuming that roster and handling AID reuse.
Do not turn the current expected count into a timing-based automatic start.

## Current follow-up: cannon aim synchronization

- New normal image `/workspace/runtime/cannon-echoed-pitch-host.nds`, SHA256
  `64b5c9cc0e3d33f62c22ae3e5a337cf21914269ab9b3688cc4652f01bdd086a2`.
  An independent rebuild matches. This supersedes f641 for further emulator
  regressions; the user's pending physical tests explicitly target af50a63b7
  and f641. They currently have up to3 systems available.
- Native St_Cannon_Main used the displayed camera's pitch for launch velocity.
  Different local views therefore produced different native trajectories.
  The new hook replaces only its unsigned pitch read with the firing player's
  echoed bytes7..8; native yaw/trigonometry/state handling remain intact.
- Five private compiled/native checks reproduce the old divergence and verify
  equal launch velocities across4 different views, independent aim per player,
  offline parity, unsigned pitch, register/condition preservation and unchanged
  displayed pitch. Tests replace the final return before presentation and
  explicitly invalidate Unicorn's translated block after patching the fixture.
  Wireless cannon firing is still unverified.
- Full suite PASS:129 discovered,125 executed,4 obsolete prefix-only skips,
  `cannon-echoed-pitch-all-tests.log`. This does not establish campaign completion.
- Four-console28..32 cycle PASS: `cannon-pitch-stage28-wireless/`, all5
  stages passed four-controller movement, exact horizontal same-input-tick
  synchronization and shared pause/resume. Party exited normally. Driver frozen
  under driver/. Diagnostic ROM
  `cannon-pitch-stage28-cycle-host.nds`, SHA256
  `d57d51fd2c8a84d5effd4f65def03124ba40c7ae9b61642357962a7a3fb038a5`.
- The f641 normal party passed a key-only Save & Quit after repeated BOB exits:
  `seeded-camera-key-save-quit/result.json`. Host title/radio0, all3 guest session
  endings, both host key backups and other adventure slots verified. It then
  shut down. No new star was earned: the bot missed the lower exit, lawn and
  castle door routes. Do not report a star/save-continuation pass.
- A proposed general waypoint pulse change did not solve the narrow-door route
  and was reverted. Real analog movement crossed that doorway but missed its
  overly precise endpoint; captures remain in `seeded-camera-analog-door/`.
  Keep this input-navigation limitation separate from native/wireless faults.

## Current checkpoint: echoed camera controls and deterministic actor initialization

- Normal cartridge `/workspace/runtime/seeded-actors-echoed-cameras-host.nds`,
  SHA256 `f641c6e7927a5e088ad5e34e8fd9c23564124f4f164e6ef86ff0b55ddaab00af`.
  An independent rebuild produces the same SHA256. Retail boot bytes remain
  protected; physical host-boot confirmation belongs to baseline89505d400,
  not a physical test of this newer image.
- Full isolated suite:124 discovered,120 executed,4 obsolete prefix-only skips,
  all passing (`seeded-actors-echoed-cameras-all-tests.log`). Coverage includes
  original Snufit initialization, camera input parsing, loading errors and flight
  actor construction. Private Unicorn fixtures adapt external dependencies;
  these checks do not establish campaign completion.
- Four-console stages33 through40 PASS controls, exact horizontal positions at
  matching input ticks, and shared pause/resume:
  `/workspace/runtime/seeded-actors-stage33-wireless/diagnostic-cycle.json`.
  Diagnostic cartridge SHA256
  `f583585d7f37a1cb3bc8d060c0fe958ee0a057e1f1612323751be90b84ea2776`.
  Actor initialization now seeds native randomness from stage-relative identity
  rather than local rendering/IO RNG or loading-time NET ticks. This resolves
  the previously captured stage33 enemy/pause divergence in this regression.
- Earlier flight31 and transition32 PASS in `loading-grace-wing-wireless/` on
  SHA256 `252ae4a34ca28be7cfb00917f6be062057cb6816c82f53d467d18b6518a10fbc`.
  All actors receive native Mario caps at flight entrances. Arrival state is
  preserved except shared result poses. During asymmetric native loading,
  only the known wing-mask checksum mismatch is ignored while an active peer
  advertises loading. Radio, timeout, membership and gameplay errors stay fatal.
  Each guest actually exercised21 checksum clears during31→32. Retest these
  stages and Rainbow Ride on the final combined cartridge.
- Camera input availability, zoom prohibition, personal owl completion and head
  pitch are echoed per player. Shared dialogs retain host ownership. Sixteen
  native movement-mode guards and look-target changes use the local camera.
  Combined image f641 now passes all12 native zoom transitions and two mixed
  first-person/camera-arrow cases, exact same-input-tick sync throughout:
  `seeded-camera-controls-same-tick/{camera-controls,mixed-camera-controls}.json`.
  Host and guest first-person views remain still when the other console turns;
  camera-arrow dragging does not walk the player. Continuations must set
  COOP_FRAME_SAMPLES=1: serial snapshots alone produced a misleading12-unit
  vertical overlap discrepancy on the initial camera check. Teleport, movement
  camera modes and further area restrictions still need wireless coverage.
- Normal campaign attempt `seeded-camera-key-fixture-star/` loaded the previously
  controller-earned key-only save (SHA256
  `37bdc0cc4b85ed1ca875a8b6ed70b5895e08b3e2c96626bc4d8c403fdb815b58`),
  reached BOB with four players, then failed the analog coin navigation route.
  No coin/star/save pass is claimed. Party retained at the same path plus`.sock`
  for read-only diagnosis and real controller continuations. Physical jump
  pulses then cleared the lower terrain lip and collected a real guest coin:
  `seeded-camera-coin-recovery/result.json`, all4 totals0→1 and matching ticks.
  Star/save continuation in `seeded-camera-guest-star-continuation/` failed
  navigation before earning a star. Party subsequently saved its existing key
  and closed, as recorded in the follow-up above.
- Historical checkpoint headings below describe older images and closed runs.
  Their “active” labels are historical, not the current session status.

## Latest active checkpoint: native flight caps

- New normal image `/workspace/runtime/flight-party-native-cameras-host.nds`,
  SHA256 `15d4d2c0a83668f8b7edcf5502ab9d224b5d325980090b183512a1f3fec423da`.
  Builds add ordinary Mario caps to all actors at native flight entrances.
  The per-player selection array and pending-cap global are restored after
  spawning. Base character identities and normal entrances are unchanged.
- All102 discovered checks PASS with4prefix-only skips (98executed):
  `/workspace/runtime/flight-party-native-cameras-all-tests.log`. Four new
  compiled construction-policy checks cover flight, normal, offline and disabled
  mode, original table registration and selection restoration. Native actor
  construction is adapted in these policy tests; live flight is still pending.
- Preserving arrival kinds alone did NOT fix multiplayer Wing Tower31:
  `/workspace/runtime/native-arrival-wing-tower-wireless/result.json` returned
  all4 consoles to castle1 during arrival. Its failed party was captured and
  shut down. Native LevelEnter_Init explicitly changes non-Mario flight arrivals
  into a fall; those guests cannot remain in this aerial course.
- ACTIVE four-console test:
  `/workspace/runtime/flight-cap-party-wing-wireless/`, exec99953.
  Source frozen in driver/. Failure socket is that path plus `.sock`.
  It requests31..40 with real diagnostic chord transitions. ROM
  `/workspace/runtime/flight-cap-party-wing-cycle-host.nds` SHA256
  `52f6dc024f8290342a5ca2082a7c96b625717618c60154b72e6b021dddde6b7e`.
  No earned progression or flight acceptance is claimed before results.
- The fresh aea94b7b baseline party finished with an actual earned-key Save &
  Quit PASS: `/workspace/runtime/retail-boot-combined-earned-key-save/result.json`.
  HostTitle, three guest SessionEnded/radio0 and other adventure slots verified.
  Backup `wireless-save-after.sav` is8192bytes, SHA256
  `37bdc0cc4b85ed1ca875a8b6ed70b5895e08b3e2c96626bc4d8c403fdb815b58`;
  it contains the actual earned key and no stars. The party was shut down.
- Star navigation exhausted all3routes and did NOT earn a star on that baseline
  run: `retail-boot-combined-native-coin-continuation/course-star-route-attempts.json`.
  Route1 hit the under-bridge wall, route2 died at the post, route3 missed the
  lawn waypoint. Keep the successful coin/jump/key-save checkpoints separate
  from this failed star checkpoint. The older star/save acceptance remains tied
  to its older cartridges. Earlier queued runners have all exited.

## Work in progress: native arrivals and movement cameras

- New normal image `/workspace/runtime/native-arrival-local-cameras-host.nds`,
  SHA256 `4a8322b72a648cf67c6414aa7476be3af8f542feeb94f62f86b59d5408b9712e`.
  Sixteen more player-guarded native camera state setters use the local slot.
  Guest arrival normalization now applies only to shared result poses4/8/11/
  15/16/18. It previously grounded water/flight arrivals; flight has no floor
  under the spawn and could obtain INT_MIN Y. Do not claim wireless resolution yet.
- Full suite PASS:98 discovered,94 executed,4prefix-only skips,
  `/workspace/runtime/native-arrival-local-cameras-all-tests.log`. Six policy
  checks cover all19 native arrival types, host/guest, offline and non-result
  transitions. Two camera checks cover all16 additional setters under native
  local/foreign guards and offline parity. Core and src/ unchanged.
- The 16KiB build-time linked-code bound was raised to32KiB for these guards;
  the resident loader's64KiB bound is unchanged. The appended archive index and
  relocation tail are separate from that linked-code span.
- `/workspace/runtime/local-movement-camera-stage31/result.json`:single-console
  Wing Tower31 PASS; actual flight controls, not four-player acceptance.
- Later single-console matrix `/workspace/runtime/native-arrival-later-local-matrix/`
  PASSed all19 entries32..40,42..51. With the separate31 pass,20 later entries
  pass locally. These are diagnostic entries, not earned access or boss wins.
  Normal build was restored and exactly reproduced4a8322b7 at
  `native-arrival-local-cameras-rebuild-host.nds`.
- `/workspace/runtime/retail-boot-combined-fresh-guest-star/` is the fresh full
  four-console guest coin/star/consecutive-save run on the physically booted
  aea94b7b baseline (BEFORE these newest camera/arrival changes). It has earned
  the key, entered the castle and reached Bob-omb Battlefield. Source frozen
  under driver/. Failure socket:that path plus `.sock`.
- New native-arrival diagnostic31..40 image
  `/workspace/runtime/native-arrival-wing-tower-cycle-host.nds`, SHA256
  `6ea476987bb1fdd525bddc77412670b799be76f732ac2277f9f9421fa15b7cd8`.
  Four-console run `/workspace/runtime/native-arrival-wing-tower-wireless/`
  is queued in exec25534 (`/workspace/runtime/run-wing-after-save.py`), waiting
  for `retail-boot-combined-native-coin-continuation/result.json` to pass. That
  runner shuts the old party down before launching the new one. Earlier queued
  runners exited on the failed navigation checks; no two wireless parties ran
  concurrently. If this continuation fails, inspect its retained party first.
- The original fresh run reached BOB but its fixed-delay jump-height read
  failed. An independent read-only native-tick probe showed three successful
  jumps with peaks172/225/172 against a floor near62:
  `jump-history-inspection/result.json`. Jump checks now use recorded trajectories
  rather than a point read that can occur after landing. Full3jump check PASSed
  in `retail-boot-combined-history-continuation/repeated-guest-jumps.json`.
- That continuation collected a coin but missed its navigation endpoint; the
  subsequent fixed-target retry was already aiming at a collected coin. Both
  failures are preserved. The coin driver now selects a remaining native gold
  coin from a read-only RAM capture and approaches it with the native analog
  stick. `retail-boot-combined-native-coin-continuation/shared-coin-pickup.json`
  PASSes actual guest pickup1->2 on all4 replicas. No state injection/reload.
- `retail-boot-combined-native-coin-continuation/` is continuing the same fresh
  aea94b7b party through star and consecutive Save & Quit. Star route1 could not
  reach the western lawn from below the bridge; route2 uses an actual exit and
  reentry. The repository driver now leaves the under-bridge coin area through
  its southern opening before heading west; this correction is not in that
  already-frozen running driver. Do not claim a first-route or new-camera-ROM pass.
  The RemoteEmulators continuation did not copy the shared_course_coins driver
  attribute; its star helper's combined coin-witness field is therefore false,
  though the separate native coin checkpoint above passed.
- The older retained normal party could not resume after several hours idle:
  net/session/radio all0, no native crash or exception. Captures:
  `/workspace/runtime/combined-camera-campaign/retained-session-failure/`.
  Party shut down cleanly; do not count the failed resume as campaign coverage.
- Diagnostics now check the stage again after arrival messages before calling
  a matching-input-tick comparison. The earlier31 snapshot already showed
  castle1 at that point; its error was reported later as movement leaving31.

## Current checkpoint: retail boot preservation and local cameras

This section supersedes the historical experiments below. No campaign-complete
or full physical-wireless acceptance is claimed.

- Current normal candidate: `/workspace/runtime/retail-boot-full-local-camera-host.nds`,
  SHA256 `aea94b7bc8a51986b02c258cb779934bd200f269e05ad4d193282237be4baedf`.
  Default ROOT placement; acknowledged closed-entry startup; bounded particle
  reservations; streamed LZ; ROM-indexed NARC views; common source-cache release;
  callback-driven teardown; local zoom/recenter/FOV/first-person/normal camera;
  echoed per-player head pitch. This is the physically booted baseline; see
  the newer work-in-progress section before rebuilding or running unit tests.
- Host parent loader moved out of retail secure-area BIOS wrappers to overlay75's
  reserved result cave. ARM9, ARM7, first16KiB secure area and metadata stay retail.
  Four boot-layout checks PASS: `retail-boot-layout-tests.log`.
- True BIOS/firmware boot PASS: `retail-control-firmware-boot/result.json` and
  `retail-boot-local-camera-firmware-rerun/result.json`. The old secure-loader
  image ALSO passes: `previous-secure-loader-firmware-boot/result.json`.
  Therefore this does not reproduce or prove resolution of the physical white screen.
  User setup: New3DS + R4 SDHC2022 + latest Wood; original commit419afe72b.
- Boot-only physical retest requested for `retail-boot-local-camera-host.nds`,
  SHA256 `ce3cdcda3dd12f1c2c3a55a3efcf639066180b74e28ffdfa8552ec818dbf327b`.
  That earlier candidate lacks later first-person/head-pitch hooks and indexed NARC.
  User cannot download this artifact and requested a GitHub push plus local
  build steps. [BOOT-RETEST.md](../BOOT-RETEST.md) instead identifies the newer
  normal candidate aea94b7b above; a fresh rebuild exactly reproduced that hash
  (`github-boot-retest-build.log`). The user rebuilt the published
  commit89505d400 and confirmed: “The ROM now boots on the R4 card.” Mark the
  reported white-screen issue resolved on the New3DS/R4/Wood setup; physical
  Download Play and campaign behavior are not established by this boot report.
- Full current ROOT suite:90 discovered,86PASS,4prefix-only skips;
  `/workspace/runtime/full-local-camera-all-tests.log`.
- Eleven compiled native ARM camera tests PASS: `full-local-camera-arm-tests.log`.
  New normal four-console run: `/workspace/runtime/full-local-camera-story/`,
  frozen source under driver/; controller socket at that path plus `.sock`.
  This normal cartridge PASSed Download Play castle grounds, original Yoshi
  palettes and four independent movement controls. Party is retained paused.
  `full-local-camera-zoom-cycle/camera-controls.json`:12 physical-input transitions
  PASS (far/first-person/normal,4controllers), foreign view unchanged, shared
  player choices and matching-input-tick positions/progress synchronized.
  Reproduce with `COOP_BATCH_INPUT=1 COOP_FRAME_SAMPLES=1 python
  mods/coop/tests/wireless_camera.py --socket SOCKET --output NEW_DIRECTORY`.
  Test copy/hash and cartridge hash saved in that output directory. The current
  party began this check in far zoom following a successful one-tap probe on
  each console (`full-local-camera-input-probe-buttons.log`). Original touchscreen
  probe stopped on Standard mode0; this mode uses the physical X button.
  Recenter/turn/movement modes and fresh combined guest-star/save remain pending.
- Indexed archive diagnostic image SHA256
  `b1a096fa85f8f491cbf681684b8cfa85e8454a78c7df57b71ab2eed1976d0896`:
  `/workspace/runtime/indexed-narc-retail-boot-rainbow-matrix/`.
  Stage28 Rainbow Ride,29,30 PASS movement/shared pause/same-input-tick sync.
  Stage31 movement left the selected stage: all4 captured level1, crash0,
  exception0. Cycle incomplete; retained party shut down cleanly. This image
  precedes first-person/head-pitch hooks. Do not equate stage entry with earned progress.
- ROM index covers all13 archives and is independently checked against ndspy.
  Six native ARM archive tests PASS: `indexed-narc-arm-tests.log`.
  Four native cache-lifetime tests PASS: `stage-cache-release-arm-tests.log`.
  Earlier failed runtime metadata read captured at
  `narc-read-diagnostic-rainbow-matrix/dialogue-native-fault-*`; party shut down.
- Earlier fresh prefix normal run PASSED guest coin/star, Save & Continue,
  castle controls and consecutive Save & Quit:
  `prefix-runtime-normal-guest-star/result.json`. Star required route2;
  route1 bot failure retained. This image precedes later allocator/index/camera
  changes; do not transfer its acceptance to the latest candidate.
- Prefix placement is an abandoned opt-in experiment; the latest indexed body
  exceeds its16KiB capacity. Default ROOT is current. Four prefix-only installer
  tests skip on ROOT. Keep older logs as historical evidence only.
- Remaining acceptance is tracked in [WORKLIST.md](../WORKLIST.md).

## Historical bounded-reservation regression

- Source now fixes an additional physical-budget bug: extending a split arena
  previously ignored protected arrays/unusable tails and could reserve far
  more than the native35840/43008 bytes. Unusable tails now shrink through the
  correct heap before growth; pending protected arrays are excluded from the
  growth budget. Native manager/parser checks assert physical segment capacity
  never exceeds that native budget. All18particle tests and all71tests PASS:
  `/workspace/runtime/bounded-particle-prefix-all-tests.log`.
- Prefix placement DID install on all4consoles at02000100 and get past the
  skybox allocation. Its old unbounded particle build later crashed on map
  allocation while finishing entrance messages:
  `/workspace/runtime/prefix-runtime-rainbow-matrix/dialogue-failed-*`.
  This was a native Crash(), not a dialogue bug. Failed party shut down.
  Message helper now checks native fault flags before waiting for conversation.
- Current four-console run uses the bounded allocator and cache-safe loader:
  `/workspace/runtime/bounded-particle-prefix-rainbow-matrix/`, exec52176;
  failure socket `/workspace/runtime/bounded-particle-prefix-rainbow-matrix.sock`.
  Image `bounded-particle-prefix-rainbow-cycle-host.nds` SHA256
  `86906c9cc585f198fd7cd46ea375b739ede88d0cf158af9243c1a1868eee3171`.
  Frozen driver in driver/. Requests28..40; no acceptance claimed yet.
- Prefix installer now aligns its64-word fixup input window and flushes/
  invalidates it before physical reads, as does the512-byte LZ input window.
  Body input gets cache maintenance before IO. Four loader checks include
  these calls, bounds, exact relocation, cached reuse and rejection paths.
- The older normal prefix guest-star run remains active in exec52192. It
  precedes physical-budget correction and installer-input cache maintenance;
  do not attribute its campaign result to the newest bounded image.
- Canonical integrated output remains OLD. Prefix is still opt-in; do not
  promote it until current live load/controls and normal campaign checks pass.

## Newest results and active experiment

- All71 isolated checks PASS on the prefix build:
  `/workspace/runtime/prefix-runtime-all-tests.log`. Earlier67-check result:
  `/workspace/runtime/streamed-lz-cache-safe-all-tests.log`.
  Teardown's actual loaded-star wireless Save & Quit PASS:
  `/workspace/runtime/acknowledged-teardown-loaded-star/result.json`.
  HostTitle and all3guest SessionEnded verified. This used the actual earned
  guest star backup; it did not collect a new star in that run.
- Streaming LZ in ROOT placement still FAILED guest Rainbow skybox result33336:
  `/workspace/runtime/streamed-lz-rainbow-matrix/story-entry-native-crash-1`.
  Eight streamed LZ reads completed per guest, nine on host; NARC reads4each.
  ROOT largest20584,total29220; GAME largest23436. Failed party shut down.
- NEW OPT-IN --runtime-placement prefix puts the module at02000100..02004000,
  outside retail ARM9 (begins02004000), preserving first256bootstrap diagnostic
  bytes. Body15168 fits the16128-byte bound. Guard capacity and expected stock
  ARM9 base at build time; loader also checks capacity before copying. Fixups
  stream in64-word chunks, so no heap allocation or resident fixup tail.
  Four compiled ARM installer checks PASS at
  `/workspace/runtime/prefix-installer-arm-tests.log`: exact relocation/body,
  cached second install, oversized rejection, invalid fixup rejection; preserve
  diagnostics and first256retail ARM9 bytes. FS operations are unit adapters.
  Prefix is NOT the default until live acceptance.
- Current live Rainbow28..40 prefix run:
  `/workspace/runtime/prefix-runtime-rainbow-matrix/`, exec43921;
  failure socket `/workspace/runtime/prefix-runtime-rainbow-matrix.sock`.
  Image `prefix-runtime-rainbow-cycle-host.nds` SHA256
  `d37a6836d008a2db8279c94938e9314cbf89e078f494bf16ed7c42c2d94035ce`.
  Frozen drivers in driver/. Includes cache-safe512-byte LZ window, partial
  particle reservation, and full teardown fix including radio1 error screen.
- Fresh normal prefix guest coin/star/consecutive-save run is active:
  `/workspace/runtime/prefix-runtime-normal-guest-star/`, exec52192;
  failure socket `/workspace/runtime/prefix-runtime-normal-guest-star.sock`.
  Image `prefix-runtime-normal-host.nds` SHA256
  `c04f676b02aedcd357e78092558887c2a0e55143720e9c3a9085ac8abad7243e`.
  Frozen drivers in driver/. This run earns fresh key/coin/star; it has no
  preexisting save fixture. Source recovery includes all3new unit test files.
- Latest default ROOT-placement normal image (not prefix):
  `streamed-lz-cache-safe-normal-host.nds` SHA256
  `94452af860dfbb1fd6a723801d634d6d87d85e915eb54dc6f83ce6f73ee00089`.
  It includes input cache maintenance and the full teardown error branch.
  Do not treat the ROOT variant as Rainbow-compatible.


## Current checkpoint (supersedes historical runs below)

- Default startup is `closed-restart-parent`; entry closure and beacon update
  must both acknowledge before BOOT. Debug[31]==0x1005 proves execution.
  Five signed-menu boots and three complete story/course-return cold starts
  PASS. Course-return schedules [0,0,0], [0,600,1800], [1800,0,600] are at
  `/workspace/runtime/closed-entry-course-return-repeats/result.json`.
  Legacy restart-parent failed overall2/3; the phase1-only prototype did not
  exercise closure. Do not revive either as the default.
- Native particles retain full 40/256 or Bowser64/320 counts. Split arrays
  preserve each individual contiguous allocation and track heap owners.
  Total free bytes, rather than just each heap's largest block, gate splitting.
  But guest Rainbow has ROOT largest9264/total17736, GAME largest23436: its
  17408-byte particle array and 10272-byte resource array cannot both fit late.
  Captures `/workspace/runtime/streamed-narc-rainbow-inspection/load-failed-*`.
  Native ARM parser reproduces safe rejection, not an overwrite.
- Reserving the full arena early FAILED host skybox raw LoadFile: compressed
  scratch23607 plus result33336 exceeded contiguous free space. Reserving only
  the resource table at ROOT's high end also FAILED that temporary peak:
  `/workspace/runtime/reserved-table-rainbow-matrix/story-entry-native-crash-0`.
  ROOT total35260/largest26688; GAME largest23436. FAT64a is
  `data/vrbox/vr02.bmd`. These parties were shut down cleanly.
- Current policy reserves ONLY the native10272-byte resource table before stage
  resources; during native arena initialization, it reserves/protects the
  17408/21760-byte particle array before smaller callback requests. Both remain
  part of the original native35840/43008-byte budget. Owner-aware teardown
  frees all segments; real native manager+resource parser tests pass.
- Uncached NARC member views completed four actual reads per console before
  the later particle failure. Unit tests compare every member of all13NARCs
  with ndspy. Their physical FS APIs are ROM adapters, not wireless substitutes.
- NEW raw compressed-file hook at0201834c reads LZ10 with a512-byte input window,
  avoiding the full scratch copy beside its output. Five ARM tests PASS:
  exact33336-byte skybox vs ndspy, native OOM reproduction, bounded reads,
  eight releases without leaks, offline/uncompressed delegation. Tests use a
  private captured heap and stub physical file reads; no live memory writes.
- Current Rainbow wireless run: `/workspace/runtime/streamed-lz-rainbow-matrix/`,
  exec62560; failure socket `/workspace/runtime/streamed-lz-rainbow-matrix.sock`.
  Image `streamed-lz-rainbow-cycle-host.nds` SHA256
  `f160a47d8175bc5e4c7cf8a894e64f9f296406c24d15336b76fa215c189ad14d`.
  Frozen drivers in driver/. Diagnostic chord L+R+X (0x700), metadata describes
  it; old images use Select (0x304). It requests28..40; no pass claimed yet.
- Normal run `/workspace/runtime/streamed-narc-normal-guest-star/` PASSED real
  guest coin0→1 on every console, three acknowledged guest jumps, actual guest
  Chomp star on FIRST physical route, Save & Continue with persistence, castle
  controls. BUT subsequent Save & Quit FAILED: hostTitle, guests native radio4,
  menuLoading5/sessionEnded0. Star is actually saved; `earned-star.sav` retained.
  Image SHA2566c657e5765e2e5db8a85ab679c912346a3fab49502eb193d3847821e0bccc7c9.
  Failed party was shut down cleanly after read-only inspection.
- NEW teardown retry calls native02040724 while waiting for radio shutdown.
  SDK Reset02062200 is wrapped only during co-op title handoff: accepted Reset
  is deduplicated until the native Reset→Disable→End chain completes. Preserve
  the actual native callback. Pending flag is set BEFORE SDK submission; a
  rejected request does not claim an asynchronous operation. Native radio1
  is FAILURE, not "pending"; it exits the wait through the resident error screen.
- Four native ARM teardown checks exercise the real polling/callback chain,
  with SDK command submission stubbed. `/workspace/runtime/final-teardown-arm-tests.log`.
  The first66-test suite PASSED at `/workspace/runtime/streamed-lz-teardown-all-tests.log`;
  the latest error-screen branch PASSED targeted4teardown+7image checks.
- New quit wireless run from the controller-earned star backup:
  `/workspace/runtime/acknowledged-teardown-loaded-star/`, exec68959;
  failure socket `/workspace/runtime/acknowledged-teardown-loaded-star.sock`.
  Normal image `acknowledged-teardown-normal-host.nds` SHA256
  `e72f866d8b21189326145ff0912a0b3fca0fe4ceb1caa7eb87bd3ce8078166b0`.
  It includes compressed streaming/table reservation/reset deduplication, but
  precedes the extra radio1 error-screen branch. Flag --quit-loaded-save is
  explicit: this run does not earn a new star. Frozen drivers in driver/.
- Recovered old diagnostic party PASSED3..12 after46..51,1,2. Same-tick rerun
  corrected the false stage6 serial-read floor-adjustment failure. Evidence:
  `/workspace/runtime/luigi-early-same-tick-continuation/diagnostic-cycle.json`.
  This party is shut down. Always set COOP_FRAME_SAMPLES=1 on Remote drivers.
  Earlier healthy coverage13..23, fresh24, fresh25..27,42..45 does not establish
  the new memory policy's compatibility, boss victories, or earned progression.
- Canonical integrated bootstrap output is OLD. Latest build/coop module is a
  standalone normal module including the radio1 branch; its matching integrated
  host has not been rebuilt yet. Do not offer an old cartridge as current.
- No agents/core patches/live RAM writes. Stock melonDS1.1 core git clean at
  b86390e4428bf38ce4c1ce0e9ca446d6d25955e8. Readonly frontend adds ITCM/banked
  registers. Do not interrupt pending RemoteEmulators requests.

## Historical diagnostics and driver corrections

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
