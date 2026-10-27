# Four-player co-op worklist

The mod is experimental. A passing unit test or stage-entry diagnostic does
not establish campaign completion or real-hardware compatibility.

- [x] Write a detailed generalized HaxxStation/Download Play integration guide
  for future game mods. [HAXXSTATION-PORTING.md](HAXXSTATION-PORTING.md) documents
  authentication, packaging, host ports, reconnects, WFS and porting boundaries.
- [ ] PRIORITY: attain full-speed steady gameplay and eliminate hitches on
  real hardware in every level and supported party size. Preserve native
  geometry, animation, actors, synchronization and standard Yoshi colors.
  Measure native VBlanks/input cadence, worst stalls, CPU/render spans and
  synchronous wireless reads; host wall-clock speed does not prove DS speed.
  Optional ordered collision plans and exact painting math/normals/reject-only
  mesh work pass native tests and earlier mixed-character13–16 diagnostics.
  Several four-Yoshi stages reach mostly2-VBlank cadence, but first-use pose
  reads still cause30–42-VBlank guest stalls and BoB still has3-VBlank samples.
  This is not full-speed or full-campaign acceptance. The latest loading/prefetch
  candidate105a389d passes296 tests (286 executed,10 skipped).
  The normal four-Yoshi0c52 run passes6–12 but crashes guests on12→13 in a
  native1048-byte model-work allocation. A guarded source-release boundary
  preserves native model data, allocation and cleanup; nine captured ARM
  cases and the full275-test intermediate suite pass. The167a repeat passes
  6–11 and reaches12 before capture storage ENOSPC interrupts the harness;
  that is not a native game failure and does not validate13. The5bf repeat
  now uses separate scratch storage and PASSES6–16, course return and four-system
  Save & Quit. Every steady stage sample has zero physical gameplay reads;
  the expanded fourteen-pose105a candidate eliminates the three stage9 swimming
  movement reads as well.6/13/14/16 retain slower intervals.
  Continue17–51,
  repeated loads, moving/visible paintings, missions, bosses and final combined
  hardware performance acceptance. Exact evidence and older results are in
  [PERFORMANCE.md](PERFORMANCE.md) and [EMULATOR-HANDOFF.md](tests/EMULATOR-HANDOFF.md).
  The user's physical confirmation applies to old normal89505d400 image
  `aea94b7bc8a51986b02c258cb779934bd200f269e05ad4d193282237be4baedf`:
  functional physical multiplayer, with substantial slowdown/hitches. Newer
  images have no equivalent physical performance acceptance yet.
  The user also tested requested3-systembe682ed7f performance image
  `f7fc1a0118fadfde2aa16ea64b3a53c7d510659ab50c5388fad36caefc50967d`:
  all Yoshi heads visible, no missing geometry observed, but very slow play
  and frequent movement hitches with at most slight gain. Hardware performance
  FAILED on that image. Long nondescript black/white loads also remain poor.
- [ ] Finish acceptance of optional loading and first-use IO improvements.
  `--experimental-lz-window` uses optional4KB ROOT/GAME input storage after
  output allocation, with the original512-byte stack fallback. Eight native
  cases pass; one captured asset requires7 reads instead of48. Same-source
  window-on rebuild reproduces167a exactly; window-off8cbf93be passes21
  discovered checks (18 executed,3 skipped). An actual matched four-console comparison
  measures window-off→on SDK VBlanks2733→1500 for1→2,5139→4304 for6→7
  and4898→4095 for7→8. This includes input/polling, is only one matched pair,
  and does not establish hardware or universal loading improvement. Native mounting and
  original archive/file extents must stay intact; the earlier mount-bypass
  experiment was withdrawn after a wireless crash.
  `--experimental-animation-prewarm` copies verified Yoshi idle/walk members
  before common-source release without additional reads; native heap/lifetime
  tests pass. It does not remove the direct sleep/cold first-use hitches.
  `--experimental-animation-prefetch` moves fourteen missing idle/walk/sleep/cold/swimming
  reads after native skybox loading using optional8KB GAME scratch and the
  existing32-entry/64KB reclaimable cache. Eight native cases pass, including
  exact bytes/cursors, repeat hits, native close, short reads, readiness and
  both heap-pressure paths. Compare gameplay stalls and total loading time
  on5bf, all stages, both guests and host. All performance options remain off
  by default pending acceptance.

- [ ] Replace long black loading periods with visible, animated loading
  feedback on the host and guests. Keep a resident indicator responsive during
  Download Play handoff, wireless file reads and stage changes. Show real byte
  or phase progress where measurable; use an animated indicator when no honest
  total is available. Validate that feedback preserves native loading barriers,
  input acknowledgments, geometry/VRAM ownership and the retail hardware boot fix.
  The opt-in stage-loading LOADING/spinner passes13 native lease/fade/window/
  restoration checks and the296-test suite. Actual105a389d screenshots verify
  letters and multiple spinner phases on all four consoles during normal
  transitions; gameplay/heap and save checks are running. Thedf0b anddd47
  prototypes had invisible text under native darkening; they are superseded. Initial firmware/menu
  loading phases and final hardware visual acceptance remain open.
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
- [x] Confirm the reported missing Yoshi heads at spawn are fixed on the
  user's three-system R4 test ofbe682ed7f/f7fc1a0: every head is visible and no
  missing geometry observed. Broader camera/level/final-image rendering
  acceptance remains part of the performance and campaign checks.
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
