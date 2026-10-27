# Four-player co-op worklist

The mod is experimental. A passing unit test or stage-entry diagnostic does
not establish campaign completion or real-hardware compatibility.

- [ ] Finish validation of the optional4KB compressed-input loading window.
  Eight native cases and the259-discovered-test suite pass; one captured asset
  needs7 reads instead of48. Four-Yoshi normal-route wireless stage testing is
  failed12→13 on0c52c505 after passing6–12. Diagnose native model-work
  allocation pressure: a guarded model-work boundary now passes nine native
  cases and the275-test suite; fresh167a normal-route wireless run is active.
  Measure same-source window-off loading transitions before
  claiming a causal load-time gain. Animated loading feedback remains open.
- [ ] Validate opt-in idle/walk animation prewarming in wireless play. Full266
  native tests pass, including exact bytes and temporary GAME/ROOT ownership.
  No new reads are added, but direct sleep-start first use still needs work.
- [ ] PRIORITY: optimize steady gameplay speed and eliminate significant
  hitches on real hardware across every level and supported party size.
  Latest56b combined four-console diagnostic PASSES short6–16, course return,
  and Save & Quit. Level14 collision elapsed falls from~6.7ms to~3.6ms;
  steady cadence252 intervals at2 VBlanks/33 at3, versus179/83 previously.
  Scene trajectories differ between runs; this is not an exact causal FPS
  comparison or physical acceptance. Level13 remains mostly3 VBlanks.
  An optional exact painting-wave coefficient experiment matches native
  arithmetic and reduces a private400-cell ARM replay from89200 to64929
  instructions and1200 to3 divisions. Live f67 passes13–16 and course
  return/save/quit; its13 cadence gain is modest and not full speed.
  A separate exact regular-grid-normal candidate passes seven full-mesh ARM
  comparisons and the247-test suite;90153→75864 instructions,400→324 native
  normalizations. Live timing is pending. A Yoshi sleep-start cold read also
  needs loading-time warming; it can span phase measurement boundaries.
  Normals7f9 passes13–16 and return/save/quit but13 is still mostly3 VBlanks.
  Its native flags reject the expensive painting mesh in these views. A new
  opt-in reject-only mesh path preserves hit testing/sliding/phase and visible
  bytes; nine native cases plus the256-test suite pass. Live timing is pending.
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
  and whole Stage Render without FIFO drains; eight ARM checks pass. Use it
  to quantify the remaining steady-play bottleneck before selecting changes.
  Completed native elapsed profiles identify whole Stage Render at~11.4ms
  versus~4.2ms for all four Player Behavior updates in steady BoB. Split its
  terrain/shadow/collision spans: collision takes9.4–9.7ms per frame. The
  optional leaf cylinder guard passes six native and live movement/pause checks
  but saves only~0.1ms and leaves cadence near3 VBlanks. Keep it disabled.
  Investigate ordered spatial candidates to avoid scanning distant pairs;
  isolated native replay matches contact/list state, with final ROM memory,
  callback and performance validation still required. Retail Adventure BoB
  baseline is confirmed near2 VBlanks.
  Ordered spatial candidates pass native four-console coin and course
  exit/reentry checks. Validated reuse with selective moving-object envelopes
  reduces steady collision cost to2.16–2.37ms and stage rendering to4.06–4.22ms;
  steady cadence is predominantly2 VBlanks, but warm movement still includes
  117 of313 intervals at3. The next candidate validates plans after callbacks
  and refreshes unchanged node lists in place with bounded sorting. All29 native
  checks and198 executed tests pass (208 discovered,10 documented skips).
  Its four-console speed test passes; warm slow intervals fall to22 of357,
  with104 validated callbacks, five full builds and16 incremental refreshes.
  Guest2 coin and course exit/reentry pass. An unprofiled four-console level
  matrix passes levels6–11 for entrance/short-motion compatibility, but includes
  a33-VBlank first-motion hitch from a2219-byte native guest read after stage
  cache flush. A separate optional persistent-cache experiment has200 native/
  other applicable tests passing and is starting a fresh four-console comparison.
  All-level exploration, hardware cadence and remaining slow intervals are open.
  Both cache and spatial planning remain
  optional; broader stage/party-size/physical validation and full-game performance
  acceptance are still required. Retail Adventure BoB cadence is near2 VBlanks.
  The four-console persistent-cache diagnostic passes short checks on6–23;
  level24 stops on a fatal controller route. Retention alone does not fix cold
  reads: a native ROOT capacity query is confirmed to evict30828 bytes in a
  three-system trace. Level14 also exposes repeated spatial preparation aborts.
  A bounded alternate-axis preflight and null-plan assembly fast path now pass
  31 native collision tests and203 applicable full-suite checks. Three-system
  direct14–16/exit/save/quit passes; normal four-console BoB speed is under test.
  Native frozen-list replay preserves contacts but full construction alone is
  more instructions than native; evaluate reuse, not square-root counts alone.
  Normal four-console3413b389 additionally passes guest2 coin and native course
  exit/reentry. Its warm cadence has339 intervals at2 VBlanks and22 at3.
  An allocation-free refresh for at most eight escaped envelopes now passes
  35 native collision checks and207 applicable full-suite checks. Pair work
  is capped at1024 and sorting at256 shifts; excess work retains full refresh
  or native processing. The first four-node live profile is a modest gain,
  not full-speed acceptance. Fresh eight-node profiling/gameplay checks are
  tracked in `edge-budget-cost-profile` and `edge-budget-gameplay-regression`.
  Both now PASS: steady/warm/pause, guest2 shared coin and native exit/reentry.
  Warm cadence is339 intervals at2 VBlanks,18 at3 and one at4. This does not
  establish a further cadence improvement or resolve cold-read hitches.
  An unmodified four-console retail VS reference also runs predominantly at
  two VBlanks with occasional jitter; its lighter scene is not a matched BoB
  CPU baseline. Cold-read hitches remain open.
  Guarded virtual capacity queries now preserve owned raw animation bytes
  without lowering native query results. Native pressure/growth still evict;
  unknown ownership/layout or bounded traversal failure uses the original policy.
  All24 animation-cache and212 applicable full-suite checks pass. Four-console
  d320a980 short checks6–16 and four-system return/save/quit now PASS. At7 there are four virtual-query
  successes/no fallback per peer,14 retained entries, and first movement has
  four cache hits/no new misses:163 intervals at2 VBlanks, one at3. The earlier
  33-VBlank Y_walk movement hitch is absent on this route. Initial stage6 cold
  entry still has a41-VBlank Y_wait guest read; this is not an all-hitch fix.
  The31-VBlank/2219-byte read is Yoshi's walking animation. A separate optional common-archive streaming build passes215 applicable native
  checks; matched wireless loading tests are starting. It avoids repeated whole mounts: its321224 bytes contain285814 bytes of
  player assets, while only the current characters may be needed at entry.
  Preserve every original file and native content if testing streamed loading.
  Remaining movement hitches include direct player paddle_end.bca reads outside
  the common-only raw-cache mask. An exact original FAT index of154 direct
  player poses now passes214 applicable native checks; fresh four-system6–9
  and second warm swimming checks are running with original mounting.
  Level14 still has collision6.68–7.23ms:194 last-frame nodes exceed192, and
  both axis windows exceed1024 despite327 actual envelope pairs. A cap-only
  private experiment is rejected. Separate bounded window work/candidate budgets
  need native and live validation before increasing these limits.
- [ ] Replace long black loading periods with visible, animated loading
  feedback on the host and guests. Keep a resident indicator responsive during
  Download Play handoff, wireless file reads and stage changes. Show real byte
  or phase progress where measurable; use an animated indicator when no honest
  total is available. Validate that feedback preserves native loading barriers,
  input acknowledgments, geometry/VRAM ownership and the retail hardware boot fix.
- [ ] Improve loading performance as well as steady gameplay speed. Measure
  cold/warm boot, castle/course transitions and guest file reads separately.
  Investigate redundant archive loading, repeated resource reads, prefetch and
  safe reuse/batching while preserving bounded memory, native authentication,
  file extents and synchronization. Record actual loading-time comparisons on
  hardware; animated feedback alone does not satisfy this requirement.
- [ ] Replace player-1-only doors and dialogue with shared interaction access.
  Allow eligible guests to initiate doors and advance shared dialogue. Select
  one synchronized owner per interaction and arbitrate simultaneous requests so
  transitions, rewards and dialogue advances occur exactly once. Test guests
  interacting with different doors/NPCs at once, disconnects and repeated inputs;
  preserve party synchronization without requiring the host to do every action.
- [ ] Let each player select a specific character through its native character
  door. Enforce exclusive Mario/Luigi/Wario assignments and retain each player's
  reserved standard multiplayer Yoshi color whenever they return to Yoshi.
  Resolve simultaneous requests deterministically and handle occupied characters
  without duplicate assignments. Verify character/door unlocks, occupied doors,
  transformations/cap states, course changes and returning to Yoshi on all peers.
- [ ] Replace the repurposed VS-level menu with the host's three real adventure
  saves A/B/C. Make its fourth option a distinct100% test session for unrestricted
  exploration. Label the choices clearly and synchronize the selected progress
  to guests before loading. Keep the100% fixture separate from the three real
  files so merely selecting it cannot overwrite normal progress. Verify all
  three actual file selections and the full-progress test option through native
  menu input, including empty files, unlocks and save/quit behavior.
- [ ] Display every connected player's location on each console's mini-map.
  Native numbered slot markers now pass four-console castle/BoB sprite
  submission checks and movement/shared-pause/world synchronization on58e096a6.
  The local head/arrow stays native; projection, clipping and area IDs are native.
  Broader maps and character/color matching remain open. The VS atlas cannot be
  used directly with story HUD textures/palettes.
  Give players distinct markers matching their character or reserved multiplayer
  Yoshi color. Keep the local player recognizable and handle area changes,
  entrances, deaths, character changes and map scaling on every peer. Schedule
  this after the current gameplay-performance work.
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
