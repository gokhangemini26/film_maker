# Getting started

This page takes you from a fresh clone to the first ten commands of a new
film. When you are ready to make the film, continue with
[NEW_FILM_WALKTHROUGH.md](NEW_FILM_WALKTHROUGH.md); if something breaks, see
[TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## 1. What you need

| Requirement | Why | Check |
|---|---|---|
| Python 3.11 or newer | the `fm` CLI (`requires-python >= 3.11`) | `python --version` |
| Git | the ledger, canon and bibles are version-controlled; `fm doctor` reports it | `git --version` |
| Claude Code, opened at the repository root | runs the specialist agents and the `/film-*` commands; it reads `CLAUDE.md` and `.claude/settings.json` | `claude` |
| Blender **5.2.x** (the pinned series) | the only Blender whose previews count as G6 evidence. Any other series is refused by design | `fm doctor` |
| Pillow (extra `vision`) | `fm qa stills` and the cloud contact-sheet script | `pip install -e ".[vision]"` |
| ffmpeg | reported by `fm doctor`; used from M6 (animatic/post), not needed for previews | `ffmpeg -version` |

You also need your own git identity (`git config user.name`). It is the name
written into the approval ledger when you approve a gate
(`config/film_maker.yaml: default_human` overrides it).

## 2. Install `fm`

The repository installs as an editable package (`pyproject.toml`,
`package-dir = core`, console script `fm = fm.cli:main`).

**Laptop (Windows, PowerShell):**

```powershell
cd C:\Users\ggule\film_maker
python -m pip install -e ".[dev,vision]"
fm --version
fm doctor
```

**Linux / macOS, or any machine where you want an isolated environment:**

```bash
cd film_maker
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev,vision]"
fm --version
fm doctor
```

**Cloud workspace (system Python, no venv):** pip refuses to install into the
system interpreter unless you say so:

```bash
pip install --break-system-packages -e ".[dev,vision]"
```

This install was checked in a clean virtual environment: it takes about ten
seconds and `fm --version` prints `fm, version 0.1.0`. If `fm` is not on
`PATH`, use `python -m fm.cli` instead.

### What `fm doctor` should say

```
fm 0.1.0 | Python 3.11.x | ...
repository: <path>
actor: ...
git: found
ffmpeg: found
blender: 5.2.x LTS OK
```

`config/blender.yaml` points at
`C:/Program Files/Blender Foundation/Blender 5.2/blender.exe`. On any other
machine (or another install location) set `FM_BLENDER` to the executable, or
edit that file. If the executable is missing or is not 5.2.x, `fm doctor`
prints `blender: REFUSED ...` and exits with code 4. That is expected on a
machine without the pinned Blender; you can still do everything up to the
storyboard there.

### Run a few tests (optional)

Do not run the whole suite in one go on a small or cloud machine: it has been
seen to hang. Run targeted files under a timeout:

```bash
timeout 120 python -m pytest tests/test_project_and_ledger.py tests/test_canon.py
```

On PowerShell there is no `timeout`; run one file at a time
(`python -m pytest tests\test_canon.py -x`) and stop it with Ctrl+C if it stalls.

## 3. Laptop versus cloud

FILM_MAKER is used from two places. They do different jobs.

| | Laptop (Windows) | Cloud workspace (Linux) |
|---|---|---|
| Repository | `C:\Users\ggule\film_maker` | `/home/claude/film_maker` |
| Good for | **human decisions** (`fm approve`, `fm revise`, `fm change approve`...); **pinned Blender 5.2.x previews** | running the agents at length; deterministic `fm` checks; **draft** previews |
| Blender | pinned 5.2.x, `fm blender preview` | `bpy` Python module (currently 5.0.1), `fm blender preview --draft` |
| Preview status | **G6 evidence** | **draft only**. Records say "draft"; never approve G6 on them |
| Git | your own terminal has credentials; **the laptop pushes** | a Claude Code shell on the laptop has no git credentials, so you push yourself |
| Long commands | a Claude Code tool call times out after about 2 minutes: run renders in the background or in your own terminal | same |

Rules of thumb:

1. **Human commands need a person at an interactive terminal.** `fm approve`,
   `fm revise`, `fm reject`, `fm amend`, `fm authorize`,
   `fm canon approve|lock|reject`, `fm change approve|reject` refuse any
   non-interactive caller (exit code 3). Open a normal PowerShell window,
   `cd` into the repository, and type them there.
2. **One writer at a time.** The approval ledger
   (`projects/<film>/.fm/ledger.jsonl`) is append-only and hash-chained, and
   history containing a ledger must never be rewritten
   (`CONTRIBUTING.md`). Pull before you start on a machine, push when you
   stop, and do not decide gates on the laptop while the cloud is still
   producing on an older commit. If the two ever diverge, stop and ask before
   merging: `fm log` verifies the chain and tells you if it is damaged.
3. **Previews for G6 come from the pinned Blender on the laptop.** Cloud
   drafts are for iterating on builders and shots quickly.

## 4. Your first ten commands for a new film

Assume the film is called `my_film`. Steps 1-4 prepare the machine, step 5
opens Claude Code, steps 6-10 are the start of production.

| # | Where | Command | What it does |
|---|---|---|---|
| 1 | terminal | `cd film_maker` then `git pull` | start from the latest commit |
| 2 | terminal | `python -m pip install -e ".[dev,vision]"` | install `fm` (cloud: add `--break-system-packages`) |
| 3 | terminal | `fm doctor` | environment and Blender pin check |
| 4 | terminal | `fm list` | see which projects already exist (`last_signal` is the reference film, approved through G6) |
| 5 | terminal | `claude` | open Claude Code **at the repository root** so it loads `CLAUDE.md` and the agents |
| 6 | Claude Code | `/film-new my_film <your idea, taste, references, duration...>` | runs `fm init my_film --title "..."`, advances to BRIEF, the creative-director analyses your brief, asks at most five questions, records your intents, advances to CREATIVE_DIRECTION |
| 7 | terminal | `fm -p my_film status` | plain status: phase, gates, next step. `-p` is needed as soon as more than one project exists |
| 8 | Claude Code | `/film-direction my_film` | creative direction and tone, QA review, `fm submit` for **G1**, then it stops |
| 9 | **your** terminal | `fm -p my_film approve G1` | you decide G1 by typing `G1` at the prompt. Use `--ack-review` if the QA verdict is WARN or FAIL; `--notes '...'` to record your answers |
| 10 | Claude Code | `/film-next my_film` | advances and runs whatever comes next (`/film-story`) |

Step 6 does the project creation for you. To do it by hand instead:
`fm init my_film --title "My Film"` then `fm -p my_film advance`. Never pass
`--sandbox` for a real film: sandbox projects are permanent demo projects that
allow simulated approvals.

Everything after step 10 repeats the same loop for each phase; it is laid out
phase by phase in [NEW_FILM_WALKTHROUGH.md](NEW_FILM_WALKTHROUGH.md).

## 5. Daily commands

```
fm -p my_film status                  # where am I, what is next
fm -p my_film validate -q             # anything broken or stale?
fm -p my_film intent                  # which creative intents are served, by what
fm -p my_film impact canon:look.color.primary   # what would this change touch?
fm -p my_film plan --scope scene:SC03           # what is stale in this scope?
fm -p my_film log --tail 20           # who decided what, when (verifies the chain)
```

Project resolution order: `-p` flag, then the `FM_PROJECT` environment
variable, then the project containing your current directory, then the only
project. With two or more projects and none of those, `fm` stops with
`several projects exist (...); pass --project`. `-p` goes **before** the
command: `fm -p my_film approve G1`.

## 6. Git

Commit canon, bibles, shots, `.fm/ledger.jsonl`, `state.yaml`,
`CHANGELOG.md` and the preview stills you want to keep. `.blend` files and
final renders are ignored (reproducible from source). See `CONTRIBUTING.md`.
Never rewrite history that contains a ledger.

```bash
git status
git add -A && git commit -m "my_film: G1 approved (human decision)"
git push
```

On the laptop, push from your own terminal.

## 7. Where the rules live

| File | For |
|---|---|
| `CLAUDE.md` | the orchestrator's hard rules (agents propose, humans decide) |
| `docs/COMMANDS.md` | every `/film-*` command |
| `docs/CLI.md` | every `fm` command, who may run it, exit codes |
| `docs/AGENTS.md`, `docs/SKILLS.md` | who does what |
| `docs/WORKFLOW.md`, `docs/DATA_MODEL.md` | phases, gates, canon, staleness |
| `docs/BLENDER.md` | resolver, builders, previews |
