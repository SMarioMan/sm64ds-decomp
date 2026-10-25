# Four-player co-op worklist

The mod is experimental. A passing unit test or stage-entry diagnostic does
not establish campaign completion or real-hardware compatibility.

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
  checks also pass. Physical Download Play and campaign acceptance remain open.
- [ ] Give each player independent camera controls and state, including zoom,
  recentering, and personal movement camera modes. Keep shared story decisions
  synchronized without consuming player 1's camera controls on other consoles.
  The current normal cartridge passes twelve real-input zoom transitions:
  far, first-person, and normal view on all four consoles, with foreign cameras
  unchanged and matching-input-tick synchronization. Recenter, turn, swimming,
  flying, and other personal movement modes still need wireless coverage.
- [ ] Complete the Rainbow Ride memory and wireless filesystem regressions.
  ROM-verified member extents now avoid the failing runtime metadata reads.
  Four-console Rainbow Ride (28), stages 29 and 30 pass controls, shared pause,
  and matching-input-tick synchronization. The cycle stopped at stage 31 when
  movement returned all consoles to stage 1 without a native fault. Investigate
  that transition and finish the remaining stage/mission coverage.
- [ ] Validate source-cache release and bounded particle reservations across
  all native stages, mission variants, repeated transitions, and teardown.
  Preserve native particle counts, individual array contiguity, heap ownership,
  and the actual physical allocation budget.
- [ ] Repeat fresh guest coin/star, Save & Continue, and consecutive Save & Quit
  on the final combined cartridge. Preserve both host backup banks and other
  adventure files. Earlier successful cartridges are separately identified in
  the emulator handoff; do not transfer their acceptance to a newer build.
- [ ] Recheck simultaneous and delayed Download Play selections, guest/host
  disconnects, and repeat sessions. Use protocol acknowledgments, not a required
  human timing window. Keep standard green/red/blue/yellow Yoshi palettes.
- [ ] Verify actual boss victories, character and castle unlocks, shared course
  collectibles, and the ending with four consoles. Synthetic stage selection
  does not prove earned progression. Physical 100-coin-star collection remains
  unverified despite compiled native counter checks.
- [ ] Build and identify the final normal cartridge, package reproducible mod
  sources/instructions, and document the tested emulator and hardware results.
  Do not label a diagnostic or partially validated image stable or complete.

Current captures, build hashes, and active run locations are recorded in
[EMULATOR-HANDOFF.md](tests/EMULATOR-HANDOFF.md).
