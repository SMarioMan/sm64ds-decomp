#!/usr/bin/env python3
"""The two tiers: how much of the game is MATCHED and LINKED.

One percentage cannot describe this project, because "done" means two
different things and they move independently:

  MATCHED    the C compiles to the ROM's exact bytes. Provably the original
             logic. This is the number the README bar and the treemap show.
  LINKED     the function's translation unit actually reaches the PC port's
             binary, replacing the host stand-in that was there before.

They are deliberately not a funnel: a function can be MATCHED and LINKED while
still being unreadable, and readability work never changes the matched bytes.

Both bars count functions. MATCHED counts against the dsd function universe.
LINKED counts functions whose translation unit the port build links, read from
config/port_linked_functions.txt. A stamp without that list falls back to
matched translation units and labels the count accordingly.

Usage:
    python tools/tiers.py                 # human-readable table
    python tools/tiers.py --json          # machine-readable, for chaos-db
    python tools/tiers.py --write-readme  # rewrite the block in README.md

MATCHED is read from chaos-db.json when it is present, which is the same file
the README bar and treemap read, so every surface reports one number. Without
it, the tiers that need no ROM are still reported and MATCHED is omitted rather
than guessed.
"""
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent

SRC = REPO / "src"
README = REPO / "README.md"
README_START = "<!-- tiers:start -->"
README_END = "<!-- tiers:end -->"
LINKED_STAMP = REPO / "config" / "port_linkage.json"
LINKED_FUNCTIONS = REPO / "config" / "port_linked_functions.txt"


# ------------------------------------------------------------------ markers
#
# The `@symbol` marker names a member's linker symbol where present; otherwise
# the filename stem is the same name by construction. The slicer below is kept
# here because tools/tubuild.py reuses it to slice a promoted TU's member
# source at marker boundaries. It is not a readability metric.

SYMBOL = re.compile(r"//\s*@symbol\s+(\S+)")


def _marked_member_fragment(text, symbol):
    """Return one explicitly marked member's source, or None if ambiguous.

    Production TUs put ``// @symbol <linker-name>`` immediately before each
    hand-written member. Slicing at the next marker keeps an unrelated member's
    text from being attributed to this member.
    """
    markers = list(SYMBOL.finditer(text))
    matches = [i for i, marker in enumerate(markers)
               if marker.group(1) == symbol]
    if len(matches) != 1:
        return None
    i = matches[0]
    start = markers[i].end()
    stop = markers[i + 1].start() if i + 1 < len(markers) else len(text)
    return text[start:stop]


# ------------------------------------------------------------------- LINKED
#
# LINKED cannot be computed here and must not pretend otherwise. port/tools/
# linkage.py reads build/port/walk_window.map, which only exists after an MSVC
# build of the port, and the port branches are not merged to main. So the number
# is STAMPED: measured by hand, recorded with the branch and commit it came from,
# and refreshed when someone runs a port build.
#
# A stamp with no provenance is worse than no number, so a stamp missing its
# branch/commit/date is treated as absent.


def linked_functions(stamp=None, list_path=None):
    """``(keys, commit)`` from the per-function list, or ``(None, reason)``.

    config/port_linked_functions.txt is written by tools/port_linked_functions.py
    from a port build. It is believed only while its ``# commit:`` line equals the
    commit of the usable stamp: two port builds must never be mixed, and a list
    without the stamp's provenance is a number nobody can trace. ``keys`` is the
    set of ``module:0xaddr`` strings; ``commit`` is the list's commit on success.
    """
    p = pathlib.Path(list_path or LINKED_FUNCTIONS)
    if not p.is_file():
        return None, "no per-function list"
    if stamp is None:
        stamp = linked_stamp()
    if not stamp:
        return None, "no usable stamp"
    keys, commit, universe = set(), None, None
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("# commit:"):
            commit = line.split(":", 1)[1].strip()
        elif line.startswith("# universe:"):
            try:
                universe = int(line.split(":", 1)[1])
            except ValueError:
                universe = None
        elif line and not line.startswith("#"):
            keys.add(line)
    if not commit or commit != stamp["commit"]:
        return None, f"list commit {commit!r}, stamp commit {stamp['commit']!r}"
    return keys, universe


def linked_stamp(stamp_path=None):
    """The stamped LINKED measurement (translation units), or None if unusable."""
    p = pathlib.Path(stamp_path or LINKED_STAMP)
    if not p.is_file():
        return None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not all(d.get(k) for k in ("measuredAt", "branch", "commit")):
        return None
    tot = d.get("matchedTus") or 0
    got = d.get("linkedTus") or 0
    if not tot:
        return None
    return {
        "linked": got,
        "matchedTus": tot,
        "pct": round(100.0 * got / tot, 2),
        "measuredAt": d["measuredAt"],
        "branch": d["branch"],
        "commit": d["commit"],
        "stale": bool(d.get("stale", False)),
    }


def linked(stamp_path=None, list_path=None):
    """LINKED, per function when the stamped build has a per-function list.

    Returns ``linked`` / ``of`` / ``pct`` / ``unit`` (``"functions"`` or, for a
    stamp with no usable list, ``"units"``) plus the stamp's translation-unit
    figures as extra detail: ``linkedTus`` and ``matchedTus``. ``of`` for the
    function count is the list's own ``# universe:`` line, the function universe
    of the measured tree; chaos_db_ci overrides it with the published record
    count so both bars share one denominator. None when there is no usable
    stamp at all.
    """
    stamp = linked_stamp(stamp_path)
    if not stamp:
        return None
    out = dict(stamp, linkedTus=stamp["linked"], unit="units", of=stamp["matchedTus"])
    keys, universe = linked_functions(
        stamp, list_path or (pathlib.Path(stamp_path).with_name("port_linked_functions.txt")
                             if stamp_path else None))
    if keys is not None and universe:
        out.update(linked=len(keys), of=universe, unit="functions",
                   pct=round(100.0 * len(keys) / universe, 2))
    return out


# ------------------------------------------------------------------ MATCHED


def matched(db_path=None):
    """MATCHED from chaos-db.json, the file the bar and treemap also read.

    Returns None when the db is absent rather than recomputing it: a second
    implementation of the matched rule is a second source of truth, and this
    repo has already paid for one of those (the itcm undercount).
    """
    p = pathlib.Path(db_path) if db_path else (REPO / "chaos-db.json")
    if not p.is_file():
        return None
    try:
        db = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    st = db.get("stats") or {}
    tot, got = st.get("totalFunctions"), st.get("matchedFunctions")
    if not tot:
        return None
    return {
        "matched": got,
        "functions": tot,
        "pct": round(100.0 * got / tot, 2),
        "matchedBytes": st.get("matchedBytes"),
        "totalBytes": st.get("totalBytes"),
        "bytePct": (round(100.0 * st["matchedBytes"] / st["totalBytes"], 2)
                    if st.get("totalBytes") else None),
        # The assembly subset, read from the same db for the same reason MATCHED is:
        # recomputing it here would be a second source of truth. Absent from a db
        # generated before the field existed, and every consumer treats that as
        # "do not print the line" rather than as zero.
        "handAsm": st.get("handAsmFunctions"),
        "handAsmBytes": st.get("handAsmBytes"),
    }


# ------------------------------------------------------------------- output


def collect(db_path=None):
    return {"matched": matched(db_path), "linked": linked()}


# Joining preserved README rows. Spelled as a constant because a newline escape
# written inline here has been mangled by an editing shell before, and a generator
# that will not import silently stops refreshing the bar.
NEWLINE = chr(10)


def bar(done, tot, width=30):
    filled = round(done / tot * width) if tot else 0
    if done and filled == 0:
        filled = 1
    return "█" * filled + "░" * (width - filled)


def matched_caption(m):
    """The indented line under MATCHED naming its assembly subset, or None.

    Generated rather than written into the README by hand, because it is a number
    and every number in that block goes stale the moment someone matches something.
    Indented so ``write_readme``'s preserved-MATCHED search, which looks for a line
    STARTING with "MATCHED", cannot mistake it for the row itself.
    """
    if not m or not m.get("handAsm"):
        return None
    return (f"           of which {m['handAsm']:,} are byte-exact assembly "
            f"(hand-written in the original, not C)")


def _linked_noun(k):
    """What LINKED counted: functions, or (an older stamp) matched translation units."""
    return "functions" if k.get("unit") == "functions" else "matched TUs"


def bar_block(t, preserved_matched=None):
    """The single fenced block shown under the README "## Progress" heading."""
    rows = []
    m, k = t["matched"], t["linked"]
    if m:
        rows.append(f"MATCHED    {bar(m['matched'], m['functions'])}  "
                    f"{m['pct']:4.1f}%   {m['matched']:,} / {m['functions']:,} functions")
        caption = matched_caption(m)
        if caption:
            rows.append(caption)
    elif preserved_matched:
        # A worktree may have the ROM inputs needed for LINKED but not
        # chaos-db.json, which supplies MATCHED. Updating the live rows must not
        # silently erase the last independently generated MATCHED measurement.
        rows.append(preserved_matched)
    if k:
        rows.append(f"LINKED     {bar(k['linked'], k['of'])}  "
                    f"{k['pct']:4.1f}%   {k['linked']:,} / {k['of']:,} {_linked_noun(k)}")
    return "```\n" + "\n".join(rows) + "\n```"


def write_readme(t):
    text = README.read_text(encoding="utf-8")
    start = text.index(README_START) + len(README_START)
    end = text.index(README_END)
    current = text[start:end]
    # The MATCHED row AND its caption: a worktree with no chaos-db.json preserves
    # whatever the last real generator wrote, and dropping the caption while keeping
    # the row would leave the block claiming more C than it measured.
    lines = current.splitlines()
    keep = []
    for i, line in enumerate(lines):
        if line.strip().startswith("MATCHED"):
            keep.append(line.strip())
            if i + 1 < len(lines) and lines[i + 1].strip().startswith("of which"):
                keep.append(lines[i + 1].rstrip())
            break
    preserved_matched = NEWLINE.join(keep) if keep else None
    new_text = text[:start] + "\n" + bar_block(t, preserved_matched) + "\n" + text[end:]
    if new_text != text:
        README.write_text(new_text, encoding="utf-8")
        return True
    return False


def report(t):
    m, k = t["matched"], t["linked"]
    out = []
    if m:
        out.append(f"MATCHED    {m['matched']:,} / {m['functions']:,} functions  "
                   f"{m['pct']:.1f}%   ({m['bytePct']:.1f}% by code bytes)")
        if m.get("handAsm"):
            out.append(f"           of which {m['handAsm']:,} functions "
                       f"({m['handAsmBytes']:,} bytes) are byte-exact assembly, "
                       f"hand-written in the original game and reproduced as assembly")
    else:
        out.append("MATCHED    (no chaos-db.json; run tools/chaos_db_ci.py first)")
    if k:
        flag = "  STALE" if k["stale"] else ""
        out.append(f"LINKED     {k['linked']:,} / {k['of']:,} {_linked_noun(k)}  "
                   f"{k['pct']:.1f}%   (stamped {k['measuredAt']} from {k['branch']}"
                   f" @ {k['commit']}){flag}")
    else:
        out.append("LINKED     (no usable stamp in config/port_linkage.json)")
    return "\n".join(out)


def main():
    db = None
    if "--from-db" in sys.argv:
        i = sys.argv.index("--from-db")
        if i + 1 < len(sys.argv):
            db = sys.argv[i + 1]
    t = collect(db)

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    if "--json" in sys.argv:
        print(json.dumps(t, indent=2))
        return
    if "--write-readme" in sys.argv:
        print(f"README.md {'updated' if write_readme(t) else 'already up to date'}")
        return
    if "--bar" in sys.argv:
        print(bar_block(t))
        return
    print(report(t))


if __name__ == "__main__":
    sys.exit(main())
