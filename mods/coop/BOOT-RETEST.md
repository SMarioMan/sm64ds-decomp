# R4 boot retest

This is an experimental, normal-game cartridge for the reported New Nintendo
3DS / R4 SDHC 2022 / Wood white screen before the title screen. The user built
this candidate from commit `89505d4009e862e4c561798b901cf45e4992c665` and confirmed:
“The ROM now boots on the R4 card.” The reported boot issue is resolved on that
setup. Full campaign and physical wireless acceptance are still incomplete;
see [WORKLIST.md](WORKLIST.md).

This candidate supersedes the previously linked `retail-boot-local-camera-host.nds`
(`ce3cdcda3dd12f1c...`). It includes the same boot-layout correction plus the
newer archive index and independent camera fixes. The host ARM9, ARM7, secure
area, and original secure-area metadata remain identical to the retail game.
The parent bootstrap loader now resides in overlay 75.

## Build

From your existing checkout, with no uncommitted local edits:

```bash
git fetch origin
git switch co-op-multiplayer
git pull --ff-only origin co-op-multiplayer
```

Activate your existing mod toolchain environment. The commands below assume
Bash/Linux; keep your existing launcher setup on other platforms.

Required tools:

- Python with `ndspy==4.2.0` and `pyelftools==0.33`.
- `dspatch` on PATH, built from Gericom/dspatch commit
  `32856c4b68c8e45d90fe135d5555a4596fbd2955`.
- `tools/mwccarm/2004/b56/mwccarm.exe`, SHA-256
  `c6aafc210c78e91b123e8e949b8e26faa76849225b9f639780fcc9db6cdff0b7`.
- `tools/mwccarm/1.2/sp2p3/mwldarm.exe`, SHA-256
  `eada466d4f0c309fbcf061ff5791a2c98a92d8b0e2364c53a0a9d0fe42100a7f`.
- On Linux, set `MWCCARM_LAUNCHER` to your working compiler launcher, e.g.
  `export MWCCARM_LAUNCHER=wibo`. On native Windows no launcher is required.

If the Python dependencies are missing, install them in your active virtual
environment:

```bash
python -m pip install ndspy==4.2.0 pyelftools==0.33
```

Use your personal ROM dumps; adjust the two input paths below. Expected SHA-256:

| Input | SHA-256 |
| --- | --- |
| Super Mario 64 DS Europe revision 0 | `ce5829aaa79f06c67140ed1f45cbca738b0a9d0180538c8c1498472d859db032` |
| DS Download Station Volume 1 USA | `ddac6d5c40c095eb282f0f14e969cc36feb15386e231ffaca3286b4a8fff00d3` |

From the repository root, run only this integrated builder. It rebuilds its
intermediate images automatically; do not run another build concurrently.

```bash
python mods/coop/build_download_play.py \
  "/path/to/Super Mario 64 DS (Europe).nds" \
  --station "/path/to/DS Download Station - Volume 1 (USA).nds" \
  --save-slot A --clients 3 --channel 1 --beacon-period 100 \
  --station-handoff closed-restart-parent --runtime-placement root \
  --output build/coop/bootstrap/retail-boot-full-local-camera-host.nds
```

Expected output SHA-256:

```text
aea94b7bc8a51986b02c258cb779934bd200f269e05ad4d193282237be4baedf
```

This exact hash was reproduced in two independent builds in the cloud
workspace. The adjacent `.json` records the inputs and image audits, including
`bootImagesUnchanged: true`, `secureAreaUnchanged: true`, and
`bootstrapLoaderStorage: "overlay75"`.

Optional cartridge-layout verification (requires only the build dependencies):

```bash
COOP_HOST_ROM="$PWD/build/coop/bootstrap/retail-boot-full-local-camera-host.nds" \
  python -m unittest discover -s mods/coop/tests -p 'test_boot_layout.py' -v
```

## Physical check

Copy **`build/coop/bootstrap/retail-boot-full-local-camera-host.nds`** to the
flashcart and launch it normally. This is the host cartridge; do not copy the
intermediate client, probe, or provisional-parent images instead.

Use a distinct filename for this test and keep existing saves backed up. The
build uses host adventure file A if you proceed into gameplay. For the initial
check, reaching the title screen is sufficient; Download Play guests, BIOS
files, and melonDS are not needed to build or perform this boot check.

Record the output hash, whether the title screen appears, and any different
behavior after the R4 loading screen. Emulator startup does not establish that
the physical white screen is resolved: both the old and corrected layouts boot
in BIOS/firmware emulation. The successful physical boot above is user-reported
evidence, separate from those emulator checks.
