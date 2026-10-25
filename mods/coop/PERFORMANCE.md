# Performance investigation

The user reports functional physical multiplayer on the89505d400 cartridge,
SHA256 `aea94b7bc8a51986b02c258cb779934bd200f269e05ad4d193282237be4baedf`,
with significant slowdown and occasional hitches. These also occur in melonDS,
less severely. Full-speed gameplay across all levels is a priority and remains
unverified. The tested physical party size and campaign coverage were not specified.

The user also reports intermittently missing objects/model parts, including a
Yoshi head, on both hardware and emulation. It is missing immediately on
entering Bob-omb Battlefield with no first-person view; moving may restore it.
Target that normal all-Yoshi entrance first. Investigate this alongside the
performance work; no rendering cause has yet been established.

Measure steady play and worst stalls separately. Compare the same scene,
camera, enemies and effects against retail single-player cadence, then compare
the identical mod image with2,3 and4 players. Record the exact image hash,
hardware, cold/warm assets and controller route. Faster host emulation or a
passing synchronization check does not establish full-speed hardware gameplay.

## Read-only emulator measurements

The test frontend links the unmodified melonDS core. Build it using the
existing core configuration (these values select the current JIT test setup):

```bash
COOP_ENABLE_JIT=ON COOP_ENABLE_GDB=OFF \
  COOP_HARNESS_OUTPUT=build/coop/melon-test-performance \
  bash mods/coop/tests/build_harness.sh
```

Use `COOP_PERF_SAMPLES=1` and point `COOP_HARNESS_EXE` at that executable when
starting a test. Ordinary `campaign.snapshot` checkpoints then write
`*-performance.json`. Retained controller clients must also set
`COOP_PERF_SAMPLES=1` to request those reports. `ds.command('performance')`
reads counters without locking/stopping the emulated consoles;
`ds.command('performance-reset')` clears only frontend measurement history.

Counters group offline and wireless observations separately by native stage
and paused state. The native SDK VBlank counter measures intervals between
successive outgoing input ticks, excluding initializing scenes and loading
flags. Reports include mean, p50/p95/p99, maximum and a histogram (bin256
includes larger intervals). They also record skipped tick sequences and the
main-loop phase observed at emulated frame boundaries. Phase observations
locate waits approximately; they are not CPU instruction/cycle profiles.
Input cadence is not rendered FPS. Compare it against the retail baseline
before assigning a frame budget. Scene/state boundaries and incomplete final
intervals are excluded, so capture individual hitches as well as aggregates.

Reports also record rendered polygon and sampled building polygon/vertex
maxima, plus observations and rising edges of the native polygon/vertex RAM
overflow flag (DISP3DCNT bit13). DS limits are2048 polygons and6144 vertices.
The flag is sticky: samples are not a count of newly failed frames, and an
inherited flag is not proof that the current level overflowed. The observer
never clears it. Check visibility/model lifetimes and personal first-person
head hiding as well as geometry exhaustion when reproducing missing parts.

## Current leads

The diagnostic26 image09f6e864 passed initial four-console movement/shared
pause and50 additional pause/resume cycles. Its subsequent stage27 capture
recorded a synchronous gameplay burst of three reads totaling22212 bytes,
lasting126 native SDK VBlanks on each guest (about2.1 emulated seconds).
The host's longest observed burst was one VBlank. This is an emulator
measurement, not a physical timing measurement or a proved cause of the
earlier stage26 disconnect.

The traced offsets resolve to player animation members in original arc0:
`data/player/Y_wait.bca` (7430 bytes), `data/player/wait.bca` (3776 bytes),
and the final slow-burst member `data/player/W_wait.bca` (7484 bytes).
The common archive contains132 animation members totaling202308 bytes.
Releasing its321KB source cache fixes actual guest allocation failures but
means subsequent animation loads can require synchronous wireless reads.
Evaluate resource reuse and a bounded, pressure-aware working set against
measured access patterns. Preserve the heap-pressure fixes and native resource
lifetimes; simply retaining the whole archive recreates known crashes.

Also profile native radio synchronization waits, actor/animation updates,
rendering, collision and effects in representative expensive scenes. Require
repeated transitions and final combined-image physical performance tests before
closing the worklist item.


## Bob-omb Battlefield geometry regression

The exact aea94 baseline reproduces overflow at normal all-Yoshi course entry
on all four consoles (`bob-head-aea94-baseline/`). A subsequent diagnostic
image d31380ff drains geometry to measure native draws: it is NOT a cadence
benchmark. Its `bob-native-render-cost/first-course-initial-arrival-runtime.json`
shows about365 opaque terrain polygons,953 shadow polygons, then6 transparent
terrain polygons. Player bodies contribute about125–128 and heads80–89 each.
Slot3's body hits2048 partway through; its head then contributes0 polygons.
All99 stage shadows were registered, including distant actors.

The synchronization guard neutralizes actor visibility while running AI. Native
DropShadowRadHeight/DropShadowScaleXYZ also read that flag, so they registered
shadows which the camera should suppress. New normal image
`local-shadow-visibility-host.nds`, SHA256
`fbb2262d6dbacd6c92e8f585bde99941d587ed8e323bde280f598e91e69abd2d`,
restores only those native flags reads from the saved local visibility. Actor
AI still sees the neutral flags. Native ANDS/early return, shadow geometry,
scale/opacity, original models and level assets remain intact. Both helpers,
offline/disabled/other-actor cases, explicit suppression and the read-hook ABI
pass six isolated ARM checks. Full suite:146 discovered,142 executed,4 obsolete
prefix-only skips. Independent normal rebuild reproduces the hash. Normal
`bob-local-shadow-visibility/` validation passes four-controller entry/movement
and matching input ticks. All four heads are visible. Registered entry shadows
fall from99 to8; entry geometry peaks at1621 polygons and movement at1796,
with no observed overflow on any console. Level/model assets are unchanged.
This is targeted emulator acceptance; broader scenes and physical retest remain.

Input cadence is still similar: the movement checkpoint averages about3.58
VBlanks per outgoing input tick, including cold reads, versus3.57 on aea94.
Do not claim full-speed gameplay or a measured cadence improvement from this
fix. Synchronous asset-read stalls and native network/frame pacing remain open.
The first frontend counted phases0..15 only, missing native NET phase0x15 and
callbacks0x16/0x17. Updated frontend counters cover32 phases; reports also expose
unclassified phase observations. Earlier cadence/geometry counters remain
valid, but those earlier phase histograms are incomplete.

A private planar-quad prototype02a8a8e1 combined80 source strips, saving81
source polygons without moving vertices/UVs. It still overflowed at entry and
had similar input cadence, so it is not included in the normal candidate.
The experimental optimizer and its11 tests are archived under
`planar-quad-experiment-source/`; later guards also exclude translucent/shadow
and alpha-texture lists. The original prototype predates those extra guards.
Do not present it as a rendering fix or transfer its acceptance to production.

`build_download_play.py --diagnostic-render-cost --output OTHER.nds` enables
the optional terrain/body/Yoshi-head cost recorder. It drains the geometry FIFO
before/after native calls, changing scheduling. Use normal images with the
read-only frontend for cadence/performance acceptance. The ROM diagnostic is
only for attributing geometry use and never raises the DS rendering limits.
