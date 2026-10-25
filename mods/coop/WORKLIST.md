# Four-player co-op worklist

The mod is experimental. A passing unit test or stage-entry diagnostic does
not establish campaign completion or real-hardware compatibility.

- [ ] Fix the reported white screen before the title screen on real hardware.
  User-tested commit: `419afe72b1f9d133bd26bb03bcd71ebe4d687869`.
  Cartridge: `sm64ds-haxxstation-game-handoff.nds`.
  Hardware: softmodded New Nintendo 3DS, R4 SDHC 2022, latest Wood firmware.
  The R4 loading screen disappears, then the game stays white. Other commercial
  games boot on this setup. Preserve the host's retail ARM9/ARM7 executables and
  secure-area metadata; test BIOS/firmware boot as well as direct boot, and
  obtain a physical retest of a clearly identified candidate. The boot-preserved
  candidate passes BIOS/firmware startup and four cartridge-layout checks;
  the older image also boots in that emulator, so a hardware fix is unproven.
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
