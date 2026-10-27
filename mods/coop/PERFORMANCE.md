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
performance work. The targeted BoB cause and fix are documented below.

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

## Rejected native frame clock experiment

Unmodified EU0 retail Adventure/file-A castle measurement records299
consecutive input intervals, all exactly2 SDK VBlanks, over600 observed frames
(`retail-cadence-baseline/retail-adventure-cadence.json`). The offline unpaced
frontend measures emulated cadence, not wall-clock speed. An earlier automated
VS-practice replay is explicitly invalid as an Adventure baseline.

Commit14ab0ad99 contains the isolated optional frame-clock experiment,
SHA256 `afa982ae47982e0bc344e7c50db54c5b71f10b4369b145e22f883b5a4bda87ee`.
It retains elapsed NET time instead of the main loop's second timer reset.
Five actual ARM reset-block/IRQ tests and the full147-test suite passed.
The default image remained byte-identical fbb2262d. The four-console normal
route passes startup, movement, castle entry and BoB entry. But matched BoB
measurements show NO meaningful improvement: median/p95 remain3 VBlanks;
mean including cold reads3.588 versus3.577 for the shadow-fix baseline.
A fresh600-frame steady BoB sample has202 intervals at about3.005 VBlanks;
almost all phase observations fall within main phase4. Castle medians were
already2 on the baseline, so they do not demonstrate improvement either.
The option and its runtime/test code were removed from the current build.
The historical commit and frozen run sources preserve reproducibility.

Main phase4 covers multiple process lists, including both actor Behavior and
Render; it is not a CPU profile of Behavior alone. The updated read-only
frontend additionally records native process phases and actor profile IDs:
phase2 initialization,3 behavior,4 cleanup,5 render,1 scene-tree traversal.
Only process phases2..5 use the current node's owner, with RAM bounds and
profile ID checks against the391-entry native registry. The initial frontend
encoded IDs0..353 with stride354; reports accept that older encoding as well
as the current16-bit phase/profile encoding. Histograms are frame-boundary observations, not call counts
or CPU cycle costs. They preserve the stock core and do not install ROM hooks.
Earlier frontend reports do not contain these additional histograms. Actual
retail Adventure replay with the new observer again records299 intervals all2
VBlanks; its300 observations within main phase4 are all process phase5 (Render).
Normal four-console fbb run `bob-native-process-profile/` and continuation
`bob-native-process-steady/` are now closed. They pass native entry,600 steady
frames, four-console warm movement and fresh guest2 coin. Steady sample has204
intervals averaging3.010 VBlanks; process samples include behavior283,render249,
scene-tree79. Player profile191 is verified from the original overlay descriptor;
its Behavior accounts for204 boundary samples, stage Render for104. Samples
can alias periodic work and do not quantify exclusive CPU time. Warm movement
mean3.628 includes cold stalls. Native func02059650 reads the existing SDK
Timer0 clock without reprogramming it; targeted elapsed-time instrumentation
now supplies an optional elapsed-time profiler described below.

The following fixed24-frame START pulse failed to open course pause despite a
healthy party. The driver now uses the existing menu-readiness/input-echo toggle
helper, already exercised by20 repeated cycles. A live course-return retest is
still required; do not transfer the helper's acceptance to that transition.

The same run exposed a camera-check driver bug: association order0,1,3,2 was
incorrectly treated as console order. Zoom assertions now index synchronized
choices using each console's actual native player slot. Earlier failed reports
are retained. Corrected physical-input zoom/mixed camera checks and20 shared
pause cycles pass on the isolated image. A subsequent guest3 coin route failed
without a pickup, ending above the lower-floor target; a north-approach probe
also failed navigation. Neither grants coin/transition acceptance. That party
is now closed. These checks do not establish normal-image release acceptance.

The controller driver's analog-stick setup also used a fixed24-video-frame
wait. Native CheckInput initializes it over five actual synchronized input
updates; the new isolated ARM test proves that24 SDK VBlanks without input
updates do not advance that delay. The driver now acknowledges release and
waits for native touching/delay readiness before reading its real origin.
It does not require exact calibrated pixel coordinates. Live confirmation is
in progress under `native-input-readiness-regression/`; loading stalls and
prior navigation failures remain open until those checks pass.

The acknowledged pause now opens and the four replicas'15 Goomba states match.
The next exit touch still arrived while the native opening cooldown was10;
actual retail PS_Update ignores touch while that counter is nonzero. The
course-return driver now also waits for PS/draw state3 and zero cooldown/menu
animation, acknowledges release, and holds the fourth-row touch until the
native action is accepted. Two isolated ARM menu checks prove rejection while
cooling down and ready acceptance into native action19. The prior party closed;
fresh `native-menu-readiness-regression/` live exit/reentry is pending.


## Optional animation cache and elapsed-time profiler

These experiments are disabled in the normal build. Add
`--experimental-animation-cache --output /your/path/cache-host.nds` to the
normal Download Play build command to evaluate the cache. Add
`--diagnostic-player-cost` to that separate build to measure costs. The latter
cannot be combined with `--diagnostic-render-cost`, whose FIFO drains alter
scheduling. Neither option changes the stock melonDS core. Their memory and
measurement overhead mean diagnostic cadence is not release acceptance.

The raw animation cache holds private immutable copies of verified compressed
`player/*.bca` members in ROOT: at most32 entries,64KB payload and16KB/member.
It copies hits into the caller's existing buffer, preserves native file cursor,
command arguments, WaitAsync and Close semantics, and never shares a mutable
animation object. Reads must be complete synchronous main-thread reads of a
verified common-archive member with healthy native state. Loaded but suspended
physical-ROM archives are valid for wireless guests; unloaded/cancelling/
suspending archives and pending native errors bypass the cache.

Cache storage is expendable. Allocation pressure evicts least-recently-used
copies, ROOT growth and capacity queries reclaim copies before native decisions,
and stage/connection teardown flushes them. The ROOT owner is explicit even
while GAME is the default heap. Optional allocation failure falls back to
unchanged native I/O. Sixteen isolated ARM checks cover native heaps, copying,
seek/wait/close, exact-read eligibility, pressure/growth/query safety, cache
limits, archive suspension, failures and teardown. Only the physical SDK read
completion is adapted from the supplied ROM bytes in those isolated tests.
All-stage memory, extended wireless and physical acceptance remain open.

Private image274084aaac11c165f7d9f8b67297e74ffdcb241ba9616c4d0a5f85368c641a8e
uses the cache without elapsed instrumentation. Its normal four-console route
reaches BoB; steady play and warm movement pass same-input-tick checks. All four
consoles have51 hits/18 misses after steady play and55 hits/18 misses after
warm movement (10808 cached bytes each). Warm host input cadence has252
intervals, mean3.000 VBlanks, maximum4, versus normal fbb warm mean3.628 and
maximum34 on the recorded comparison route. These are separate controller runs,
not physical measurements. Steady cadence remains205 intervals, mean2.990,
predominantly3 VBlanks: the cache reduces observed warm read hitches but does
not establish full-speed gameplay. The earlier pressure-safe ec9a10be prototype
incorrectly excluded suspended guest archives and cached only on the host;
its results must not be reported as guest-cache acceptance.

The elapsed profiler reads retail's already-initialized SDK Timer0 via
func02059650; it never initializes or reprograms the timer. Four spans cover
actual Player Behavior, body rendering, Yoshi head rendering and whole Stage
Render. Sixteen buckets separate active and paused spans, including stage subspans. Rows record completed
count,64-bit total, maximum and minimum ticks with an update sequence so RAM
observers can skip incomplete records. Counters reset on stage identity change;
spans crossing shared input ticks, loading or stage changes are discarded.
SDK ticks are approximately33.514MHz/64 and INCLUDE interrupt, filesystem and
GPU waits. They are not exclusive CPU cycles. The wrappers preserve native
arguments/returns, call the original model render directly and never drain
geometry. `campaign.snapshot` decodes saved RAM to `*-runtime.json`, including
milliseconds per span. Eight isolated ARM tests cover ABI, actual before/after
scope, pause buckets, low32 wrap,64-bit carry, stage reset and readiness/span
rejection. The full combined suite passes172 discovered/168 executed tests with4 obsolete
prefix-only skips. Independent normal builds still reproduce fbb2262d.
Live cost attribution on the original four-span image is recorded below.


The completed274084aa continuation also passes a fresh guest2 shared coin,
native course exit and reentry. Paired measurements at the returned BoB scene
have205 active intervals all3 VBlanks and304 paused intervals averaging2.013
VBlanks, on every console. Active gameplay work is a concrete next lead, but
this comparison alone cannot separate collision, animation, rendering and
synchronization costs. It is not proof of exclusive CPU saturation.


## Steady-play costs and conservative cylinder-pair experiment

Image dc04637cff4017ea4c9ad313de48f0821251e7e78da8f5a25a625ea9165ddbad
passes the native four-console castle/BoB route, steady600 frames, warm movement
on all consoles, and a600-frame pause check. The party is CLOSED. Subtracting
`before-steady-runtime.json` from `steady-bob-runtime.json` avoids mixing cold
asset reads into steady averages. Per stage-render call, Player Behavior totals
4.23–4.27ms, bodies1.81ms, Yoshi heads0.93ms and whole Stage Render11.37–11.52ms.
Stage Render includes collision processing and other work as well as geometry;
these categories are elapsed spans and must not be added as exclusive costs.
Steady input intervals remain3 VBlanks. Paused stage render averages1.67–1.69ms
and input intervals are2 VBlanks. The split profiler now adds terrain opaque,
shadows, terrain transparent and actor-collision spans (16 active/pause buckets).

An actual unmodified-retail Adventure/file-A replay now reaches BoB through
normal castle doors/painting: `retail-adventure-bob-cadence/` PASSES. Its600-frame
steady capture records300 input intervals,599 VBlanks, maximum2. This establishes
an emulated same-level retail target near2 VBlanks. The earlier attempt at
`retail-bob-cadence-baseline/` used a legacy command script which selects VS
practice; it failed to leave its locked castle and is not an Adventure baseline.
Always verify native story mode0, level1 and offline NET0 after file selection.

The optional `--experimental-collision-broadphase --output /your/path/test.nds`
changes only the cylinder pair walk's exact horizontal-distance callsite. After
the native flags/owner/height tests, a separated X or Z axis can prove that
cylinders do not overlap. Such a pair returns its positive radius sum so the
unchanged native overlap test rejects it. Every possible overlapping pair
continues through the original horizontal norm, SDK square root, pushback and
notifications. Pair order, collision masks and original game geometry remain.

The guard is restricted to playing co-op NET4 and nonnegative radii and absolute
axis coordinates at most0x1fffffff. This domain keeps the original SDK square
root's shifted64-bit input and signed result within range. Unusual/overflow
cases and offline/disabled/loading/disconnected states delegate unchanged.
The builder validates the native working-register and radius-overlap block,
and its small ARM adapter preserves stack alignment and saved registers.
Six isolated ARM checks execute actual native vector/sqrt/list code against a
hardware SQRT result adapter, including randomized pairs, touching/coincident/
diagonal cases, overflow/offline delegation and complete96-node list/contact
state parity. The initial native test removes2297 of2399 square roots, but this
is an isolated call-count result, not a hardware timing or gameplay-speed claim.
Live cadence and broader campaign/physical acceptance remain pending. This
optimization is disabled by default and is not a finished performance fix.


The first broadphase+split-profiler live imagebbe4e146 PASSES native startup and
independent movement, then loses wireless before the first castle waypoint.
The retained capture has errors0x101, NET0/radio0 on every console, tick6705.
Native bit1 is set when the input-exchange loop exhausts its attempts; this is
not a captured first-cause checksum diagnosis. The party is closed. There is
NO course-speed result for this optimization. A cache+split-profiler control
without the collision optimization (6339b8c0) is running to distinguish the
change from instrumentation or existing intermittent wireless loss. Keep the
optimization disabled pending repeat/control, speed and gameplay acceptance.


The6339b8c0 control PASSES native castle/BoB entry, steady600 frames, warm
movement on all four consoles and paused600 frames. Snapshot deltas give
actor-collision9.44–9.67ms/call, opaque terrain0.98–1.04ms and shadows0.48–0.55ms.
This identifies collision as the dominant measured stage-render cost. Steady
cadence is still3 VBlanks; paused2. A single passing control does not identify
the previous wireless failure's cause.

The initial C++ guard increased isolated ARM instruction count295796->326287,
despite sqrt2399->102. Its replacement is a leaf ARM routine at the same norm
callsite: caller-saved scratch registers match the original norm ABI, no saved
registers or stack words change, and rejection needs no helper call. Native
contact state still matches; isolated instruction count is299060 and sqrt102.
Instruction counts omit hardware wait cycles; speed improvement must be measured.
New image56ac474fdb57549526712d9b4f551e87934b41e0721aa783c848164ef8259ded is
running the normal four-console route. Six guard tests, eight timing tests and
full suite179 discovered/175 executed/4 obsolete prefix skips pass. Independent
all-disabled build reproduces fbb2262d. This experiment remains disabled by
default pending live speed, repeatability and gameplay acceptance.


The56ac474f leaf run PASSES normal four-console startup, castle/BoB entry,
steady600 frames, warm movement on all four consoles and paused600 frames.
It does not provide a useful steady-speed gain: collision averages9.33–9.55ms
versus control9.44–9.67ms; steady206 input intervals include205 at3 VBlanks and
one at4. Keep it disabled. Its party is retained paused for further inspection.

A read-only captured-list census finds160 native colliders,12720 pairs and2269
compatible-mask pairs.2263 of those compatible pairs are already separated on
X or Z;424 survive the height test. All nodes use the three verified pure
native position/owner getter implementations. The norm guard therefore acts
late in the expensive walk. A private isolated candidate-plan replay against
actual native Process preserves every collider's contact/list state while
considering80 spatial candidates instead of12720 pairs. It executes6332 native
instructions versus253813, and5 square roots versus424. These counts exclude
plan construction, ARM hook overhead and physical hardware waits; the replay
is not a working ROM implementation or evidence of gameplay speed. Any native
notification invalidates that frozen plan before calling into player code.
Next work is a bounded candidate plan preserving original pair order, with
safe callback invalidation, memory-pressure fallback and native parity tests.


## Ordered spatial candidates (optional, not a release)

Use `--experimental-animation-cache --experimental-collision-plan` with a
separate `--output` to evaluate this approach. It cannot be combined with the
older `--experimental-collision-broadphase` leaf guard. Add
`--diagnostic-player-cost` only for elapsed-time instrumentation. The planner
uses original native pair order, masks, distance arithmetic and responses;
only provably separated pairs are omitted. Three pure native position/owner
getter pairs are whitelisted. Unknown types, unsafe arithmetic domains, short
lists, capacity, dense preparation windows or insufficient memory retain the
native walk. Preparation handles at most192 nodes and1024 sweep comparisons;
it performs no I/O or game callbacks under its bounded IRQ guard.

Storage uses an optional nonfatal ROOT allocation with an explicit owner.
ROOT allocation pressure, capacity queries and reallocation reclaim it before
native decisions. Candidate use is suspended during native notifications. A
notification retains the plan only after fresh remaining-list/order, geometry
and original outer-position-reference validation; callback allocations reclaim
it before native allocator decisions. Stage/resource cleanup and session reset
also release it. Direct
expanding-heap allocation/reallocation forwarders are checked against complete
retail signatures; other heaps retain native behavior. IRQ guards protect
workspace reads and ROOT allocation/eviction from SDK-thread preemption.

The first implementation e05b6262de4265655965bad75272f2eb51ebaa262f98ac6932f01e1ca54b6e33
passes native four-console startup/castle/BoB, steady/warm/paused checks, a guest2
shared coin and course exit/reentry. Steady collision cost falls to4.78–5.00ms
from9.44–9.67ms; whole stage render falls to6.70–6.84ms. However cadence remains
near3 VBlanks per input tick, so this is not full-speed acceptance. During the
steady sample every console prepares207–208 plans, with no pressure eviction,
preparation abort or native notification; repeated construction is a next lead.
The party is closed.

The reuse build retains a pressure-reclaimable conservative envelope plan.
Before each frame it checks the FRESH native list/order, getter implementations,
stage identity, arithmetic domain and every actual cylinder's X/Z bounds.
Reuse is allowed only while all actual bounds remain inside the saved32-unit
margins. Teleports, radius growth, changed lists, callbacks or memory pressure
invalidate it immediately. It does not assume a frame count or movement speed.
Twenty-one isolated ARM checks cover whole native contact/list parity across
randomized getters/masks/owners, touching/coincident/zero-radius cases, moving
callbacks, real allocation pressure/growth, IRQ restoration, dense/capacity
fallback, cross-frame reuse, teleports, reordered nodes and native cleanup.
Hardware SQRT/DIV results and final game notification are isolated adapters;
no live emulator memory or wireless packets are replaced.

The earlier diagnostic image cd53ad2aa83bacf78733115aa547c794bfca9e81cc379a5798255e13ac7af7e0
completed the normal four-console route. Its full suite:200 discovered,190 executed,
10 skips (six mutually exclusive leaf-guard tests and four obsolete prefix
checks). Independent disabled builds reproduce normal fbb2262d and cache-only
274084aa. Wider stages/party sizes and physical acceptance remain
pending. Approval review could not execute the latest commit/push because of
its usage limit; current spatial-plan changes are local, after published bc1c0c564.


The fixed32-unit reuse build cd53ad2a PASSES four-console movement/pause and a
fresh guest2 coin, course exit and reentry. Its steady cadence improves only
partially:227 intervals/615 VBlanks (66 intervals at2,161 at3) on every console.
A read-only32-snapshot investigation after reentry shows45 rebuilds and4 reuses,
with no native notification or pressure release. Thirty compared rebuild samples
retain the same node order; the main cause is geometry leaving small envelopes.
Profiles208 and220 move about59 and25 units/update in the captured scene, and
native actor horizontal/X/Z velocity fields confirm this. No order-remapping
change was introduced based on the initial hypothesis.

The current motion-envelope experiment scales bounds only for moving owners:
max(32 units,32 times current horizontal/X/Z speed), capped at2048 units. These
are sizing hints, not limits or predictions trusted by collision processing.
Every fresh actual bound is still validated each frame; abrupt acceleration,
reversals, owner changes and teleports cannot bypass validation. Static position
colliders retain the base margin. Signed extremes are clamped before multiplying.
On the captured scene the candidate count changes only170->183 despite improving
coverage for the fast movers. Two additional native tests cover selective bounds
and extreme signed velocity without changing native game velocity fields.

Motion-envelope image607c46b11f05b31d49523a691fb6b9e2a649a8ce408cb239f61ba92c34c2e624
PASSES normal four-console castle/BoB entry, steady/warm movement, shared pause,
guest2 coin and native course exit/reentry. Its steady sample has303 intervals:
286 at2 VBlanks,16 at3 and one boundary interval at1. Collision averages
2.16–2.37ms; stage rendering4.06–4.22ms. Warm movement still has117 intervals
at3 and196 at2, with115 full builds and104 native notifications on the host.
That remaining movement cost motivates validating plans after callbacks and
refreshing them incrementally. This party is closed. Its23 native tests and
202-discovered/192-executed suite pass; normal fbb2262d, cache-only274084aa and
the607c image independently reproduce.

The next experimental image1f749f4719043105702446c69f710d0e2fd6027b700ed3f2b073c06459680923
retains valid plans after callbacks and refreshes unchanged node lists in place.
Every callback still revalidates the remaining suffix and original position
reference. All ROOT allocations inside callbacks reclaim optional plan storage
before calling the native allocator, even with ample free memory. Refresh uses
fresh geometry and bounded insertion sorting (256 shifts,1024 sweep comparisons).
Exceeded budgets discard the plan and run native collision for that frame;
changed lists use full construction. No frame count or user timing establishes
validity. Twenty-nine isolated ARM tests pass, including callback mutation,
allocation, native contacts, in-place refresh and sort-budget recovery. Fresh
four-console measurements and physical acceptance are pending. The full suite
passes208 discovered/198 executed tests, with10 documented skips. These experiments remain disabled in the normal build.

The elapsed profiler originally selected its pause bucket from the native menu
state0209f1ec==3. Captured active and paused BoB scenes both have that value;
its historical `paused` labels therefore cannot separate the two. Active-only
before/after deltas above remain valid. Current source reads the actual byte
pause flag0209f2c4 instead; isolated checks initialize the normal menu state3
and verify separate unpaused/paused buckets. The diagnostic stage-matrix build
uses the corrected profiler. Earlier1f749 measurements still require deltas
between explicitly active or explicitly paused captures, not bucket labels.

Image1f749 PASSES normal four-console castle/BoB entry,600 steady frames,
warm movement on every controller and600 paused frames. In steady play all
consoles record303 intervals:287 at2 VBlanks,15 at3 and one boundary at1.
Warm movement records335 intervals at2 and22 at3 (host357 intervals; guests
also include one boundary at1). This improves the previous607c warm sample's
117 slow intervals out of313, but still does not establish full-speed play.
Steady collision averages2.09–2.31ms and stage rendering3.99–4.14ms. Movement
collision averages2.18–2.39ms and stage rendering4.00–4.11ms. The host records
five full builds,16 incremental refreshes,338 reuses and104 notifications; all
104 callbacks validate, with no callback allocation, pressure release, abort or
native fallback. Four warm animation reads hit the cache on every console,
with zero misses. Guest2 coin and native course exit/reentry also PASS. Its party is closed.
Independent pre-profiler-correction builds reproduce normal fbb2262d, cache-only
274084aa and1f749 exactly. The normal ROM has no optional timing instrumentation.

The corrected stage-matrix diagnostic image is54c82a1fbd20e58c252cd3ee154eb2be8061ea490f28b8f8dbe9286cc154b8c0.
Its208-test suite passes198 tests with10 documented skips. Diagnostic file-read
tracing reads the DS shared page at027ff000; the private Unicorn fixture now
maps its captured4MB-RAM mirror so those reads execute correctly. The earlier
matrix test failure was15 unmapped-read exceptions in that isolated harness;
no game allocation or wireless failure was suppressed.

Unprofiled normal optional image64dc499bd9af263add4d6c32b20acab71ebf4d62152554e69493a7002fa1e6d2
has been built but not fully accepted. Unprofiled cycle diagnostic image
f4ade5d327917bd20b53be9fa58290eaf31a63b2d5e7ddd6c8adbce66e2d8976
is running a fresh four-console session: native castle readiness, ordinary
BoB entrance, then entrance/short-motion performance and compatibility sampling
through diagnostic native stage transitions. This removes elapsed timing
instrumentation from cadence measurements. It is not all-level exploration,
earned progression, physical acceptance or a full-speed release claim.

The unprofiled f4ade5d3 sweep PASSES entrance/short-motion synchronization,
controls and shared pause on levels6–11, then was deliberately stopped for a
cache-retention comparison. It is NOT a completed50-stage sweep. Its first
controller script failed by using the interior route while in the grounds;
the corrected run uses a labeled diagnostic transition into interior2, then
the normal painting route into BoB. BoB steady:282 intervals at2,13 at3, one
boundary at1. Movement:342 at2,16 at3, one boundary at1. Level7 steady has
300–301 at2 and three at3, but first movement includes one33-VBlank hitch.
The final native file-read trace identifies2219 bytes at ROM offset2158424:
zero VBlanks on the host and31 on each guest. The raw cache has one miss and
store during that sample after its per-stage flush. This is a cold first-motion
sample; calling the driver phase `movement` does not establish warmed assets.

Optional `--experimental-persistent-animation-cache` now preserves private
immutable animation bytes across live stage/ENTRY cleanup, while releasing
collision plans before native stage cleanup. The ROOT heap is created by
SetupRootHeap and lives for the process; its pointer is unchanged in the captured
transitions. Copies are keyed by validated immutable cartridge extents, not
model pointers or a stage heap. Native ROOT pressure, capacity queries and growth
retain their eviction policy. Offline/disconnected/ended/title sessions flush
bytes; new matches and planned session termination flush explicitly. It does
not increase the64KB payload or32-entry limits and does not suppress file errors.

Unprofiled persistent cycle image
ef284c955abef54446d2bf668f0e255f68231a59eb8b21197c0ad50d1b86aa93
is in fresh four-console testing. All210 discovered/200 executed tests pass with
ten documented skips in a fully instrumented build; without elapsed profiling,
192 execute and18 skip. Two new ARM checks cover reuse of exact bytes/native
cursor across transitions and release for disabled/offline/disconnected/title/
ended sessions. Native stage-cleanup ABI and collision-plan reclamation still
pass. Independent builds reproduce fbb2262d,274084aa,64dc499b and ef284c95;
this retention option remains disabled by default pending live speed and memory
acceptance. Duplicate verification ROM copies were removed to free space after
hashing; reports/logs and unique source images are retained.

## Bounded alternate-axis probe and cheap native fallback

The ef284c95 four-console diagnostic sweep passes entrance/short-motion
controls, synchronization and shared pause on levels6–23. Level24 fails because
the controller route kills a player; retain the failure, not a full-sweep pass.
Its attempted stage-cleanup cache retention does NOT remove the traced31-VBlank
guest read or33-VBlank movement hitch. Native ROOT queries/pressure still evict
private copies. It remains an opt-in investigation, not a demonstrated fix.

Level14 is a separate steady-speed problem:97 aborted preparations/native
fallbacks in the sampled steady delta, with many4/5-VBlank intervals. A private
RAM checkpoint contains a fully populated, freed187-node construction block
whose stage UID matches the current scene. Its X window count is1317 and Z965;
X exceeds1024 while Z fits. Choosing the larger span alone regresses existing
BoB native tests and was rejected. The current algorithm preserves the original
first choice, then counts exact one-dimensional overlap windows using a bounded
min-heap of interval ends. If needed it probes the other axis before performing
at most1024 actual candidate comparisons. Both overly dense axes retain native
processing. Scratch reuses the unpublished bitmap; no extra allocation, I/O or
game callback occurs under the IRQ guard. The min-heap work is bounded by192 nodes.

The assembly read hook now checks for a null/evicted plan before calling the
C++ pair selector. Native fallback no longer pays that wrapper/IRQ call on every
pair. The protected selector still rechecks any later pressure eviction before
using a pointer. A native-contact regression verifies no C++ selector calls in
disabled fallback. A synthetic near-square layout reproduces the rejected X
window and verifies successful Z planning with native contact parity. All31
collision cases pass, along with the full213-discovered/203-executed suite and
ten documented skips (`collision-bounded-axis-all-tests.log`).

An isolated replay reconstructs the187-node captured list in private Unicorn
memory only. Native contact/list state and notification order match exactly.
The new full construction considers320 candidates and uses four square roots
versus346 natively; however it executes295625 instructions versus269184,
INCLUDING construction and hooks. This is not a cold-frame CPU improvement;
reuse and avoiding repeated fallback are essential. No live RAM, packets or
save states are changed, and instruction counts are not hardware timing.

Diagnostic-only cache-eviction records now distinguish capacity/total-memory
queries, in-place growth, scene cleanup and session termination. A three-system
native run confirms a ROOT capacity query discards30828 bytes/ten entries at
level16. Native allocation decisions remain unchanged. Three-system image
2f28eca295181c0a0486f788ed01591666d1ce74e695293b7e333cf72a1d6b1b passes
native Download Play, direct diagnostic levels14–16, controls/shared pause,
600 steady level16 frames, real course exit, restored castle controls, and
Save & Quit with unchanged other files. The diagnostic character fixture is
Mario/Luigi/Wario, not the normal all-Yoshi campaign start. Cold animation hitches
remain in these observations; do not claim full-speed or campaign acceptance.

Independent rebuilds reproduce normal fbb2262d, cache-only274084aa and the2f28
three-system image. The new normal four-console optional spatial image is
3413b38922738c64c2b5c9c1ac71a1f016d2cdaa2b9baddd560a0206cb94b418.
Its ordinary castle/BoB run passes four controllers, shared pause, guest2 coin
pickup and native course exit/reentry. Steady host cadence has282 intervals at2,
15 at3 and two at4 VBlanks. Warm movement has339 at2 and22 at3. These are
emulator observations, not full-speed hardware acceptance. Reports are in
`bounded-axis-normal-profile/` and `bounded-axis-normal-gameplay-regression/`.
All experiments remain disabled in the default ROM.

## Updating only escaped collision envelopes

The optional planner can now refresh just the nodes that escape their cached
envelopes. It first checks the complete fresh native list and all actual bounds.
At most eight changed nodes and1024 changed-node/other-node comparisons use
the small refresh; larger changes take the existing full refresh. Each changed
envelope updates its sorted position and symmetric candidate bits in native
list order. Total sort shifts remain bounded at256. Candidate totals above1024
or unsafe geometry discard the private plan before native processing resumes.
This path allocates no scratch memory and changes no native object fields.

Thirty-five isolated collision checks pass, including exact bitmap/contact
parity for eight moving nodes, refresh with ROOT scratch unavailable, node/pair
budget fallback, and recovery after discarding partially updated private data.
The fully instrumented suite passes217 discovered/207 executed tests with ten
documented skips (`collision-edge-budget-all-tests-v2.log`). The builder now
limits linked code/data to36KiB and separately enforces the loader's64KiB limit
after adding trampolines and immutable tables. This changes no reserved size;
the loader allocates the actual module length.

The first four-node version (106ba5d5) passes ordinary four-console BoB controls,
600 steady frames, warm movement and shared pause. Host collision elapsed cost
is2.36ms steady/2.42ms moving; Stage Render is4.21ms/4.14ms. Warm cadence has345
intervals at2 VBlanks and17 at3, with15 small refreshes and nine full refreshes.
Different runs have different object trajectories, so this is a modest observed
gain, not a controlled causal FPS comparison or full-speed claim. A private
160-node replay requires21532 instructions for one escaped node versus63624
for the full refresh including its rejected small-refresh probe; bitmaps match.
The comparison changes cached envelopes only in isolated Unicorn memory, never
the live game. It is not a hardware CPU measurement.

The bounded eight-node elapsed-profile image is
`47a149ce5c27b1a918e33c42762e6d9d0e44aefaef2b0e5e1de2dc063331a9fd`.
Fresh wireless measurements and course regression are tracked separately in
`edge-budget-cost-profile/` and `edge-budget-gameplay-regression/`.
The elapsed profile PASSES600 steady frames, all four controllers and600 paused
frames. Host steady cadence has272 intervals at2 VBlanks,21 at3, two at4 and one
boundary at1; warm movement has339 at2,18 at3 and one at4. Collision elapsed
time is2.40ms steady/2.45ms moving and Stage Render4.25ms/4.17ms. Fifteen of23
warm refreshes use the small path;104 callbacks validate successfully with no
pressure releases or aborted plans. This run does not establish a further
cadence gain over the four-node version. Its separate private replay uses21539
instructions versus63972 for full refresh including the rejected probe, with
identical candidate bits (`edge-budget-native-cost-replay.json`).
The separate controller-only regression also PASSES guest2 shared coin pickup,
native course exit with synchronized castle controls, and course reentry. The
party was then closed. These checks use the exact47a149ce elapsed-profile ROM;
they are not full-campaign or physical-hardware acceptance.

The unprofiled optional four-console image is
`870b7dd1ea6066df6d51c5e384bc77dee469eeaf2d6bef97db795e3870e8c7c0`;
it is built but has not been played. Independent default fbb2262d and cache-only
274084aa rebuilds are byte-identical. Optional changes remain disabled in both.

An unmodified retail four-console Download Play reference also passes at
`retail-wireless-vs-cadence-mode1/`. Its lighter native VS level51 has293 steady
intervals at2 VBlanks, two at3 and two at4. Its movement sample has150 complete
intervals at2. This establishes a stock wireless reference with occasional
jitter; it is not a matched campaign-level CPU comparison.

Offline parsing of the captured level7 WFS state confirms512-byte parent
packets (498 payload bytes) on all four systems. The traced2219-byte animation
requires at least five data packets plus protocol exchanges. This bounds the
wireless work; it does not establish the cause of every one of the31 elapsed
VBlanks. Native cache eviction and cold-read latency remain unresolved.

A private allocator prototype tests an alternative to query-triggered eviction:
merge the real free extents with the exact padded extents of owned cache blocks,
then compute the capacity that native freeing would expose. Across24 fragmented
layouts, all192 maximum/total queries match actually freeing those blocks in
native ARM allocator code, including both alignment directions. The prototype
does not change live memory or implement a game policy. A production experiment
would need bounded validated traversal, atomic ownership checks, immediate native
fallback on any uncertainty, and existing allocation/growth reclamation. See
`virtual-cache-capacity-probe.json`; this is a next investigation, not a hitch fix.

## Guarded virtual capacity queries

`--experimental-lazy-animation-eviction` implements the query-retention
experiment and requires `--experimental-animation-cache`. It validates the ROOT
expanding allocator, cached block ownership/headers/padding and used-list
membership, then merges the native free list with those exact cached extents.
It returns the same largest/total capacity as actually releasing all cache
blocks, including headers recovered through native coalescing. It changes no
heap lists or bytes. Traversal is bounded at1024 used nodes and256 free nodes;
uncertainty retains the original flush/query path. The calculation holds IRQs
and performs no allocation, file I/O or game callbacks. Collision plans still
release before queries. Actual allocation pressure, in-place growth and session
cleanup retain their reclamation policies. It reserves no additional payload.

Twenty-four animation-cache checks and the complete222-discovered/212-executed
suite PASS, with ten documented skips (`lazy-animation-all-native-tests-v2.log`).
New native ARM checks compare predicted results to actual frees across eight
fragmented/padded layouts and all32 cached entries; exercise allocation after a
virtual query with no free capacity; reject uncertain ownership, counters and
headers without heap writes; and verify real used/free traversal-budget fallback.
The initial no-write test incorrectly included the private C++ stack. Its corrected
comparison covers the actual ROOT allocator, list sentinels and heap extent.

Private instruction samples with553–584 used nodes cost27485 instructions for
one entry,49321 for12 and68221 for32. This is bounded extra query work, not a
steady-frame or hardware timing result. Successful-query/fallback counters are
in the build report and read-only runtime snapshots. They permit checking whether
query retention helps in practice without guessing from the absence of eviction.

Four-console elapsed-profile image
`d320a980070602733dc38bdc439bc18d48dc22b58d1862467ca81458ff7696ae`
PASSES all-Yoshi castle/painting entry followed by short diagnostic stage
checks6–16 at `lazy-eviction-performance/`: controls, synchronization, steady/warm
motion and shared pause. The separate `lazy-eviction-stage16-return-save/` also
PASSES600 steady16 frames, real course return, restored castle controls and
Save & Quit on all four systems, with other files unchanged. The party is CLOSED.
These are compatibility checks, not earned campaign/boss completion. Each console records four exact
virtual queries/no fallback by7, retaining14 entries/24052 bytes across the
transition. Its first movement adds four cache hits with no new miss or traced
physical read:163 intervals at2 VBlanks, one at3. The old level7 route had a
33-VBlank movement hitch from Y_walk.bca. This is a targeted observation on one
route, not proof that every cold hitch is fixed. Initial stage6 entry still has
a7430-byte Y_wait.bca guest read taking41 VBlanks. Cold reads remain unresolved.
The earlier traced2219-byte/31-VBlank read is specifically
`data/player/Y_walk.bca`, identified from the original common NARC extents.
Default fbb2262d and cache-only274084aa independently reproduce byte-for-byte.
No new performance option is enabled in those images.


## Common-archive loading experiment and remaining bottlenecks

`--experimental-stream-common-archive` requires animation caching and avoids
new whole mounts of archive0 during live co-op. Existing mounted sources and
owners remain intact; other archives/offline/ended sessions retain native policy.
The existing verified unmounted-NARC views load the original requested member
through the normal copying/decompression paths. All ROM files and extents remain
present. A native prologue audit guards the new LoadArchive trampoline. The
counter records skipped mount requests; multiplying it by archive size would
NOT measure actual bytes saved because a normal mounted source serves many calls.

The common NARC is321224 bytes, of which285814 are player assets. This makes
on-demand loading worth comparing against the whole mount for an all-Yoshi party.
Instrumented image474f41cbbb012da123228ea2a654b201d979e04b75e1345635c7eedfdbd8bea2
PASSES225 discovered/215 executed tests, ten documented skips
(`stream-common-all-native-tests.log`), including original walk bytes without
container reservation, preservation of mounted ownership and offline/other-archive
native behavior. It is not yet played; no loading-speed improvement is claimed.

The d320 full6–16 sweep still has movement hitches in9,10,12 and13. At9 the
repeated29–31-VBlank read is the direct NitroFS player animation
`data/player/paddle_end.bca` (1011 bytes, ROM7021840), outside the current
common-NARC-only cache eligibility. There are154 direct player BCA files, all
compressed and within the16KiB member limit. Extending the verified player-file
index is a separate next fix. At13 another Y_walk read takes31 VBlanks after
memory pressure has reclaimed its bytes; query retention alone cannot solve it.

Level14 also remains slow: host collision6.68ms steady/7.23ms moving and Stage
Render9.91ms/10.81ms, with many3-VBlank intervals. A retained coherent last-frame
list has194 nodes, exceeding the192 cap. Private native-code replay with only a
256-node cap still rejects it: X has1398 windows, Z1041, both above1024 despite
only327 true two-dimensional envelope candidates. No invalid geometry was found.
Do not blindly raise just the cap or claim the existing alternate-axis fix solves
this four-Yoshi case. Consider separately bounded window work/candidate totals,
with native contact/order/heap checks and live speed evidence before promotion.
The live game was never modified; `stage14-node-cap-probe.json` records the result.

A matched three-stage loading comparison is starting with d320 control. First
attempt `stream-common-control-matrix/` FAILED because the frontend rejected an
out-of-range diagnostic read of027ffc3c; it is a harness error, not a game pass or
failure. The corrected controller reads physical RAM mirror023ffc3c in
`stream-common-control-v2-matrix/` / `stream-common-control-v2-performance/`.
Its transition totals include real resume/chord input and30-frame arrival polling.
Compare the matching candidate only after closing this party and verifying exit.
