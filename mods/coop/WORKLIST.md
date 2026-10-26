# Four-player co-op worklist

The mod is experimental. A passing unit test or stage-entry diagnostic does
not establish campaign completion or real-hardware compatibility.

- [ ] PRIORITY: optimize steady gameplay speed and eliminate significant
  hitches on real hardware across every level and supported party size.
  The user tested the pinned89505d400 normal ROM, SHA-256
  `aea94b7bc8a51986b02c258cb779934bd200f269e05ad4d193282237be4baedf`,
  and reports functional physical multiplayer with parity to melonDS behavior,
  but significant slowdown and occasional hitches on both, worse on hardware.
  Record this as physical multiplayer evidence for that exact image; the
  tested system count and campaign coverage were not specified. Profile
  native frame/VBlank cadence, worst-frame stalls, CPU/render work and
  synchronous wireless reads before selecting optimizations. Compare against
  retail single-player cadence in the same scenes; do not use host emulator
  wall-clock speed as proof of full-speed DS gameplay. Evaluate cold and warm
  assets, moving cameras, enemies, effects, pause/resume and repeated course
  transitions. Preserve synchronization, original content and standard colors.
  Require final combined-image physical performance acceptance as well as
  stock-core emulator regression coverage. See [PERFORMANCE.md](PERFORMANCE.md)
  for measurement definitions and the traced animation-read latency.
  The isolated timer-reset experiment14ab0ad99 showed no useful matched BoB
  gain and was removed. Main phase4 dominates steady samples but contains both
  behavior and rendering; new read-only process histograms distinguish those.
  Camera acceptance now uses native player slots even when guest association
  order differs from console order.
  An optional64KB compressed animation-read cache now passes16 native ARM
  checks and caches on all three Download Play guests as well as the host.
  The274084aa BoB warm sample reduces the longest observed input interval
  from34 to4 VBlanks, but steady cadence remains approximately3 VBlanks.
  It is not enabled by default and needs wider stage/memory/physical coverage.
  An optional existing-SDK-clock profiler measures Player Behavior/body/head
  and whole Stage Render without FIFO drains; seven ARM checks pass. Use it
  to quantify the remaining steady-play bottleneck before selecting changes.
  Completed native elapsed profiles identify whole Stage Render at~11.4ms
  versus~4.2ms for all four Player Behavior updates in steady BoB. Split its
  terrain/shadow/collision spans next. An optional conservative cylinder axis
  broadphase passes six native parity/ABI checks; live speed measurement is
  running. Retail Adventure BoB baseline is now confirmed near2 VBlanks.
- [ ] Fix intermittent missing objects/model parts on individual consoles.
  The user observes this on physical hardware and melonDS, including a Yoshi
  head disappearing immediately on entry to Bob-omb Battlefield, with no
  first-person view used. Moving around may restore it. Target that ordinary
  all-Yoshi course entrance first. Capture each view at the same game/input
  tick and compare model visibility, personal first-person/head hiding,
  animation state, resource ownership/lifetime, texture/palette state and
  native geometry limits. Exact aea94 reproduction reaches2048 polygons on
  every console. Native per-part tracing shows slot3's body filling RAM and
  its head submitting0 polygons.99 shadows are registered across the whole
  stage: the deterministic AI visibility guard also disabled native far-shadow
  suppression. A new flags-read hook restores the saved local shadow decision
  without changing AI flags. Six isolated checks execute both retail shadow
  helpers and verify clipping, visible scales/opacity, offline parity and ABI.
  The fbb2262d normal candidate passes the four-console BoB entry/movement
  regression: all heads visible, shadows99→8, entry peak1621 polygons,
  movement peak1796 and no observed overflow. Other scenes/parts and physical
  retest remain open. Add movement, camera
  and crowded/effect-heavy scenes to rendering acceptance; performance
  optimizations must preserve complete models and intended visibility.
- [x] Fix the reported white screen before the title screen on real hardware.
  Original failing commit: `419afe72b1f9d133bd26bb03bcd71ebe4d687869`,
  cartridge `sm64ds-haxxstation-game-handoff.nds`.
  Hardware: softmodded New Nintendo 3DS, R4 SDHC 2022, latest Wood firmware.
  The user rebuilt the candidate published at
  `89505d4009e862e4c561798b901cf45e4992c665` using
  [BOOT-RETEST.md](BOOT-RETEST.md) and confirmed: “The ROM now boots on the R4
  card.” The documented output has expected SHA-256
  `aea94b7bc8a51986b02c258cb779934bd200f269e05ad4d193282237be4baedf`.
  The fix preserves retail ARM9/ARM7, secure-area bytes and metadata by moving
  the parent loader into overlay 75. BIOS/firmware startup and four image-layout
  checks also pass. The user also reports functional physical multiplayer
  on this pinned image. Newer-image physical and campaign acceptance remain open.
- [ ] Give each player independent camera controls and state, including zoom,
  recentering, and personal movement camera modes. Keep shared story decisions
  synchronized without consuming player 1's camera controls on other consoles.
  The current normal cartridge passes twelve real-input zoom transitions:
  far, first-person, and normal view on all four consoles, with foreign cameras
  unchanged and matching-input-tick synchronization. Sixteen additional native
  movement-camera guards now select the local player; compiled native checks
  cover local/foreign slots and offline parity. Recenter, turn, swimming, flying,
  look-target changes and teleport camera setup still need wireless coverage.
  The combined candidate also passes camera-arrow drags alongside host and
  guest first-person views, with independent yaw and matching input ticks.
  Cannon launch now reads the firing player's echoed pitch; five native
  arithmetic checks reproduce the original divergent trajectory and verify the
  fix. Real wireless cannon firing and remaining movement modes are unverified.
- [ ] Complete the Rainbow Ride memory and wireless filesystem regressions.
  ROM-verified member extents now avoid the failing runtime metadata reads.
  The combined cannon-pitch candidate now passes four-console Rainbow Ride28
  through32, including native Mario-cap flight and the asymmetric loading
  checksum fix. Deterministic actor initialization resolves the
  captured stage33 enemy/pause divergence; the latest33..40 cycle passes all
  controls and synchronization checks on the prior image. Finish the remaining
  stages and mission variants, then repeat final combined acceptance. These are diagnostic
  entries, not evidence of earned progression or boss victories.
  The all-Yoshi1..40 continuation found an ordinary stage3 celebration/tally
  deadlock. Guests2/3 were stuck while wireless stayed active. Reserving the
  ordinary celebration8 for the leader now passes the same four-console3
  regression; the later run passed stages1..12. Native captured model/
  ground initializer checks pass, and movement/death/flight poses stay intact.
  That run later passed1..12 but crashed all3 guests on12→13 while allocating
  a native9600-byte painting mesh. The new pressure-triggered common-source
  release passes captured native allocation/cleanup checks and the live12→13
  regression. The new12..40 matrix passed12..25, then lost the native wireless
  connection while resuming the stage26 pause menu. First-cause error and
  synchronous gameplay file-read diagnostics are investigating this regression.
- [ ] Validate source-cache release and bounded particle reservations across
  all native stages, mission variants, repeated transitions, and teardown.
  Preserve native particle counts, individual array contiguity, heap ownership,
  and the actual physical allocation budget.
- [ ] Repeat fresh guest coin/star, Save & Continue, and consecutive Save & Quit
  on the final combined cartridge. Preserve both host backup banks and other
  adventure files. Earlier successful cartridges are separately identified in
  the emulator handoff; do not transfer their acceptance to a newer build.
- [ ] Support2–4 total players with one normal cartridge build. The host
  explicitly starts a ready party of1–3 guests; joining earlier must not
  automatically start the transfer or require a particular timing window.
  Freeze that ready roster before the acknowledged entry-close handshake,
  then use its actual association bitmap/count for firmware BOOT, payload
  readiness/completion, parent restart, native MAC roster restoration and
  gameplay/save barriers. Handle abandoned/reused AIDs rather than assuming
  every roster occupies consecutive radio slots. Current bootstrap/host.cpp
  gates still use COOP_EXPECTED_CLIENTS throughout; --clients1/2/3 remains a
  build-time requirement pending this change. Verify the identical ROM at all
  three party sizes, delayed joins, lobby departures and repeat sessions.
- [ ] Recheck simultaneous and delayed Download Play selections, guest/host
  disconnects, and repeat sessions. A later cold start lost one signed loader
  before its menu while two others succeeded; earlier5/5 and3/3 batches do not
  establish stable startup. Preserve that failure and inspect the packet-logged
  retry. A retained paused party also ended after a long idle interval with
  native error0x101 and melonDS reply FIFO overflow warnings; isolate native
  SDK/transport from frontend pacing. Do not suppress genuine radio failures
  or require a human timing window. Keep standard Yoshi palettes.
- [ ] Verify actual boss victories, character and castle unlocks, shared course
  collectibles, and the ending with four consoles. Synthetic stage selection
  does not prove earned progression. Physical 100-coin-star collection remains
  unverified despite compiled native counter checks.
- [ ] Build and identify the final normal cartridge, package reproducible mod
  sources/instructions, and document the tested emulator and hardware results.
  Do not label a diagnostic or partially validated image stable or complete.

Current captures, build hashes, and active run locations are recorded in
[EMULATOR-HANDOFF.md](tests/EMULATOR-HANDOFF.md).
