# FILM_MAKER

An AI-assisted film and animation production system: a reusable pipeline
that takes a creative brief through story, world, characters, look,
cinematography and storyboard to Blender scenes, renders, QA and delivery —
with human approval at every creative milestone.

**Status: M2 (creative pipeline) built.** The deterministic core (M1) plus
10 specialist agents, 17 skills and 14 `/film-*` commands take a brief to an
approved storyboard and shot specs. Blender builders (M3), preview/QA (M4),
revision through builds (M5) and animation/post (M6) follow. See the [roadmap](#roadmap).

## The idea in one paragraph

Specialist agents *propose* creative work as files. A deterministic CLI,
`fm`, validates that work, tracks what it was derived from, and records
every human decision in an append-only, hash-chained ledger. Approved
decisions become **locked canon**; nothing downstream can silently
contradict them. When a decision changes, `fm impact` names exactly which
documents, shots, Blender scenes, renders and QA reports are affected, and
`fm plan --scope ...` regenerates only those. Blender is the production
engine, not the database: every scene is reproducible from text files.

## Quick start

```powershell
cd C:\Users\ggule\film_maker
python -m pip install -e ".[dev]"
python -m pytest              # 144 tests
fm doctor                     # checks the pinned Blender (5.2.x)
fm init my_film --title "My Film"
fm status
python scripts\demo_m1.py --clean   # full walkthrough on a sandbox project
```

Then open Claude Code in the repository and start a film:

```
/film-new last_signal A courier alone in a rain-soaked harbour receives a message from her dead brother...
```

Full walkthrough: [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md).

## Make your own film

You can start a second film without the author. Read these three, in order:

1. [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) - prerequisites (Python 3.11+, Git, Claude Code, pinned Blender 5.2.x), installing `fm`, laptop vs cloud, and the first ten commands.
2. [docs/NEW_FILM_WALKTHROUGH.md](docs/NEW_FILM_WALKTHROUGH.md) - every phase from `/film-new` to the first preview: the command, the agent, the artifacts, the gate, the exact decision command, what to look at before you approve, and how to revise.
3. [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - the problems already met (PowerShell quoting, `-p` with several projects, git locks, EEVEE frame corruption, tool timeouts, cloud pip, hanging test runs) and their fixes.

Short version: `/film-new my_film <your idea>` in Claude Code, then decide each gate yourself in your own terminal (`fm -p my_film approve G1` ...). Note that the Blender set builders are still specific to Last Signal: a new film gets a generic stage until its own builders are written (see the walkthrough).

## Documentation

| Doc | What it covers |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Principles, layers, agents, Blender strategy, extension points |
| [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) | Prerequisites, install, laptop vs cloud, the first ten commands |
| [docs/NEW_FILM_WALKTHROUGH.md](docs/NEW_FILM_WALKTHROUGH.md) | Phase-by-phase guide from `/film-new` to preview, gates and revisions |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Real problems met in this project and their fixes |
| [docs/WORKFLOW.md](docs/WORKFLOW.md) | Phases, gates, proposals vs locked decisions, change requests |
| [docs/DATA_MODEL.md](docs/DATA_MODEL.md) | Canon, intent, artifacts, shots, ledger, dependency graph |
| [docs/BLENDER.md](docs/BLENDER.md) | Resolver, Blender builders, previews, draft vs pinned |
| [docs/CLI.md](docs/CLI.md) | Every `fm` command, who may run it, exit codes |
| [docs/COMMANDS.md](docs/COMMANDS.md) | The `/film-*` commands in Claude Code |
| [docs/AGENTS.md](docs/AGENTS.md) | The specialist agents, what they own, what they can never do |
| [docs/SKILLS.md](docs/SKILLS.md) | Shared rules and domain skills |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Conventions, tests, Git workflow |
| [CLAUDE.md](CLAUDE.md) | Rules for the Claude Code orchestrator session |

## Repository layout

```
film_maker/
├── CLAUDE.md               orchestrator rules (Executive Producer = main session)
├── .claude/agents/         10 specialist agents
├── .claude/skills/         film-conventions, project-management, 15 domain skills
├── .claude/commands/       14 /film-* commands
├── .claude/settings.json   blocks agents from human-only commands
├── config/                 repo marker, Blender pin, models, render profiles
├── core/fm/                the deterministic `fm` package
├── schemas/json/           exported JSON Schemas (model-independent contracts)
├── templates/project/      files copied into every new film
├── projects/<film>/        one directory per film
├── library/                shared assets and references (cross-film)
├── scripts/demo_m1.py      M1 demonstration
├── tests/                  pytest suite
└── docs/
```

## Roadmap

| | Milestone | State |
|---|---|---|
| M1 | Core: state, canon, ledger, dependency graph, impact, validation, CLI | ✅ done |
| M2 | Creative pipeline: 9 agents, 16 skills, 13 `/film-*` commands, gate reviews, intent + continuity checks | ✅ done - demo film Last Signal approved through G5 (see [M2 acceptance](docs/M2_ACCEPTANCE.md)) |
| M3 | Blender build: resolver, idempotent scene builders, proxy characters | in progress: resolver + preview stills for all 38 shots work (see docs/previews) |
| M4 | Preview + 3-layer QA loop | |
| M5 | Revision: feedback → impact → scoped regeneration | |
| M6 | Animation + animatic/post | |
| M7 | Documentation pass for a second film from docs alone | |

Requirements: Python ≥ 3.11, Git, Blender 5.2.x LTS (from M3), ffmpeg (from M6).
