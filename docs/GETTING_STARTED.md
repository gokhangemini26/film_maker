# Getting started

## 1. Install (Windows, PowerShell)

```powershell
cd C:\Users\ggule\film_maker
python -m pip install -e ".[dev]"
fm --version
python -m pytest
fm doctor
```

`fm doctor` must report `blender: 5.2.x LTS OK`. If Blender lives
elsewhere, edit `config/blender.yaml` or set `FM_BLENDER`. Any other series
is refused by design.

If `fm` is not on PATH, use `python -m fm.cli` instead.

## 2. See the whole system work

```powershell
python scripts\demo_m1.py --clean
```

Creates a sandbox project `projects/m1_demo`, walks it through gates G1–G5,
shows refusals, a locked-canon violation, a change request, impact analysis
and scoped planning. Delete `projects\m1_demo` afterwards (or keep it to
explore with `fm -p m1_demo status`).

## 3. Start a real film

```powershell
fm init last_signal --title "Last Signal"
cd projects\last_signal
fm status
```

Until the agents arrive (M2), content is written by hand or by Claude Code
following `CLAUDE.md`:

1. `fm advance` → BRIEF. Fill `00_brief/brief.yaml` (`given`/`assumed`/`unknown`)
   and put the must-haves in `canon/intent.yaml` as `USER_REQUIREMENT`s.
2. `fm advance` → CREATIVE_DIRECTION. Write `00_brief/CREATIVE_DIRECTION.md`
   with an `fm:` block (see `docs/DATA_MODEL.md`) and `canon/tone.yaml`.
3. `fm stamp 00_brief/CREATIVE_DIRECTION.md`, `fm validate`, `fm submit`.
4. Review, then in **your own terminal**: `fm approve G1` (type `G1`).
5. `fm advance` and continue.

## 4. Daily commands

```powershell
fm status                              # where am I, what's next
fm validate                            # anything broken or stale?
fm impact canon:look.color.primary     # what would this change touch?
fm plan --scope scene:SC03             # what needs regenerating here?
fm log                                 # who decided what, when
```

## 5. Working with Claude Code

Open Claude Code in `C:\Users\ggule\film_maker`. It reads `CLAUDE.md` and
`.claude/settings.json`, which set `FM_ACTOR=agent:claude-code` and block
human-only commands. When Claude reaches a gate it stops and tells you the
command to run yourself.

## 6. Git

```powershell
git status
git add -A; git commit -m "..."
```

Commit canon, docs, shots, the ledger and state. Renders and `.blend` files
are ignored (reproducible from source). See `CONTRIBUTING.md`.
