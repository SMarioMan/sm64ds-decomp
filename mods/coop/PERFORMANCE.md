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
