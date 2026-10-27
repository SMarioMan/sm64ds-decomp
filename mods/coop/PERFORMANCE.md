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

## Latest stage-loading and first-use results

Candidate `105a389d43dcf763a3616a0650380aac129990775f512cfc02d0dc43cf66bcc8`
combines the optional loading indicator with fourteen preloaded Yoshi poses.
The full native suite passes296 discovered tests (286 executed,10 skipped).
The previous nine-pose5bf build already passes normal four-Yoshi6–16, course
return and four-system Save & Quit with no new physical gameplay reads in any
steady sample. It still reads three swimming poses during stage9 movement.
Adding paddle1/paddle2/paddle-end/swim-in/swim-wait to loading removes those
movement reads on105a. All exact original file bytes are retained; cache entry
and byte budgets are unchanged. Broader actions,17–51 and physical speed
acceptance remain open;6/13/14/16 still show intervals above two VBlanks.

The105a party PASSES6–16,600 more steady16 frames, native course return
and four-system Save & Quit. Actual frontend exit is verified. Every steady
and short movement sample in6–16 has zero new physical gameplay reads on
all four consoles. Host steady14 still has717 two-VBlank,126 three-VBlank
and one six-VBlank interval (plus a boundary one-VBlank sample), so removing
IO does not finish the full-speed requirement.

The loading indicator now has actual four-console screenshot evidence: custom
LOADING glyphs and two distinct spinner phases appear during each observed
transition. It releases its VRAM/OAM/IRQ leases at playable entry with zero
ownership faults. A first prototype passed ownership checks but drew black:
the native fade targets OBJ with effective coefficient16, although reading
write-only BLDY returns zero. Read-only GPU-state captures confirmed that cause.
The lease excludes OBJ from the native blend targets, clears window/forced-blank
bits temporarily, and redraws after the original VBlank handler and immediately
on lease acquisition. Thirteen isolated ARM cases cover these visibility rules
and native graphics restoration. This covers stage initialization, not initial
firmware/Download Station/menu phases, and still needs hardware visual testing.
Screenshot sampling adds test overhead; its load times are not matched speed
benchmarks. Evidence: `loading-ui-scanout-{matrix,performance}/` and
`loading-ui-scanout-all-native-tests.log` in the private runtime directory.

The separate same-source LZ-window control measures actual four-console load
SDK VBlanks off→on:1→2 **2733→1500**,6→7 **5139→4304**,
7→8 **4898→4095**. Off image8cbf93be and on image167a are source-matched
(the on proof rebuild is byte-identical). This is one pair, includes input and
polling, and is emulated time; physical and broader loading acceptance remain.

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


## Withdrawn common-archive loading experiment and remaining bottlenecks

The former `--experimental-stream-common-archive` option skipped new whole
mounts of archive0 during live co-op. It has been removed after live failure. Existing mounted sources and
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
native behavior. The live candidate passes6, then FAILS6→7 with native Crash() on all three
guests. Its first measured1→2 transition is2905 SDK VBlanks versus2722 for
the matched control (about7% slower, including resume/chord/poll overhead).
Native mount/unit checks did not establish correctness of the full loading path.
The hook, build option and mount-policy tests are withdrawn; original mounting
remains. Failed images/logs/captures are retained, not counted as passes.

The d320 full6–16 sweep still has movement hitches in9,10,12 and13. At9 the
repeated29–31-VBlank read is the direct NitroFS player animation
`data/player/paddle_end.bca` (1011 bytes, ROM7021840), outside the current
common-NARC-only cache eligibility. There are154 direct player BCA files, all
compressed and within the16KiB member limit. The exact direct-file index is implemented in the following section. At13 another Y_walk read takes31 VBlanks after
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

The matched d320 control PASSES short6–8 checks and measures1→2/6→7/7→8
transitions at2722/5240/4826 SDK VBlanks on every console. Its party is CLOSED. First
attempt `stream-common-control-matrix/` FAILED because the frontend rejected an
out-of-range diagnostic read of027ffc3c; it is a harness error, not a game pass or
failure. The corrected controller reads physical RAM mirror023ffc3c in
`stream-common-control-v2-matrix/` / `stream-common-control-v2-performance/`.
Its transition totals include real resume/chord input and30-frame arrival polling.
Compare the matching candidate only after closing this party and verifying exit.


## Direct player animation reads

The cache now recognizes154 original direct NitroFS `data/player/*.bca` files,
in addition to the common-NARC player members. The builder verifies original FAT
extents and compressed prefixes, then emits a sorted physical-offset/length index.
Reads still require the full exact file view, main thread, synchronous mode and
native ready/error/cursor checks. Owned copies, native SeekFile completion and
pressure/growth/session reclamation are unchanged; no partial data is cached.
The extra immutable index is1236 bytes. It changes experimental cache-image
hashes; the older274084aa control describes the earlier common-only policy.

Native224-discovered/214-executed/ten-skip checks PASS after removing the failed
mount bypass (`direct-player-normal-mount-all-native-tests.log`). Two new ARM
checks verify the captured1011-byte paddle_end pose and exact cached bytes/cursors
for every direct player pose. The prior227 suite included the now-withdrawn
mount-policy cases. Unplayed d3878454 combined the direct index with that failed
mount experiment and was removed after hashing; its metadata/logs remain.

Fresh imagef66e880d0d11cd925dd4d781564ec0876fe5c598287898ea8fe02feb4502fcf5
restores original mounting and is in a four-console6–9 test with a second warm
swimming pass. Parent `direct-player-normal-mount-matrix/`; observations
`direct-player-normal-mount-performance/`. No swimming speed acceptance yet.

A further isolated194-node replay raises both the node cap and window budget
(256/2048), retaining327 actual candidates, and matches native contact bytes and
notification order with intact heap/restored free bytes. This is not production
code or a live edit. Any implementation must separately preserve the1024 true
candidate limit, bounded refresh work and native fallback; see
`stage14-bounded-window-work-probe.json`.

## Direct player poses and crowded collision lists

The normal-mount f66 four-console6–9 regression passes. The second swimming
traversal performs12 cache hits with no physical reads, and all consoles record
163 intervals at2 VBlanks. First traversal retains three cold reads. The direct
index covers154 original player BCA files; original archive loading is preserved.
The common-mount bypass is withdrawn after real integration crashes on6→7.

The next combined candidate56b1796f uses256 collision nodes and2048 axis-window
checks, with actual candidates and edge work still capped at1024. A retained
194-node level14 replay produces327 candidates, identical native contacts and
callback order, and restores heap free bytes. Instruction counts are287266
native,233088 cold planned and78692 reused; this is isolated ARM evidence only.
37 targeted collision tests and216 executed tests (226 discovered,10 skips) pass.
Live6–16 and physical performance acceptance remain pending.

## Combined crowded-list pass and painting follow-up

56b1796f PASSES short four-console6–16 diagnostics plus course return and
Save & Quit. In level14, collision elapsed is3.615ms steady/3.462ms motion,
versus6.68/7.229ms on d320. Steady cadence is252 intervals at2 VBlanks and33
at3; motion143 at2 and17 at3. Different shared starting ticks can change actor
trajectories, so these are separate scene samples rather than a controlled FPS
claim.13 remains mostly3 VBlanks; cold poses still hitch in9/10/12/13.

Read-only sampling identifies a400-cell continuous-wave painting in13. Its
native RippleHeight repeats the same phase-speed, amplitude and radial-slope
divisions for every cell. `--experimental-painting-math` reuses coefficients
only when all five wave parameters and the timer match. Phase and distance
arithmetic still run for every vertex with native fixed-point rounding. State0,
other modes, offline and unknown/invalid inputs keep the original routine.
The original signed-divider call is ROM-verified at02125cf0→01ffabe4.
Six isolated ARM tests match native phases, clocks, signed inputs and mutations;
no actor, RNG or parameter writes occur. A400-cell sample uses89200 native vs
64929 optimized instructions and1200 vs3 divisions. These are instruction and
call counts, not DS elapsed timing. The option is disabled by default pending
live timing/transition coverage. The code/data soft bound becomes37KiB; the
existing final64KiB loader limit remains enforced. Combined module body/tables
are42152 bytes in the current diagnostic build.

The240-test combined native suite passes (230 executed,10 skipped). Structural
boot checks explicitly used the earlier58e integrated image while testing the
new painting module; the former failed run retained a missing generated
provisional-ROM fixture error, then passed with COOP_HOST_ROM set explicitly.
All raw default private RAM fixtures remain available.

## Continuous painting live result and regular-grid normals

Painting coefficients f67dd4ca PASSES direct13–16, movement, shared pause,
world synchronization, course return and four-system Save & Quit. In matched
13-entry settings, control4604 steady cadence is247 at2/439 at3/4 at4 VBlanks;
f67 is268 at2/427 at3/2 at4. Movement changes33 at2/90 at3 plus boundary1 to
60 at2/74 at3/1 at5. Boot/shared ticks and trajectories can differ. This is a
modest gain;13 still misses full speed. All consoles reuse279600 coefficients
in the steady sample with one fill and no fallback; native geometry is retained.

A14 cold4969-byte `data/player/Y_sleep_start.bca` read crosses the steady/motion
boundary. Its read count is unchanged while its completion/store happens later.
A zero miss delta in a single phase does not establish no file-read stall. Trace
both active/end fields and store counters. Idle/walk/sleep first-use warming
remains part of the hitch work.

`--experimental-painting-normals` requires painting math and remains disabled by
default. It proves square2–32-cell regular X/Y coordinates before writing mesh
fields; unknown geometry/counts and offline modes call the original. The known
zero cross-product terms and redundant vector-subtraction calls are removed.
Both patched calls are ROM-verified to immediately call native FlattenFrame.
Border normals are overwritten by that function, so their calculation is
skipped while their heights remain available to neighbouring interior normals.
All remaining normalization and final flattening still use native routines.

Seven ARM cases compare every resulting vertex byte after normal/flatten,
including nonzero border heights, signed wrapping, reversed/min/max grids,
nonregular/rectangular/inconsistent-count fallbacks, actor/RNG preservation.
400-cell instructions fall90153→75864; normalizations400→324. Full247-discovered
suite passes (237 executed,10 skips). This is private replay evidence; live
cadence is pending. Code/data soft bound becomes38KiB; final64KiB cap remains.
The diagnostic combined body/tables are43072 bytes. No polygon/mesh/actor detail
is removed. A captured inner256-cell region has256 distinct normalization inputs;
a speculative normalization-result cache was therefore not added.

## Reject-only private mesh work

Normals7f9 PASSES13–16, movement, pause, course return and four-system Save &
Quit.13 steady is284 intervals at2 VBlanks/418 at3: still slow. The captured
painting flags are0x38 in4604, f67 and7f9, so native BeforeRender rejects its
mesh in all those views while behavior still computes400 heights/normals.

`--experimental-painting-visibility` requires normals/math and is disabled by
default. It skips only that known continuous20x20 private mesh when the exact
native actor-render flags reject it. It uses saved local clip bits during the
shared AI visibility scope. Native HitTest/slide/matrix/open-flag/phase code is
still executed; the actual cell count is not changed. Native final flattening
is retained. Visible frames regenerate native vertex bytes before rendering.
Other geometry, state0 final-wave frames and offline/disabled modes retain work.
The first count load at02126570 is ROM-verified and a branch bridge restores
all non-result registers, CPSR flags, SP and native LR before resuming02126574.

Nine private ARM cases verify actual native render-bit equivalence, shared actor
fields, hit-test calls, native sliding/matrix/open-flag code, saved visibility,
hidden→visible byte identity, native wave restart, state0 final frames, fallback
and complete bridge ABI. Native wave distance refresh explicitly zeros local z,
so old hidden heights cannot affect the next wave's planar distances; the test
runs that original BeginWave path. Three hidden frames fall551346→31791 ARM
instructions, height calls1200→0. This is private replay, not live frame rate.

The fixed five-word coefficient comparison also avoids the compiler's counted
boolean loop while checking every parameter.400-cell heights now use45766
instructions (native89200, old optimized64929); all six arithmetic cases pass.
Full256 tests pass (246 executed,10 skipped); the integrated visibility image's
four retail boot/layout checks pass. Combined body/tables43476 bytes, still
inside the38KiB code/data and64KiB final-module bounds. Live timing is pending.

## Optional compressed-input loading window

`--experimental-lz-window` retains the exact streamed LZ10 decoder and native
archive mounting, and tries a4096-byte aligned heap input window after allocating
the output. ROOT is preferred, then GAME; neither optional allocation invokes
fatal allocation policy. If neither fits, the original512-byte window is used.
The4096-byte storage is on the heap; the original543-byte stack fallback storage
remains. Explicit owner release occurs before completion and on decoder/read
errors. IRQs are restored before filesystem reads. No extra4KB stack is needed.

Eight private ARM cases pass, including exact decompressed output, file cursor,
cache maintenance, repeated loads, GAME ownership and both-heaps-pressure
fallback. The captured23607-byte skybox takes48 physical reads with512-byte
chunks versus7 with4096-byte chunks, including its header. This read-count
comparison does not establish a whole-level loading-time improvement.
Full259 discovered tests pass (249 executed,10 skipped), plus four integrated
retail boot/layout checks. Combined diagnostic body/tables are44188 bytes;
code/data soft bound39KiB and final module64KiB remain enforced without padding.
The option is disabled by default. The normal integrated cartridge independently
reproduces35d8be5d8a49681d37c9e05f3b12b991bb6ffff96e165f05223ba46c6d25adc3.

The0c52c505 combined cartridge is currently being tested with the normal
castle→BoB route and four confirmed Yoshi characters, followed by native stage
entries6–16. SDK VBlank loading measurements include controller/poll overhead;
a fresh same-source window-disabled control is needed for causal comparison.
All earlier direct13 painting runs used the native Mario/Luigi/Wario/Yoshi
character fixture, so their results are not four-Yoshi acceptance.
Visibility8cc passes13–16 and return/save/quit;13 steady improves to791 intervals
at2 VBlanks/28 at3/1 at4/1 at37/3 at38. That still includes cold reads and hitches
and is not full-speed hardware acceptance.

## Idle/walk prewarming and normal-route regression

`--experimental-animation-prewarm` requires the optional animation cache and is
also disabled by default. Before the native common archive is released it copies
the builder-verified Y_wait/Y_walk compressed members into optional GAME scratch,
unmounts normally, then stores exact bytes in the existing reclaimable ROOT
cache. The temporary9652-byte aligned scratch allocation is returned through
its recorded owner. No file reads are added. No scratch space means ordinary
unmount and no warming; unavailable cache storage also releases the scratch.
Native source lifetime, exact bytes, heap pressure, offline policy, repeated
boundaries and mesh cleanup checks pass. Full266 tests pass (256 executed,
10 skips); combined body/tables44700 bytes. Wireless prewarm acceptance pending.

The0c52 normal four-Yoshi run PASSES6–12, then FAILS12→13 on all three guests
inside native model-work allocation (1048 bytes, DoSetFile02016c20), before the
painting mesh allocator. It is not accepted. Retained RAM/DTCM captures are in
lz-window-yoshi-performance/06-level-12. A later read-only frontend regs command
terminated the frontend; the original game-failure captures predate that harness
failure. Actual frontend exit is verified; no party remains active. A fresh
same-source window-off control is still required to isolate loading changes.

## Guarded model-work source pressure boundary

Normal four-Yoshi failure0c52 requested1048 bytes in native DoSetFile at02016c20.
The original source remained mounted while ROOT could not fit that work buffer.
The guarded replacement keeps native allocation and cleanup, releasing common
source only when cooperative ROOT pressure requires it, no file IO is active,
and the supplied BMD is outside the mounted archive allocation. The caller's
r6 BMD is forwarded through a ROM-verified bridge; its other argument registers
are restored. Native mounting remains intact. The owned ten-bone BMD from the
failure is0232bdfc, not the unrelated saved caller value021891c4.

Nine native checks reproduce the failure, exercise full native model setup and
destruction, preserve BMD bytes and heap ownership, verify fitting/private-heap/
offline/borrowed-source/active-IO guards and bridge arguments. Full275 tests pass
(265 executed,10 skipped). The first build exceeded the39KiB soft code/data
bound; it is now40KiB, with the same hard64KiB module limit and no padding.
Combined body/tables44932 bytes. Tests accidentally
started against the failed build had mismatched ELF/image and are invalid;
the corrected build-and-test command is serialized and stops on build failure.
The initial full-model test also used the wrong saved BMD pointer; the corrected
case identifies the exact1048-byte ten-bone model from the native registry.

The167a680a cartridge combines the guarded fix, idle/walk prewarm and other
performance options. A fresh four-console normal-route6–16 run is active;
acceptance through the failed12→13 transition and return/save is pending.

## Loading-only animation prefetch

The normal167a BoB sample confirms that archive-copy prewarming leaves two
physical reads during steady play: Y_sleep_start and Y_sleep_wait. Cold-weather
idle start (6614 bytes) also stalls stage10. Host CARD reads complete within a
VBlank while guests wait30–40 VBlanks; native cadence sees the whole party stall.
This is evidence for moving those first reads into loading, not reducing poses.

`--experimental-animation-prefetch` requires animation caching and is default
off, independent of archive-copy prewarming. After native skybox loading it
tries an8192-byte GAME scratch buffer and native file views for nine verified
common/direct Yoshi idle/walk/sleep and shared cold-weather poses. Existing
entries are reused without IO; insufficient ROOT cache room skips the read.
IRQs are enabled for IO and the aligned scratch has cache maintenance before
CARD DMA. Exact complete reads alone enter the same32-slot/64KB optional cache.
Every opened view closes on success or short read; scratch ownership is returned.
Offline, gameplay, another thread, active IO and unready/error archives skip it.

Eight ARM cases pass: exact original bytes/cursors, all nine cache hits without
new reads, repeat passes, existing common entries, close/error paths, aligned
cache maintenance, IRQ policy, both heap-pressure paths and readiness guards.
Native FS read/wait/seek/close and heaps execute; only physical open/range and
ROM data delivery are adapted. Full283 tests pass (273 executed,10 skipped).
Combined5bf388b2 body/tables45932 bytes; code/data soft bound41KiB and hard64KiB
module cap are enforced. No padding is allocated. The first40KiB build was
rejected before any native tests; failure logs remain. Wireless acceptance is
pending behind the active167a regression, which currently passes normal6–8.

The default flags-off slot-A integrated cartridge independently reproduces
`de4be02f1e8a4067265457a7d1894a9f8fb3c3454cf51aaa101e6c3e2edac881`
in two complete builds. Its9 model-work tests and14 boot/layout/relocation/map
checks pass. Older35d8be5d is the pre-model-pressure normal image. No new
hardware performance or complete-campaign acceptance is claimed.

Diagnostic clarification: the later0c52 frontend exit came from an invalid
`regs` request without its required console index (`regs 1`, for example).
The frontend reported "Bad console index" and exited. This was an operator
command error, separate from the retained native12→13 game crash. No register
command was used to modify state; the original failure RAM predates that error.

Infrastructure interruption:167a PASSED6–11 and reached12 but the runner could
not create its12 output folder because the workspace filled. Its subsequent
failure screenshot command ended the frontend. This is not a native game-crash
result and does not validate12→13 or return/save. Original results are retained.
Historical compression copied files from an immutable lower layer, consuming
space instead of reclaiming it. Those verified archives and closed167a outputs
now live on the separate /tmp filesystem with their original paths preserved by
symlinks. Inputs, native default RAM fixtures and source files were not moved.
New5bf prefetch runs write captures directly to that separate filesystem.

The same-source window-disabled control builds as8cbf93be78729e861cbc19e2c588941986ac19f909656fe02bc36b77cf038599.
Its21 boot/LZ/model checks pass (18 executed,3 large-window-specific skips).
Re-enabling the window with the same current source exactly reproduces167a,
recorded in model-work-window-control-source-proof.json. Thus its pending
wireless comparison can isolate the input-window option. No control party has
started; only5bf is active. Global ELF/base/default bootstrap now match that
167a source-reproduction build, not the active5bf prefetch image. Original raw
ROMs and frozen build reports remain separate.

## Physical three-system follow-up: be682ed7f

The user tested the requested three-system R4 performance build atbe682ed7f,
expected SHA-256f7fc1a0118fadfde2aa16ea64b3a53c7d510659ab50c5388fad36caefc50967d,
with --clients2 --experimental-animation-cache --experimental-collision-plan.
All Yoshi heads are visible and no missing geometry was observed. This is
positive physical rendering evidence for that image and configuration.
Speed remains very slow, with frequent hitches especially during movement;
any gain is slight. Long loads show nondescript black/white screens. Record
hardware performance and loading UX acceptance as FAILED, not pending or passed.
This does not validate later direct-pose, expanded-plan, painting,4KB-window,
model-pressure or loading-prefetch candidates. The active5bf emulator regression
continues; new final-image physical speed and loading acceptance are required.

## Normal four-Yoshi prefetch acceptance and matched loading control

5bf388b2 PASSES normal castle→BoB, diagnostic6–16, four controllers, shared
pause/world checks,600 further steady16 frames, native course return and
four-system Save & Quit (other host files remain protected by the save test).
It has been shut down and actual frontend exit verified. Every steady6–16
sample records zero new physical gameplay reads. Stages7/8/9/10/11/15 are almost
entirely2 VBlanks/input tick;6/13/14/16 still have slower intervals. Host steady14
is747 at2,110 at3, plus one boundary1. BoB is842 at2,44 at3,one4 and boundary1.
These are stock-core native cadence measurements, not rendered FPS or physical
acceptance. The earlier30–42-VBlank sleep/cold stalls disappear in these samples.
Stage9 movement still reads paddle_1/2/end (922/767/1011 bytes); the last guest
read takes29 VBlanks. These need further first-use handling.

Window-OFF8cbf93be PASSES the same normal route through6–8 and is closed with
actual frontend exit verified. Its source-equivalent window-ON build reproduces
167a exactly. One pair of loading measurements, including input/poll overhead:

| Native transition |512-byte window OFF control|4KB window ON167a|Reduction|
|---|---:|---:|---:|
|1→2|2733 VBlanks|1500 VBlanks|45.1%|
|6→7|5139|4304|16.2%|
|7→8|4898|4095|16.4%|

This establishes a gain in these emulated transitions, not a universal load-time
claim or hardware result. Loading is still very long.9-pose prefetch5bf records
1555/4387/3949 respectively; its different cache/startup state is not the matched
window-only control. Preserve each exact image/report rather than mixing runs.

## Experimental animated stage feedback

`--experimental-loading-screen` is independently opt-in. It leases256 bytes at
the end of native16KB sub-OBJ bankI, two regular OBJ palette colors and8 OAM
objects while native stage initialization is pending. A black-outlined white
LOADING word and clock-driven spinner use the original native VBlank handler;
IRQ registration is restored when the lease ends. No heap buffer or content
reduction is introduced. Unused bankI may be borrowed temporarily only if the
SDK and hardware both show it unowned; its prior ownership/mapping is returned.
Unknown OBJ layouts/IRQ handlers/owners are left alone.

Native bank disable, OBJ decompression, OBJ palette copies and direct file
writes suspend and restore the lease BEFORE native asset writes, then snapshot
the newly written data before resuming. Skybox/prefetch completion releases it
before native final display configuration; pending group waits can reacquire
with that new configuration. Gameplay readiness and connection-error display
release it. Stage loading is the current coverage; initial firmware/Station
screens and arbitrary other scene-loading screens are separate.

Ten compiled ARM cases pass: tile animation, exact tile/palette/OAM/
brightness/IRQ restoration, unrelated display-bit preservation, native bank
ownership, fresh asset snapshots, writer arguments/results, guards and offline
behavior. Original IRQ registration/bank SDK code executes in private mappings;
asset producers/VBlank bodies are adapted. Full293 tests pass (283 executed,
10 skipped). Combineddf0b76ee body/tables49116 bytes; code/data soft bound44KiB,
hard64KiB module cap unchanged without padding. The first compile rejected an
include path; the corrected explicit repository-relative include builds.

Onlydf0b UI party is now active. Its controller observer checks actual rendered
LOADING letters and two spinner phases per console during native transitions,
plus zero ownership faults, released state and native IRQ at playable stages.
The observer's9-frame sampling delay is test capture spacing, not a runtime
or human timing requirement. Live UI/heap/save acceptance remains pending.

## Bounded actor-class elapsed profiling

`--diagnostic-player-cost` now also measures successful nonplayer dActor_c
behavior spans, from the return of the original BeforeBehavior guard until
entry to AfterBehavior. It excludes the guard and cleanup themselves, and does
not cover dBase-only HUD classes or subclasses which override those hooks.
The aggregate is separate from player behavior. A64-slot linear-probed table
also groups these spans by native16-bit actorID and pause state; saturation
increments an overflow counter instead of overwriting another class. All rows
reset at stage identity changes. Counts,64-bit elapsed total, minimum and
maximum use the same SDK clock and sequence protocol as the existing scopes.
They include interrupts/waits and cannot be called exclusive CPU-cycle costs.

Native tests cover exact elapsed totals, class hash collisions, pause separation,
saturation, maximum actorID encoding, stage reset, rejected behavior and existing
player/render delegates. The source changes are diagnostic-only; no actor
behavior, animation, clipping, file IO or packet contents are altered. The
soft linked code/data ceiling is48KiB to accommodate diagnostic arrays; actual
allocation stays at the emitted size and the64KiB final-module limit remains.
Use before/after totals in a stable stage and compare class totals against
aggregate spans; last-actor pointers at frame boundaries are not elapsed time.

## Actor-class measurements and line/coin shadow work

The7f10 normal four-Yoshi profiling route reaches BoB with a64-class table and
no overflow. In its stable609-frame guest sample, nonplayer Behavior spans total
13.93ms per stage render: yellow coins4.37ms, Goombas3.57ms, Bob-ombs1.93ms,
King Bob-omb0.87ms and Chain Chomp0.40ms. Four player behaviors total4.26ms;
bodies1.80ms, heads0.94ms, stage Render3.98ms. Stage Render already includes
actor-collision elapsed: **do not add collision to that total again**. These
are instrumented elapsed SDK-clock observations, including interrupts/waits,
not exclusive CPU costs or hardware acceptance. Later class samples include
13 with Goombas1.49ms,actor237 1.44ms,actor255 1.27ms and coins1.04ms.
The active route continues beyond16. Initial7f10 profiling was interrupted by
an invalid1792-byte readv field (frontend maximum1024), not an established
native game failure. Its frontend exited. The corrected repeat reads two
896-byte fields under the same core lock and retains exact image7f10.

`--experimental-line-broadphase` is optional and independent of collision plans.
It replaces only the Vec3_Dist call at020387a4 in native dBgCh_Lin::DetectClsn.
The subsequent ADD/CMP/BGT still consumes the distance comparison. In the
ordinary co-op gameplay state, wrapped32-bit differences with absolute values
below2^29 prove that native squared arithmetic and its sqrt left shift cannot
overflow. If any axis exceeds the nonnegative cutoff, return cutoff+1; otherwise
run original rounded Vec3_Dist. Unusual differences, thresholds and offline/
nonplaying states retain native arithmetic exactly. The bridge forwards the
native r6+r4 cutoff and preserves those saved registers. The builder pins the
original call and following ADD/CMP. No mesh query or accepted contact is changed.
Six native cases cover600 seeded comparisons, rounding/touching boundaries,
wrap/large/negative fallbacks, modes, bridge ABI and full captured coin behavior.
For68 captured coins all complete actor bytes and query results match;
128054→124253 private ARM instructions and704→45 SQRT reads. The first
coordinate-domain prototype was correct but slower in instructions, so it was
replaced before gameplay testing by the wrapped-delta guard. These are private
instruction counts, not a measured wireless or hardware speedup.

`--experimental-local-coin-shadows` targets a larger related cost. The AI
visibility guard neutralizes clip bits so every replica simulates the same
world. Coin helper020b10e4 uses bit8 only to gate a **visual shadow-floor probe**;
neutering it makes far, unprobed coins ray-cast every frame even when invisible.
A single flags-read hook at020b10f0 restores that saved local bit for the native
probe gate. Coin Behavior itself still sees the neutral AI flags. Collection,
movement, timers, Yoshi-mouth logic, collider updates and model matrices remain
native. Shadow floor state/height and derived render clip radius are visual
state; this hook does not introduce camera-dependent simulation decisions.
Original native probing resumes as soon as the coin becomes visible.

The authenticated overlay is changed only after loading, with both the LDR and
following ANDS pinned. No new cache/allocation is needed. Six captured ARM cases
cover native visible behavior, local-reference flags, inactive/foreign-context
policy, ABI and returning to visible state. In this68-coin offscreen BoB cohort,
complete actor bytes also match the old implementation: the redundant far
probes all miss. Work falls127310→21616 instructions (83.0%) and704→0 SQRT reads.
Combined candidatef74354c3 passes the full311-test suite (301 executed,10
skipped). Four additional observation-client checks pass after that run: large
fields are split into legal1024-byte requests within a single4KB atomic read,
and invalid requests fail before reaching the frontend. The wireless comparison
is next; this is not yet physical or all-level performance acceptance. Both options are
off by default and absent from the published2ac hardware retest candidate.
Evidence: `bob-coin-instruction-profile.json`, `line-sphere-delta-native-tests.log`
and `local-coin-shadow-native-tests.log` in the private runtime directory.


A new read-only paused coin check compares stage-relative identity, type,
parameter, position/angles, movement, timers, active/bounce flags and block state
on every peer. Local shadow-floor bits/height and derived render clip radius
are intentionally excluded; they do not make collection or motion decisions.
The comparison passes an existing four-system105a paused fixture (22 coins).
It is integrated into stage checks for the local-coin-shadow candidate and must
also pass in actual wireless play. The earlier2ac three-system retest image is
independently rebuilt after these source additions and remains byte-identical;
its14 boot/relocation/minimap proof checks pass. Neither new option is enabled
in that image, so the published hardware test instructions/hash stay valid.

## Wireless coin-shadow result and retained-pause timeout

Candidatef74354c3 PASSES normal four-Yoshi6–23, four controllers, shared pause,
actual loading animation, native graphics/IRQ restoration and per-stage paused
coin gameplay comparison. Every comparable paused coin set matches across all
four consoles, including68 in BoB,102 in14 and50 in23. The same image's later
return/save attempt finds the retained session already ended. First retained
reason is0x101 (native input-exchange retry exhaustion, bit0), on all consoles
at tick183074, stage23, pause1, loop phase4, no file wait. This occurred during
an extended unattended pause after the matrix finished, not within a passing
matrix checkpoint. It is NOT established as a checksum or coin-state failure.
The failure captures remain in `local-coin-shadow-stage23-return-save/`.
Save & Quit is not verified for this image. Its frontend is explicitly closed
and actual exit verified; repeat/control and long-pause stability remain open.

With the same elapsed actor-class diagnostics enabled on both images, guest
BoB steady cadence changes from1 interval at2 VBlanks/607 at3 on7f10 to
885 at2/14 at3 plus one boundary1 onf743. Yellow coin elapsed per stage render
falls4.37→0.856ms; all nonplayer behaviors13.93→9.93ms.13 improves from
603x2/187x3/13x4 plus boundary1 to797x2/66x3/5x4 plus boundary1.14 changes
little (382x2/342x3/7x4 versus388x2/335x3/9x4). Boot/trajectories can differ;
these are instrumented emulator samples, not physical full-speed acceptance.
The class profiler itself adds work and is absent from normal builds. Do not
compare its cadence directly against older images without that instrumentation.

## Optional adoption of packed common animations

`--experimental-packed-animation-cache` requires the animation cache and lazy
capacity-query support. It replaces, and cannot be combined with, the two-pose
`--experimental-animation-prewarm` option. It is disabled by default.

The native common NARC has already been downloaded for stage resources. At the
existing source-release boundary, preserve its original unmount/name teardown,
clear its native ARC owner record, then adopt its existing ROOT allocation as
optional read-cache ownership. Compact the132 eligible compressed BCA
members in place and shrink with the native allocator to202512 bytes. This
includes126 player poses and six cap/star poses. No new
buffer, member transfer or file read is required. All original mounts before
this boundary, ROM/archive extents and later raw member views remain native.
This does not repeat the withdrawn whole-mount bypass experiment.

One of the existing32 cache records owns the entire packed block; regular reads
retain an additional64KB budget and at most31 other records. Native pressure,
growth, capacity queries and teardown can reclaim the block before making the
same allocation decisions as an empty optional cache. Existing exact virtual
capacity bookkeeping works for this single native allocation, including its
original backward alignment. Common read hits copy exact original bytes and
retain the original file cursor/readiness/error/thread checks. Generic running,
jumping, landing and wall poses can remain hot instead of requiring separate
wireless first-use reads. Separate direct NitroFS poses still use the ordinary
read cache/prefetch policy and need broader action coverage.

Packing uses a temporary reserved cache key and exposes that optional ownership
between copies, masking IRQs for at most one16KB native copy. If an intervening
allocation reclaims the block, packing stops before touching it again. Validation
or shrink failure retains native unmount/free behavior. The settled cache block
contains no borrowed model, actor or SDK archive pointers.

Six new ARM cases cover every original member byte/native hit cursor with zero
physical reads, exact virtual/native capacity, pool plus31 regular cache records,
source validation fallback, interrupted ownership and foreign/async views. Existing
model-work, painting and stage-source tests now explicitly evict optional cache
ownership before asserting restoration of the complete original free block.
Two old immediate-free assertions failed until that lifetime distinction was
made explicit; their stronger native cleanup checks and the repeated full suite
pass. Full321 discovered tests PASS (304 executed,17 skipped, including the
mutually excluded prewarm configuration). Body/tables53764 bytes;64KiB cap stays.

Candidatef8c7a49a6a22b800f320559626a48f9436cef31d6215cff69c737732f88f81da
passed the normal four-Yoshi wireless route through6–23. This earlier
configuration packs126 player poses into200740 bytes. The block remains on every
sampled guest, common hits accumulate, steady physical read counts do not grow,
and validation/interruption/shrink error counts are zero. Heavy13/14 model/heap
and paused coin/gameplay checks pass. The first return/save check stopped on a
test-only requirement for Goombas in stage23; its retry compares available enemy
and coin states instead. The retry passed native course return, Save & Quit,
host cartridge persistence/title initialization and all three guest shutdowns.
Explicit frontend shutdown and actual process exit were verified.

The newer132-pose build also prefetches the direct swimming-damage pose, bringing
its direct prefetch list to15; the non-packed configuration retains its original14.
Candidatef759a3778d5ddea71b84173c061112763e9da94db2e7b5d7c4675fb8e4f46143
omits the actor-cost profiler so cadence can be measured without its overhead.
Fourteen focused packed/prefetch cases pass. The full321 discovered native
suite also passes (293 executed,28 skipped, including disabled actor-cost and
mutually excluded prewarm checks). Its actual wireless comparison is underway.
With packed mode off, the default integrated cartridge rebuilds byte-identically
to publishedde4be02f; the existing three-system hardware candidate also rebuilds
byte-identically to2ac1e988. More stages, direct first-use actions, mixed
characters and physical acceptance remain open.
Private evidence: `packed-animation-adoption-feasibility.json`,
`packed-animation-all-native-tests.log`, `packed-animation-{matrix,performance}/`.


## Collision composition measurement and additional actor parity

An unpublished experiment combined the ordered collision plan with the older
axis check at the remaining native cylinder-distance call. Its321 native checks
passed (299 executed,22 configuration skips), including randomized native contact
bytes and notification order. A private comparison of the160-node captured list
measured plan-only173071 instructions/8 SQRT reads versus combined173231/5.
For Lethal Lava Land, reconstructing the194-node list privately from its retained
plan nodes measured warm plan-only79244/3 versus combined79308/2; cold builds
were234979/3 versus235043/2. Contacts and callback order matched. Hardware SQRT
latency is not modeled by these isolated instruction counts, and no material
performance benefit is established. The composition option was discarded; the
builders retain their original mutual exclusion. These measurements do not
alter the playedf759 image or its acceptance status.

A new native replay executes all15 captured Goomba Behavior updates and compares
complete0x488-byte actor state and return values against the original distance
calls. The existing line-sphere rejection preserves those results while changing
109425 instructions/376 SQRT reads to108123/151. All seven line-broadphase cases
pass. This extends correctness coverage of the already published optimization;
it adds no runtime hook or production overhead.

Private evidence: combined-collision-native-benchmark.json,
combined-collision-level14-{cold,warm}-benchmark.json,
combined-collision-all-native-tests.log, combined-collision-plan-recheck.log,
combined-collision-goomba-tests.log. A first multi-mode private benchmark reused
a workspace pointer after restoring its heap fixture; explicitly releasing the
private plan between trials fixed that probe. No live console was modified.


## Optional bootstrap payload grouping

`--experimental-bootstrap-multicast` changes only initial unsigned execution-
payload data sends. The signed station's existing native reliable port15 path
can address multiple associated guests. Group only phase8 peers with identical
nonterminal offset/chunk and zero cooldown; keep menu/length/start/execute
messages individual. Capture each selected generation before submission. On
SDK success advance only matching phase/generation/offset/chunk records. Errors
advance none; stale recipients cannot acknowledge a replacement transaction.
The existing complete-body barrier still precedes every execute terminator.
No user timing, custom emulator core, new client protocol or larger packet is
required. It is disabled by default and does not accelerate stage WFS reads.

The native fixtures use the default three-guest parent and exercise singleton,
two-member and three-member destination bitmaps. Seven private native ARM cases
execute the actual compiled selection, Pump and
completion code with isolated SDK submission:1–3 target membership/readiness,
control/terminal exclusions, exact grouped packet bytes and per-peer advancement,
SDK submission/completion errors, generation/phase/offset/chunk changes, duplicate
completion, and slow-body/individual-execute barriers. The first terminal test
used the outer HaxxStation package size instead of its embedded execution body;
correcting that private fixture makes all seven pass. No live packets were edited.

Candidate5db570d18224942544dd8f00977a8ef6cd6dea8a230d0a1431ad26dd44e564a5
is built but UNPLAYED. Full image/overlay audits pass. With the new option off,
the build is BYTE-IDENTICAL to playedf759. Actual wireless transfer speed,
full-body execution and physical behavior remain unverified. Counters report
completed groups, actual recipient advances, potential repeated payload bytes
saved and stale recipients; these are not measured wall-clock savings.
