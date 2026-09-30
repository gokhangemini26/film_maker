# Troubleshooting

Problems that have actually happened while building FILM_MAKER and Last Signal,
with the fix. Each entry: symptom, cause, what to do. Exit codes are in
[CLI.md](CLI.md).

## Shell and environment

### PowerShell swallows `$variables` inside double quotes

**Symptom.** A note or value arrives truncated or with holes:
`fm revise G3 --notes "keep the $50 prop"` records `keep the  prop`
(PowerShell expanded `$50` before `fm` saw it). The same happens to
`$name`, `$(...)` and backtick sequences in any double-quoted argument.

**Fix.** Use single quotes in PowerShell: `--notes 'keep the $50 prop'`. To put
a single quote inside, double it: `'Mara''s jacket'`. Bash has the same rule for
`$`, so prefer single quotes there too. Also avoid inner double quotes in
PowerShell 5.1 arguments; they are stripped on the way to native programs.

### `fm approve` says "several projects exist ... pass --project"

**Symptom.**

```
fm: several projects exist (another, second_film); pass --project
```

**Cause.** With two or more projects, `fm` needs to know which one you mean.
Resolution order: `-p`, then `FM_PROJECT`, then the project containing the
current directory, then the only project.

**Fix.** `-p` is a global option and goes **before** the command:
`fm -p my_film approve G1`. Or `cd projects\my_film` first, or set
`$env:FM_PROJECT = 'my_film'` (PowerShell) / `export FM_PROJECT=my_film`.
Claude's commands take the project slug as their first argument
(`/film-look my_film`).

### `fm doctor` says `blender: REFUSED` (exit code 4)

**Cause.** The configured executable was not found, or it is not the pinned
series (5.2.x). The default path in `config/blender.yaml` is a Windows path,
so this is what a Linux machine or a cloud workspace prints.

**Fix.** Install Blender 5.2.x and set `FM_BLENDER` to its executable (or edit
`config/blender.yaml`). Any other series is refused on purpose; the record
would otherwise not be G6 evidence. Without the pinned Blender you can still
do all the creative phases and use `fm blender preview --draft`.

### Stale git lock

**Symptom.** `fatal: Unable to create '.../.git/index.lock': File exists.`
after an interrupted commit or a crashed tool call.

**Fix.** Make sure no git process is running (close other terminals, editors
with git integration, and any stuck Claude Code tool call), then delete the
lock file:

```powershell
Remove-Item .git\index.lock
```

```bash
rm .git/index.lock
```

Never delete it while a git command is still running.

### The laptop shell cannot push (no git credentials)

**Symptom.** `git push` from a Claude Code shell on the laptop fails with an
authentication error.

**Cause.** That shell has no git credentials.

**Fix.** Commit from wherever you like, but **you push from your own terminal**
(where your credential manager works). Do the same for pulls before you start
on another machine. See the one-writer rule in
[GETTING_STARTED.md](GETTING_STARTED.md#3-laptop-versus-cloud).

### `pip install` fails in the cloud ("externally-managed-environment")

**Cause.** The cloud workspace uses the system Python.

**Fix.** `pip install --break-system-packages -e ".[dev,vision]"`, or create a
virtual environment first (`python3 -m venv .venv && . .venv/bin/activate`).

### `fm qa stills` says Pillow is missing

**Fix.** `pip install -e ".[vision]"` (Pillow is the `vision` extra).

### `fm blender preview --draft` says it needs the `bpy` module

**Fix.** `pip install bpy` (cloud: add `--break-system-packages`). The version
you get (currently 5.0.1 in the cloud) is not the pinned series. Its records
say "draft" and it is never G6 evidence.

## Long-running commands

### Two-minute tool timeout

**Symptom.** A render started from Claude Code is cut off, or the tool call
returns before the job finishes.

**Cause.** A Claude Code tool call times out after about two minutes. A full
preview (one Blender process per shot, dozens of shots) takes much longer.

**Fix.** Run long jobs in the background, or in your own terminal window, and
poll the log.

Cloud / Linux:

```bash
nohup fm -p my_film blender preview --draft --jobs 4 > /tmp/preview.log 2>&1 &
tail -n 20 /tmp/preview.log
```

Laptop (PowerShell): run `fm -p my_film blender preview` in a normal
PowerShell window (no timeout there), or use the same run outside `fm`:
`scripts\m3_preview.ps1 -Project my_film` (it writes
`.fm_local\prev.log` and a `.fm_local\prev.done` file when finished; stills land in
`.fm_local\prev`, and no derived records are written). Prefer `fm blender
preview` for anything you want recorded.

A single shot can be re-rendered on its own, which is also the fastest way to
check a fix: `fm -p my_film blender preview --shots SC04_SH020`.

### Corrupt frames after a while (garbled colours in EEVEE)

**Symptom.** Later stills in a batch come out with wrong or garbage colours;
the same shot rendered alone is fine. Seen on Windows ARM.

**Cause.** One long-lived EEVEE process can corrupt its output.

**Fix.** Already built in: `fm blender preview` starts **one Blender process
per shot**. Do not "optimise" it into a single process. If you render outside
`fm`, keep one process per shot too (`scripts/m3_preview.ps1`,
`scripts/m3_preview_cloud.py` do). `--jobs N` runs N such processes at once.

### Full `pytest` hangs

**Cause.** Running the entire suite on a small or cloud machine has stalled.

**Fix.** Run targeted files under a timeout:

```bash
timeout 120 python -m pytest tests/test_project_and_ledger.py tests/test_canon.py
```

Test files: `test_agent_layer`, `test_blender_and_cli`, `test_blenderrun`,
`test_canon`, `test_deps_changes_scopes`, `test_m2_core`, `test_m3_prep`,
`test_project_and_ledger`, `test_qa_stills`, `test_resolve`, `test_schemas`,
`test_state_and_authority` (and any newer ones in `tests/`). On PowerShell run
one file at a time with `-x` and Ctrl+C if it stalls.

### Blender output lands in the wrong place (Windows)

**Cause.** Blender resolved a relative output path against `C:\`
(found in the M3 spike).

**Fix.** Always pass absolute paths to Blender. `fm blender preview` and the
scripts already do; keep it that way in any new runner.

## Approvals and state

### "Authority refused" (exit code 3) when Claude runs `fm approve`

**Cause.** Human decisions need a person at an interactive terminal typing the
confirmation. A non-interactive caller (how agents run) is refused, and the
`.claude/settings.json` deny rules block it a second time.

**Fix.** Copy the exact command Claude printed and type it in your own
terminal. Do not try `--sandbox-confirm` (sandbox projects only) or
`FM_ACTOR`; both are blocked for agents on purpose.

### A gate shows "approved (DRIFTED)" and `fm advance` refuses

**Cause.** Something the gate approved changed after approval: an edited
document, or upstream canon changed by an approved change request. Everything
below it is stale.

**Fix.** `fm -p my_film status` and `fm -p my_film plan --scope film` list what
is stale. Regenerate it through its owner (`/film-revise`), re-stamp, get the
review redone, then re-approve: `fm -p my_film approve G3` works again on a
drifted gate. If only wording changed and the meaning did not, use
`fm -p my_film amend G3 <ref...> --note '...'` (human only).

### `fm approve` refuses because the review is stale

**Cause.** The gate review (`qa/reviews/G#_REVIEW.md`) lists every item the gate
approves in its `derived_from`. If any of them changed after the review, the
review is stale.

**Fix.** Ask Claude to re-run the review (`/film-review`), then approve. If the
review is WARN or FAIL you also need `--ack-review`.

### Validation errors you will meet

| Code / message | Meaning | Fix |
|---|---|---|
| `LOCKED_CANON_MODIFIED` | a LOCKED canon entry was edited in place | revert the edit; use `fm change propose` and approve it |
| `STATUS_NOT_BACKED` | a file claims `APPROVED`/`LOCKED` without a ledger record | set it back to `PROPOSED`; only `fm approve` creates approval |
| stale node / `derived_from` out of date | an upstream changed | revise if the meaning changed, then `fm stamp <file>` |
| `fm stamp` refuses to refresh | upstream changed but your content did not | either revise the content, or `fm stamp <file> --note 'why no revision is needed'` (recorded; do not use to silence staleness) |
| G5 submit blocked | `fm check continuity` has a FAIL | fix the shot or the continuity canon it names |

### A stale locked note cannot be corrected

**Cause.** `fm change propose` cannot change `notes`.

**Fix.** `fm -p my_film canon annotate <canon id> --notes '...'`. Notes are not
part of the decision hash and every annotation is logged with old and new text.

### `fm status --repair-cache` is refused inside Claude Code

**Cause.** Rebuilding `state.yaml` from the ledger is blocked for agents so a
person investigates first. Never edit `state.yaml`, `STATUS.md`,
`CHANGELOG.md`, `.fm/` or `changes/` by hand.

**Fix.** Run it yourself in your own terminal if the ledger (`fm log` says
`chain OK`) and `state.yaml` disagree. If `fm log` reports a broken chain
(exit code 5), stop and do not commit: restore the ledger from git.

### The ledger identity is wrong or empty

**Cause.** The name recorded for your decisions comes from
`config/film_maker.yaml: default_human`, or `git config user.name` when that is
empty.

**Fix.** `git config user.name "Your Name"` (Last Signal's decisions are
recorded as `human:gokhan_guler`).

## Console and platform quirks

- Console output uses ASCII dashes on purpose (Windows terminals mangled
  Unicode dashes).
- Blender 5.2 prints a deprecation warning for `Material.use_nodes`. It is
  harmless on 5.2 LTS (removed in 6.0).
- A `PREVIEW_REVIEW.md` shown as "stale" in `fm status` after you fixed a
  builder or a shot means the stills it reviewed have changed: re-render the
  affected shots and have QA re-read them.

## Still stuck

Report what happened as: command, full error, file, likely cause, next step
(the same format Claude uses). `fm validate` and `fm log` output plus
`fm doctor` cover most bug reports.
