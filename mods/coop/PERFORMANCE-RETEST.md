# Three-system performance and loading retest

This optional candidate combines the current performance experiments and stage
loading feedback without timing or stage-cycle diagnostics. It requires one
flashcart host and two ordinary DS Download Play guests. A single ROM supporting
an arbitrary two-to-four-system party is still on the worklist.

The previous three-system hardware report for `be682ed7f` confirmed complete
Yoshi heads, but very slow movement and long blank loads. The updated candidate
adds the packed common-animation cache and conservative line/coin-shadow work
to the earlier loading/performance options. It has **no physical performance
acceptance yet**.

The exact three-system image below passes real stock-core Download Play startup,
normal castle/painting entry into Bob-omb Battlefield, independent movement,
shared pause and coin-state comparison, course return, host cartridge saving,
host title initialization and both guest shutdowns. Its steady BoB guest sample
has905 two-VBlank intervals, one three-VBlank interval and one four-VBlank interval;
movement has270 two-VBlank and one three-VBlank interval. Those are emulated
SDK input intervals, not measured hardware frame rates. A related four-system
build passes stages6–23; stationary enemies killed a guest in24, followed by a
synchronized native castle recovery and Save & Quit. Later courses and complete
campaign/physical speed acceptance remain open.

If you already built the older `2ac1e988…` retest, its hardware results are still
useful. The new image is a separate comparison and excludes the new experimental
bootstrap multicast option.

## Build

Fetch the `co-op-multiplayer` branch and use source commit `175708cbb` for this
exact hash, then activate your existing build environment. Later documentation
and test-only commits do not change this ROM.
Use your own paths for the EU revision-0 game and USA Download Station Volume1
dumps. The command below uses the cloud setup's paths; the flags are portable.
Run builders one at a time because their intermediate filenames are shared.

```bash
source /workspace/setup/activate.sh
python mods/coop/build_download_play.py /workspace/inputs/sm64ds-eu.nds \
  --station /workspace/inputs/download-station.nds \
  --save-slot A --clients 2 \
  --experimental-animation-cache \
  --experimental-lazy-animation-eviction \
  --experimental-persistent-animation-cache \
  --experimental-collision-plan \
  --experimental-painting-math \
  --experimental-painting-normals \
  --experimental-painting-visibility \
  --experimental-lz-window \
  --experimental-packed-animation-cache \
  --experimental-line-broadphase \
  --experimental-local-coin-shadows \
  --experimental-animation-prefetch \
  --experimental-loading-screen \
  --output build/coop/bootstrap/packed-performance-loading-3p.nds
```

Expected SHA-256, with slotA and the inputs pinned in the main README:

```text
28e661dca4b9d1914b3987e3440317b0711de363c4ad2f87c3d2132da695073d
```

The adjacent JSON identifies the exact ROM, input hashes and module options.
This selects and saves adventure fileA. `--save-slot B` or `C` changes both the
selected file and output hash. No custom melonDS, BIOS modification or special
button timing is required by the mod. Boot the host cartridge normally, choose
its multiplayer option, and join its broadcast using Download Play on both guests.

## Useful observations

Compare the same saved game, party size and route with the earlier hardware
build. Please retain the ROM hash, DS/flashcart models and any footage with the
results. Record these separately:

- Cold start and joining: successful boot, all guests complete both transfers,
  and no need to join or press a button within a narrow time window.
- Castle→Bob-omb Battlefield loading: approximate time from entry until all
  players can move; whether every screen shows visible changing LOADING feedback
  during the stage wait. Initial Download Station/firmware/menu waits are not yet
  covered by this indicator.
- Normal entry: every Yoshi head and intended object remains visible.
- Steady play and movement: idle briefly, move each player independently, then
  move all three together. Distinguish constant slowdown from intermittent
  freezes. Also compare swimming and a scene with moving paintings if accessible.
- Return and save: leave the course normally, use Save & Quit, and confirm a
  fresh launch loads the chosen adventure file.

Hardware speed is the acceptance criterion. The emulator checks use unmodified
melonDS1.1 cores; their native VBlank/input measurements are not a hardware FPS
claim. The source's diagnostic-only actor-class profiler is absent from this ROM.

## Build checks recorded for this image

The integrated image passes44 isolated/native and layout checks: original retail
boot executables and secure area, cartridge/FAT bounds, relocation behavior,
minimap selection, loading leases/fades/restoration, exact preloaded animation
bytes, and the guarded model-work allocation. The combined diagnostic source
passes299 discovered tests (289 executed,10 skipped). These checks do not replace
physical wireless, all-level or final combined-image testing.
