"""`fm` command-line interface. Thin wrapper over fm.ops / fm.validate."""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import click
import yaml

from . import __version__
from .authority import current_actor
from .blender import require_blender
from .deps import build_graph
from .errors import FMError
from .io import dump_yaml, short, write_json
from .ledger import Ledger
from .phases import GATES
from .project import find_repo, list_projects, resolve_project
from .schemas import EXPORTED, layer_of

log = logging.getLogger("fm")


def _setup_logging(project_dir: Path | None) -> None:
    if project_dir is None:
        return
    logdir = project_dir / ".fm" / "logs"
    logdir.mkdir(parents=True, exist_ok=True)
    h = logging.FileHandler(logdir / "fm.log", encoding="utf-8")
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(h)
    log.setLevel(logging.INFO)


class Ctx:
    def __init__(self, project_name: str | None):
        self.project_name = project_name
        self._repo = None

    @property
    def repo(self) -> Path:
        if self._repo is None:
            self._repo = find_repo()
        return self._repo

    def project(self):
        p = resolve_project(self.repo, self.project_name)
        _setup_logging(p.dir)
        log.info("actor=%s argv=%s", current_actor(), " ".join(sys.argv[1:]))
        return p


def main() -> None:
    try:
        cli(standalone_mode=False)
    except click.exceptions.Abort:
        click.echo("aborted", err=True)
        sys.exit(130)
    except click.ClickException as exc:
        exc.show()
        sys.exit(exc.exit_code)
    except FMError as exc:
        click.secho(f"fm: {exc}", fg="red", err=True)
        log.error("%s: %s", type(exc).__name__, exc)
        sys.exit(exc.exit_code)


sandbox_opt = click.option("--sandbox-confirm", is_flag=True,
                           help="Sandbox projects only: simulate the typed confirmation (recorded as simulated).")


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("-p", "--project", "project_name", help="Project slug (default: FM_PROJECT / cwd / the only project).")
@click.version_option(__version__, prog_name="fm")
@click.pass_context
def cli(ctx, project_name):
    """FILM_MAKER - deterministic production core.

    Agents propose; humans approve. State lives in an append-only ledger.
    """
    ctx.obj = Ctx(project_name)


# ------------------------------------------------------------------ init / status
@cli.command()
@click.argument("slug")
@click.option("--title", required=True, help="Working title of the film.")
@click.option("--sandbox", is_flag=True, help="Demo/test project: allows simulated confirmations. Permanent.")
@click.pass_obj
def init(c: Ctx, slug, title, sandbox):
    """Create a new film project under projects/SLUG."""
    from .ops import init_project

    p = init_project(c.repo, slug, title, sandbox=sandbox)
    click.echo(f"created projects/{slug}  ({'SANDBOX' if sandbox else 'production'})")
    click.echo(f"phase: IDEA  |  actor: {current_actor()}  |  next: fill 00_brief/brief.yaml, then `fm advance`")
    _ = p


@cli.command()
@click.option("--repair-cache", is_flag=True, help="Rewrite state.yaml from the ledger (the ledger is authoritative).")
@click.pass_obj
def status(c: Ctx, repair_cache):
    """Show project status (regenerates STATUS.md)."""
    from .ops import load_state, refresh

    p = c.project()
    if repair_cache:
        refresh(p)
        click.echo("state.yaml rewritten from the ledger")
    else:
        load_state(p)
        refresh(p)
    click.echo(p.status_path.read_text(encoding="utf-8"))


@cli.command("list")
@click.pass_obj
def list_cmd(c: Ctx):
    """List projects in this repository."""
    for name in list_projects(c.repo):
        click.echo(name)


@cli.command()
@click.option("--json", "as_json", is_flag=True)
@click.option("--quiet", "-q", is_flag=True, help="Only errors and the summary.")
@click.pass_obj
def validate(c: Ctx, as_json, quiet):
    """Validate schemas, canon locks, ledger integrity, dependencies and gates."""
    from .validate import validate as run

    p = c.project()
    rep = run(p)
    if as_json:
        click.echo(json.dumps([f.__dict__ for f in rep.findings], indent=2))
    else:
        for f in rep.findings:
            if quiet and f.level != "ERROR":
                continue
            color = {"ERROR": "red", "WARN": "yellow"}.get(f.level)
            click.secho(str(f), fg=color)
        n = {lvl: sum(1 for f in rep.findings if f.level == lvl) for lvl in ("ERROR", "WARN", "INFO")}
        click.secho(f"validate: {n['ERROR']} error(s), {n['WARN']} warning(s), {n['INFO']} info",
                    fg="red" if n["ERROR"] else "green")
    if not rep.ok:
        sys.exit(1)


# ------------------------------------------------------------------ phases / gates
@cli.command()
@click.pass_obj
def submit(c: Ctx):
    """Submit the current phase's deliverables for human review at its gate."""
    from .ops import submit as run

    from .phases import GATE_FOR_PHASE
    from .reviews import review_verdict

    p = c.project()
    st = run(p)
    gate = GATE_FOR_PHASE[st.phase]
    verdict = review_verdict(p, gate.id, p.load())
    click.echo(f"{st.phase} submitted for {gate.id}; awaiting human decision"
               + (f" (qa review verdict, advisory: {verdict})" if verdict else ""))
    click.echo(f"  human, in a terminal: fm approve {gate.id}   |   fm revise {gate.id} --notes \"...\"")


@cli.command()
@click.pass_obj
def advance(c: Ctx):
    """Move to the next phase (only if its gate is approved and healthy)."""
    from .ops import advance as run

    st = run(c.project())
    click.echo(f"advanced to {st.phase}")


def _gate_cmd(decision):
    @click.argument("gate", type=click.Choice(list(GATES)))
    @click.option("--notes", help="Feedback / reasons (required for revise and reject; on approve, "
                                  "record your answers to the review's open questions).")
    @click.option("--ack-review", is_flag=True, help="Acknowledge a WARN/FAIL QA review (required to approve past one).")
    @sandbox_opt
    @click.pass_obj
    def _cmd(c: Ctx, gate, notes, ack_review, sandbox_confirm):
        from .ops import decide_gate

        st = decide_gate(c.project(), gate, decision, notes, sandbox_confirm=sandbox_confirm,
                         ack_review=ack_review)
        click.echo(f"{gate}: {st.gates[gate].status} by {st.gates[gate].decided_by}")
    return _cmd


cli.command("approve", help="HUMAN: approve a gate (records hashes, locks its canon domains).")(_gate_cmd("approved"))
cli.command("revise", help="HUMAN: send a gate back for revision with notes.")(_gate_cmd("revise"))
cli.command("reject", help="HUMAN: reject a gate's submission with notes.")(_gate_cmd("rejected"))


@cli.command()
@click.argument("what", type=click.Choice(["final-render"]))
@click.option("--scope", default="film")
@sandbox_opt
@click.pass_obj
def authorize(c: Ctx, what, scope, sandbox_confirm):
    """HUMAN: authorize an expensive operation (final render)."""
    from .ops import authorize as run

    run(c.project(), what, scope, sandbox_confirm=sandbox_confirm)
    click.echo(f"authorized {what} ({scope})")


# ------------------------------------------------------------------ canon
@cli.group()
def canon():
    """Inspect and decide canon entries."""


@canon.command("list")
@click.option("--domain")
@click.pass_obj
def canon_list(c: Ctx, domain):
    from .ops import load_state

    p = c.project()
    st = load_state(p)
    loaded = p.load()
    for cid, it in sorted(loaded.canon.items()):
        if domain and it.entry.domain != domain:
            continue
        lk = st.canon.get(cid)
        status = (lk.status if lk else it.entry.status).value
        click.echo(f"{status:10} v{it.entry.version:<3} {short(it.hash)}  {cid}  - {it.entry.statement}")


@canon.command("show")
@click.argument("cid")
@click.pass_obj
def canon_show(c: Ctx, cid):
    p = c.project()
    loaded = p.load()
    if cid not in loaded.canon:
        raise FMError(f"unknown canon id '{cid}'")
    click.echo(dump_yaml(loaded.canon[cid].entry.model_dump(mode="json", exclude_none=True)))


@canon.command("annotate", help="Correct the free-text notes of a canon entry (allowed on LOCKED entries; "
                                "logged in the ledger; cannot change a decision).")
@click.argument("cid")
@click.option("--notes", required=True, help="The corrected notes text.")
@click.pass_obj
def canon_annotate(c: Ctx, cid, notes):
    from .ops import annotate_canon

    annotate_canon(c.project(), cid, notes)
    click.echo(f"{cid}: notes updated (recorded in the ledger)")


@cli.command("amend", help="HUMAN: accept a wording-only edit to approved documents without re-approving the gate.")
@click.argument("gate", type=click.Choice(list(GATES)))
@click.argument("refs", nargs=-1, required=True)
@click.option("--note", required=True, help="What changed and why the meaning is unchanged.")
@sandbox_opt
@click.pass_obj
def amend(c: Ctx, gate, refs, note, sandbox_confirm):
    from .ops import amend_gate

    st = amend_gate(c.project(), gate, list(refs), note, sandbox_confirm=sandbox_confirm)
    click.echo(f"{gate}: amended ({st.gates[gate].amendments} amendment(s) since approval)")


for _action in ("approve", "lock", "reject"):
    def _make(action):
        @canon.command(action, help=f"HUMAN: {action} a canon entry.")
        @click.argument("cid")
        @sandbox_opt
        @click.pass_obj
        def _cmd(c: Ctx, cid, sandbox_confirm):
            from .ops import canon_decide

            st = canon_decide(c.project(), cid, action, sandbox_confirm=sandbox_confirm)
            click.echo(f"{cid}: {st.canon[cid].status.value}")
        return _cmd
    _make(_action)


# ------------------------------------------------------------------ changes
@cli.group()
def change():
    """Change requests for approved/locked decisions."""


def _parse_sets(pairs: tuple[str, ...]) -> dict:
    out = {}
    for pair in pairs:
        key, sep, raw = pair.partition("=")
        if not sep:
            raise FMError(f"--set expects field=value, got '{pair}'")
        out[key.strip()] = yaml.safe_load(raw) if raw.strip() else None
    return out


@change.command("propose")
@click.argument("cid")
@click.option("--set", "sets", multiple=True, required=True,
              help="field=value (value parsed as YAML). Fields: statement, value, rationale, serves, depends_on, applies_to, tag.")
@click.option("--reason", required=True)
@click.pass_obj
def change_propose(c: Ctx, cid, sets, reason):
    """Propose changing an approved/locked canon entry (agents allowed)."""
    from .ops import propose_change

    cr = propose_change(c.project(), cid, _parse_sets(sets), reason)
    click.echo(f"{cr.id} proposed for {cid} - awaiting human decision")
    _print_impact(cr.impact)


@change.command("list")
@click.pass_obj
def change_list(c: Ctx):
    loaded = c.project().load()
    for cid, (cr, _) in sorted(loaded.changes.items()):
        click.echo(f"{cid}  {cr.status.value:9} {cr.target}  - {cr.reason}")


@change.command("show")
@click.argument("change_id")
@click.pass_obj
def change_show(c: Ctx, change_id):
    loaded = c.project().load()
    if change_id not in loaded.changes:
        raise FMError(f"unknown change '{change_id}'")
    click.echo(dump_yaml(loaded.changes[change_id][0].model_dump(mode="json", exclude_none=True)))


for _decision in ("approve", "reject"):
    def _make_change(decision):
        @change.command(decision, help=f"HUMAN: {decision} a change request.")
        @click.argument("change_id")
        @click.option("--notes")
        @sandbox_opt
        @click.pass_obj
        def _cmd(c: Ctx, change_id, notes, sandbox_confirm):
            from .ops import decide_change

            cr = decide_change(c.project(), change_id, "approved" if decision == "approve" else "rejected",
                               notes, sandbox_confirm=sandbox_confirm)
            click.echo(f"{cr.id}: {cr.status.value}")
            if cr.status.value == "APPROVED":
                click.echo(f"{cr.target} is now v{cr.base_version + 1} ({short(cr.new_hash)}); "
                           "downstream nodes are stale until regenerated:")
                _print_impact(cr.impact)
        return _cmd
    _make_change(_decision)


# ------------------------------------------------------------------ graph
def _print_impact(impact: dict) -> None:
    if not impact:
        click.echo("  impact: nothing downstream")
        return
    for layer, refs in impact.items():
        click.echo(f"  {layer:9} ({len(refs)}): " + ", ".join(refs))


@cli.command()
@click.argument("refs", nargs=-1, required=True)
@click.option("--json", "as_json", is_flag=True)
@click.pass_obj
def impact(c: Ctx, refs, as_json):
    """What is affected downstream if REFS change (e.g. canon:look.color.primary)."""
    from .ops import impact_of

    p = c.project()
    loaded = p.load()
    refs = [r if ":" in r else f"canon:{r}" for r in refs]
    for r in refs:
        if not loaded.exists(r):
            raise FMError(f"unknown node '{r}'")
    res = impact_of(loaded, list(refs))
    if as_json:
        click.echo(json.dumps(res, indent=2))
        return
    click.echo(f"impact of {', '.join(refs)}:")
    _print_impact(res)


@cli.command("resolve")
@click.option("--scope", default="film", help="film | shot:ID | shots:A..B | scene:SC01 | sequence:SQ01 | character:ID")
@click.pass_obj
def resolve_cmd(c: Ctx, scope):
    """Resolve shot specs + canon into engine-ready JSON (09_resolved/), recorded as derived nodes."""
    from .resolve import resolve

    r = resolve(c.project(), scope)
    click.echo(f"resolved {len(r['resolved'])} shot(s), {len(r['unchanged'])} unchanged; "
               f"film = {r['film_frames']} frames at {r['fps']:g} fps ({r['film_seconds']:g} s)")


@cli.group("feedback")
def feedback_group():
    """Review findings -> scoped regeneration (M5). Agents may add, plan and resolve."""


@feedback_group.command("add")
@click.argument("target")
@click.option("--note", required=True)
@click.option("--severity", type=click.Choice(["low", "medium", "high", "blocker"]), default="medium",
              show_default=True)
@click.option("--owner", help="Override the suggested owner (default: routed from the note/target).")
@click.pass_obj
def feedback_add(c: Ctx, target, note, severity, owner):
    """Record a feedback item on TARGET (shot:ID, canon:ID, artifact:ID, scene:SC01 ...)."""
    from .feedback import add

    it = add(c.project(), target, note, severity=severity, owner=owner)
    click.echo(f"{it['id']} OPEN  {it['target']}  [{it['severity']}]  owner: {it['suggested_owner']} "
               f"({it['owner_reason']})")
    click.echo(f"  next: fm feedback plan {it['id']}")


@feedback_group.command("list")
@click.option("--open", "open_only", is_flag=True)
@click.pass_obj
def feedback_list(c: Ctx, open_only):
    from .feedback import list_items

    items = list_items(c.project(), open_only=open_only)
    for it in items:
        click.echo(f"{it['id']}  {it['status']:8} {it['severity']:7} {it['target']}  "
                   f"-> {it['suggested_owner']}  - {it['note']}")
    if not items:
        click.echo("no feedback" + (" open" if open_only else ""))


@feedback_group.command("plan")
@click.argument("fid")
@click.option("--json", "as_json", is_flag=True)
@click.pass_obj
def feedback_plan(c: Ctx, fid, as_json):
    """Minimal stale set, handling agent/command and whether a change request is needed."""
    from .feedback import plan_for

    r = plan_for(c.project(), fid)
    if as_json:
        click.echo(json.dumps(r, indent=2))
        return
    click.echo(f"{fid}  target {r['target']}  (scope {r['scope']})")
    click.echo(f"  handled by: {r['owner']}  via {r['command']}")
    click.echo(f"  change request: {'YES' if r['change_request_needed'] else 'no'} - {r['change_request_note']}")
    if r["impact"]:
        click.echo("  downstream if the target changes:")
        _print_impact(r["impact"])
    if not r["stale"]:
        click.echo("  stale now: nothing (revise the target, then re-stamp and regenerate what `fm plan` lists)")
    for layer, refs in r["by_layer"].items():
        click.echo(f"  stale {layer:9} ({len(refs)}): " + ", ".join(refs))


@feedback_group.command("resolve")
@click.argument("fid")
@click.option("--by", required=True, help="What resolved it (commit, revised shot, review ref ...).")
@click.option("--force-stale", is_flag=True, help="Resolve even though nodes in scope are still stale (recorded).")
@click.pass_obj
def feedback_resolve(c: Ctx, fid, by, force_stale):
    """Mark RESOLVED (agents allowed; actor recorded; refused while the plan's nodes are stale)."""
    from .feedback import resolve

    it = resolve(c.project(), fid, by, force_stale=force_stale)
    res = it["resolution"]
    click.echo(f"{fid} RESOLVED by {res['actor']} ({res['by']})"
               + ("  [forced past stale nodes]" if res["forced_stale"] else ""))
    if res["target_changed"] is False:
        click.secho("  note: the target's content is unchanged since the feedback was opened", fg="yellow")


@cli.group("qa")
def qa_group():
    """Quality checks on produced material (M4)."""


@qa_group.command("review-status")
@click.option("--file", "rel", default="qa/reviews/PREVIEW_REVIEW.md", show_default=True)
@click.option("--json", "as_json", is_flag=True)
@click.pass_obj
def qa_review_status(c: Ctx, rel, as_json):
    """PASS/WARN/FAIL counts of the preview review and whether it is stale vs the current project."""
    from .qa_review import review_status

    r = review_status(c.project(), rel)
    if as_json:
        click.echo(json.dumps(r, indent=2))
        return
    n = r["counts"]
    click.echo(f"{r['file']}: verdict {r['verdict']}  |  PASS {n['PASS']}  WARN {n['WARN']}  FAIL {n['FAIL']}"
               f"  ({r['shots']} shots in table)" + ("" if r["table_found"] else "  [no per-shot table found]"))
    if r["stale"] is None:
        click.echo("  staleness: unknown - " + "; ".join(r["stale_reasons"]))
    elif r["stale"]:
        click.secho("  STALE: " + "; ".join(r["stale_reasons"][:8]), fg="yellow")
    else:
        click.echo("  fresh: every reviewed hash matches the current project")
    if r["uncovered_previews"]:
        click.echo(f"  {len(r['uncovered_previews'])} preview(s) not listed in the review's derived_from "
                   "(freshness unprovable): " + ", ".join(r["uncovered_previews"][:8]))


@qa_group.command("stills")
@click.pass_obj
def qa_stills(c: Ctx):
    """Deterministic checks on 10_blender/previews (blank, blown-out, black frames, colour drift)."""
    from .qa_stills import check

    r = check(c.project())
    for row in r["rows"]:
        for sev, msg in row["findings"]:
            click.echo(f"{sev:4} {row['shot']}: {msg}")
    s = r["summary"]
    click.echo(f"{s['shots']} stills: {s['fail']} FAIL, {s['warn']} WARN")
    if s["fail"]:
        sys.exit(1)


def _run_qa_motion(c: Ctx, strict: bool, record: bool):
    from .qa_motion import check as motion_check

    r = motion_check(c.project(), strict=strict, record=record)
    for row in r["rows"]:
        for sev, msg in row["findings"]:
            click.echo(f"{sev:4} {row['shot']}: {msg}")
    s = r["summary"]
    click.echo(f"{s['shots']} shots: {s['fail']} FAIL, {s['warn']} WARN (qa/motion_report.json)")
    if s["fail"]:
        sys.exit(1)


@qa_group.command("motion")
@click.option("--strict", is_flag=True, help="A missing or stub anim file is a FAIL (default: WARN while M6 is in progress).")
@click.option("--no-record", "no_record", is_flag=True, help="Write the report but do not record the qa:motion derived node.")
@click.pass_obj
def qa_motion(c: Ctx, strict, no_record):
    """Tier 0 motion checks on the anim files (timing, vocabulary, prop continuity, speeds, UI, running time). Exit 1 on FAIL."""
    _run_qa_motion(c, strict, not no_record)


@cli.group("blender")
def blender_group():
    """Blender-side production (M3): previews from resolved shot files."""


@blender_group.command("preview")
@click.option("--shots", help="Comma-separated shot ids (default: all).")
@click.option("--width", default=768, show_default=True)
@click.option("--draft", is_flag=True, help="Use the bpy module (not the pinned Blender): fast drafts only, never G6 evidence.")
@click.option("--jobs", default=1, show_default=True, help="Parallel Blender processes.")
@click.pass_obj
def blender_preview(c: Ctx, shots, width, draft, jobs):
    """Render one still per shot into 10_blender/previews/ and record each as a derived node."""
    from .blenderrun import preview as run

    r = run(c.project(), c.repo, shots=shots.split(",") if shots else None, width=width, draft=draft, jobs=jobs)
    click.echo(f"rendered {len(r['rendered'])} preview(s) with {r['backend']}; failed: {', '.join(r['failed']) or 'none'}")
    if r["failed"]:
        sys.exit(1)


@blender_group.command("frames")
@click.option("--scope", help="shot:ID[,ID] | scene:SCxx | shots:A..B (default: whole film).")
@click.option("--frames", "frames_spec", help="Shot-local frames, e.g. 12,f24,30-34,last.")
@click.option("--every-key", is_flag=True, help="The anim file's preview_frames.")
@click.option("--preview-frame", is_flag=True, help="The shot's designated preview_frame.")
@click.option("--draft", is_flag=True, help="Use the bpy module (not the pinned Blender): never evidence.")
@click.option("--width", default=480, show_default=True)
@click.option("--jobs", default=1, show_default=True, help="Parallel Blender processes.")
@click.pass_obj
def blender_frames(c: Ctx, scope, frames_spec, every_key, preview_frame, draft, width, jobs):
    """Render chosen animation frames to 10_blender/frames/<SHOT>/ plus a contact strip (working images, not recorded)."""
    from .blenderrun import frames as run

    r = run(c.project(), c.repo, scope=scope, frames=frames_spec, every_key=every_key, preview_frame=preview_frame,
            draft=draft, width=width, jobs=jobs)
    click.echo(f"rendered frames for {len(r['rendered'])} shot(s) with {r['backend']}; failed: {', '.join(r['failed']) or 'none'}")
    for sid, p in r["strips"].items():
        click.echo(f"  {sid}: {p}")
    if r["failed"]:
        sys.exit(1)


@blender_group.command("playblast")
@click.option("--scope", help="shot:ID[,ID] | scene:SCxx | shots:A..B (default: whole film).")
@click.option("--draft", is_flag=True, help="Use the bpy module (not the pinned Blender): never evidence.")
@click.option("--width", default=640, show_default=True)
@click.option("--jobs", default=1, show_default=True, help="Parallel Blender processes.")
@click.option("--resume", is_flag=True, help="Keep frames already on disk.")
@click.pass_obj
def blender_playblast(c: Ctx, scope, draft, width, jobs, resume):
    """Render every frame of the shots in scope, stamp shot id + frame, encode <SHOT>.mp4 (and film.mp4 for the whole film)."""
    from .blenderrun import playblast as run

    r = run(c.project(), c.repo, scope=scope, draft=draft, width=width, jobs=jobs, resume=resume)
    click.echo(f"playblast of {len(r['rendered'])} shot(s) with {r['backend']}; failed: {', '.join(r['failed']) or 'none'}")
    if r["film"]:
        click.echo(f"  film: {r['film']}")
    if r["failed"]:
        sys.exit(1)


@blender_group.command("build")
@click.option("--draft", is_flag=True, help="Use the bpy module (not the pinned Blender): never G6 evidence.")
@click.option("--json", "as_json", is_flag=True, help="Print the full built/unchanged/removed report as JSON.")
@click.pass_obj
def blender_build(c: Ctx, draft, as_json):
    """Build/update the persistent 10_blender/<project>.blend; only units whose input hash changed are rebuilt."""
    from .blenderrun import build as run

    r = run(c.project(), c.repo, draft=draft)
    if as_json:
        click.echo(json.dumps(r, indent=1))
        return
    n = r["counts"]
    click.echo(f"blend built with {r['backend']}: {n['built']} built, {n['unchanged']} unchanged, {n['removed']} removed; recorded {r['derived']}")
    for u in r["removed"]:
        click.echo(f"  removed orphan {u}")


@blender_group.command("assets")
@click.option("--json", "as_json", is_flag=True)
@click.option("--strict", is_flag=True, help="Exit 1 when any needed asset has no builder.")
@click.pass_obj
def blender_assets(c: Ctx, as_json, strict):
    """ASSET_PREP contract: assets shots need (world.*, ui.*) versus what the Blender builders can produce."""
    from .blenderrun import assets_report

    r = assets_report(c.project())
    if as_json:
        click.echo(json.dumps(r, indent=1))
    else:
        for row in r["assets"]:
            how = f"{row['how']} via {row['builder']}" if row["status"] == "ok" else "NO BUILDER"
            click.echo(f"{row['status']:7} {row['asset']:32} {len(row['shots']):3} shot(s)  {how}")
        s = r["summary"]
        click.echo(f"{s['needed']} asset(s) needed: {s['buildable']} buildable, {s['unknown']} unknown")
    if strict and r["unknown"]:
        sys.exit(1)


@cli.command()
@click.option("--scope", default="film", help="film | shot:ID | shots:A..B | scene:SC01 | sequence:SQ01 | character:ID | asset:ID | ref:REF")
@click.option("--json", "as_json", is_flag=True)
@click.pass_obj
def plan(c: Ctx, scope, as_json):
    """Partial production plan: what in SCOPE is stale and needs regenerating."""
    from .ops import plan as run

    res = run(c.project(), scope)
    if as_json:
        click.echo(json.dumps(res, indent=2))
        return
    click.echo(f"scope {scope}: {len(res['roots'])} root(s), {res['in_scope']} node(s) in scope")
    if res["shots"]:
        click.echo("  shots in scope: " + ", ".join(s.split(':', 1)[1] for s in res["shots"]))
    if not res["stale"]:
        click.echo("  nothing stale - no regeneration needed")
    for layer, refs in res["by_layer"].items():
        click.echo(f"  regenerate {layer:9} ({len(refs)}): " + ", ".join(refs))


@cli.command()
@click.argument("ref")
@click.pass_obj
def deps(c: Ctx, ref):
    """Show a node's hash, upstream dependencies and downstream dependents."""
    loaded = c.project().load()
    g = build_graph(loaded)
    ref = ref if ":" in ref else f"canon:{ref}"
    if ref not in g.nodes:
        raise FMError(f"unknown node '{ref}'")
    n = g.nodes[ref]
    stale = g.stale()
    click.echo(f"{ref}  [{layer_of(ref).value}]  hash {short(n.hash)}"
               + (f"  STALE: {'; '.join(stale[ref])}" if ref in stale else ""))
    click.echo("  upstream:")
    for d in n.deps:
        cur = g.nodes[d.ref].hash if d.ref in g.nodes else None
        mark = "structural" if d.hash is None else ("ok" if d.hash == cur else f"CHANGED {short(d.hash)} -> {short(cur)}")
        click.echo(f"    {d.ref}  ({mark})")
    click.echo("  downstream:")
    for r in sorted(g.down.get(ref, ())):
        click.echo(f"    {r}")


@cli.command("hash")
@click.argument("ref")
@click.pass_obj
def hash_cmd(c: Ctx, ref):
    """Print the current content hash of a node."""
    loaded = c.project().load()
    ref = ref if ":" in ref else f"canon:{ref}"
    h = loaded.current_hash(ref)
    if h is None:
        raise FMError(f"unknown node '{ref}'")
    click.echo(f"{h}  {ref}")


@cli.command()
@click.argument("target")
@click.option("--note", help="Why upstream changes need no content revision (recorded).")
@click.pass_obj
def stamp(c: Ctx, target, note):
    """Record current upstream hashes into an artifact/shot's derived_from."""
    from .ops import stamp as run

    refreshed = run(c.project(), target, note)
    click.echo(f"stamped {target}" + (f" (refreshed: {', '.join(refreshed)})" if refreshed else ""))


@cli.command()
@click.argument("ref")
@click.option("--from", "from_refs", multiple=True, required=True, help="Upstream refs this product was made from.")
@click.option("--file", "file_", type=click.Path(exists=True, path_type=Path))
@click.option("--note")
@click.pass_obj
def record(c: Ctx, ref, from_refs, file_, note):
    """Record a derived product (resolved:/blend:/render:/qa:) and its inputs."""
    from .ops import record_derived

    rec = record_derived(c.project(), ref, list(from_refs), file=file_, note=note)
    click.echo(f"recorded {rec.ref} ({short(rec.content_hash)}) from {len(rec.derived_from)} input(s)")


@cli.command()
@click.option("--json", "as_json", is_flag=True)
@click.pass_obj
def intent(c: Ctx, as_json):
    """Creative-intent coverage: what serves each intent, and unserved decisions."""
    from .intent import intent_coverage, unserved_decisions

    loaded = c.project().load()
    rows = intent_coverage(loaded)
    unserved = unserved_decisions(loaded)
    if as_json:
        click.echo(json.dumps({"intents": [r.__dict__ for r in rows], "unserved_decisions": unserved},
                              indent=2))
        return
    if not rows:
        click.echo("no intents yet (canon/intent.yaml)")
    for r in rows:
        gap = "  <- NOT ON SCREEN" if loaded.shots and not r.shots else ""
        click.echo(f"{r.intent}: {r.statement}{gap}")
        click.echo(f"    canon ({len(r.canon)}): {', '.join(r.canon) or '-'}")
        click.echo(f"    docs  ({len(r.artifacts)}): {', '.join(r.artifacts) or '-'}")
        click.echo(f"    shots ({len(r.shots)}): {', '.join(r.shots) or '-'}")
    if unserved:
        click.echo(f"decisions serving no intent ({len(unserved)}): {', '.join(unserved)}")


@cli.group()
def check():
    """Deterministic production checks."""


@check.command("continuity")
@click.pass_obj
def check_continuity_cmd(c: Ctx):
    """Shots vs continuity canon, scene index, characters and running time. Exit 1 on FAIL."""
    from .continuity import check_continuity

    findings = check_continuity(c.project().load())
    for f in findings:
        click.secho(str(f), fg="red" if f.level == "FAIL" else "yellow")
    fails = sum(1 for f in findings if f.level == "FAIL")
    click.secho(f"continuity: {fails} FAIL, {len(findings) - fails} WARN", fg="red" if fails else "green")
    if fails:
        sys.exit(1)


@check.command("anim")
@click.option("--strict", is_flag=True, help="A missing or stub anim file is a FAIL.")
@click.option("--no-record", "no_record", is_flag=True, help="Write the report but do not record the qa:motion derived node.")
@click.pass_obj
def check_anim_cmd(c: Ctx, strict, no_record):
    """Alias of `fm qa motion`."""
    _run_qa_motion(c, strict, not no_record)


# ------------------------------------------------------------------ ledger / tools
@cli.command("log")
@click.option("--tail", default=20, show_default=True)
@click.pass_obj
def log_cmd(c: Ctx, tail):
    """Show the approval ledger (and verify its hash chain)."""
    p = c.project()
    led = Ledger(p.ledger_path)
    problems = led.verify()
    for r in led.records()[-tail:]:
        sim = " (simulated)" if r.payload.get("simulated") else ""
        click.echo(f"{r.seq:4} {r.ts}  {r.actor:24} {r.action:15} {r.target}{sim}")
    click.secho("ledger chain: OK" if not problems else "ledger chain: BROKEN\n  " + "\n  ".join(problems),
                fg="green" if not problems else "red")


@cli.command()
@click.pass_obj
def doctor(c: Ctx):
    """Check the environment, including the pinned Blender version."""
    import platform
    import shutil

    ok = True
    click.echo(f"fm {__version__} | Python {platform.python_version()} | {platform.system()} {platform.machine()}")
    click.echo(f"repository: {c.repo}")
    click.echo(f"actor: {current_actor()}")
    click.echo(f"git: {'found' if shutil.which('git') else 'MISSING'}")
    click.echo(f"ffmpeg: {'found' if shutil.which('ffmpeg') else 'missing (needed from M6)'}")
    try:
        info = require_blender(c.repo)
        click.secho(f"blender: {info.version}{' LTS' if info.lts else ''} OK (pinned {info.series}.x) - {info.executable}",
                    fg="green")
    except FMError as exc:
        ok = False
        click.secho(f"blender: REFUSED - {exc}", fg="red")
    if not ok:
        sys.exit(4)


@cli.group("post")
def post_group():
    """Post-production (M6): EDL, animatic, master assembly, delivery encodes."""


def _size(v: str) -> tuple[int, int]:
    try:
        w, h = v.lower().split("x")
        return int(w), int(h)
    except ValueError:
        raise click.BadParameter("use WIDTHxHEIGHT, e.g. 1280x720")


@post_group.command("edl")
@click.option("--out", type=click.Path(path_type=Path), default=None, help="Output dir (default 12_post).")
@click.pass_obj
def post_edl(c: Ctx, out):
    """CMX3600 EDL (24 fps NDF) + ffconcat list from the resolved frame table."""
    from . import post

    r = post.build_edl(c.project(), out)
    click.echo(f"{r['edl']}: {r['events']} events, {r['total_frames']} frames, end {r['end_timecode']}, "
               f"fade in {r['fade_in']} / out {r['fade_out']} frames")
    click.echo(r["ffconcat"])


@post_group.command("animatic")
@click.option("--out", type=click.Path(path_type=Path), default=None, help="Output dir (default 12_post).")
@click.option("--size", "size", default="1280x720", show_default=True, callback=lambda ctx, p, v: _size(v))
@click.option("--audio", type=click.Path(path_type=Path), default=None, help="Mix wav (default 12_post/audio/mix_48k_stereo.wav).")
@click.option("--no-audio", is_flag=True, help="Silent animatic even if a mix exists.")
@click.option("--no-stamp", is_flag=True, help="Do not stamp the shot id.")
@click.pass_obj
def post_animatic(c: Ctx, out, size, audio, no_audio, no_stamp):
    """animatic.mp4 from rendered frames, else preview stills held for the shot duration (H.264, 24 fps)."""
    from . import post

    p = c.project()
    r = post.build_animatic(p, out, size=size, audio=audio, stamp=not no_stamp, no_audio=no_audio)
    click.echo(f"{r['file']}: {r['duration_s']:.3f} s, {r['video']['frames']} frames @ {r['video']['fps']} fps, "
               f"{r['size'][0]}x{r['size'][1]}, audio: {'yes' if r['with_audio'] else 'silent'}, "
               f"{r['shots_from_frames']} shots from frames, {r['shots_from_stills']} from stills")
    if r["missing_sources"]:
        click.secho("no frame or still for: " + ", ".join(r["missing_sources"]), fg="yellow")


@post_group.command("assemble")
@click.option("--out", type=click.Path(path_type=Path), default=None, help="Output dir (default 13_delivery).")
@click.option("--frames", "frames_dir", type=click.Path(path_type=Path), default=None,
              help="Final frames root, <SHOT>/%04d.png (default 11_render/final).")
@click.option("--audio", type=click.Path(path_type=Path), default=None)
@click.option("--silent", is_flag=True, help="Assemble without sound.")
@click.option("--grain", is_flag=True, help="Apply the locked film grain (off by default).")
@click.option("--vignette", type=float, default=0.0, help="Corner darkening 0..canon max (off by default).")
@click.option("--fade-in", type=int, default=None, help="Frames (default: canon, else 12).")
@click.option("--fade-out", type=int, default=None, help="Frames (default: canon camera.rhythm.transitions).")
@click.pass_obj
def post_assemble(c: Ctx, out, frames_dir, audio, silent, grain, vignette, fade_in, fade_out):
    """Master mezzanine from final frames: grain, vignette, fades, audio (loudnorm -16 LUFS / -1 dBTP)."""
    from . import post

    r = post.assemble(c.project(), out, frames_dir=frames_dir, audio=audio, grain=grain, vignette=vignette,
                      fade_in=fade_in, fade_out=fade_out, silent=silent)
    click.echo(f"{r['master']} [{r['codec']}]: {r['duration_s']:.3f} s; fades {r['fade_in']}/{r['fade_out']}; "
               f"grain {'on' if grain else 'off'}, vignette {vignette or 'off'}")
    if r["loudnorm_pass1"]:
        click.echo(f"  loudnorm pass 1: {r['loudnorm_pass1']['input_i']} LUFS, {r['loudnorm_pass1']['input_tp']} dBTP")


@post_group.command("export")
@click.option("--out", type=click.Path(path_type=Path), default=None, help="Delivery dir (default 13_delivery).")
@click.option("--master", type=click.Path(path_type=Path), default=None)
@click.option("--no-proxy", is_flag=True)
@click.pass_obj
def post_export(c: Ctx, out, master, no_proxy):
    """Web MP4 (+ review proxy) from the master and MANIFEST.json (files, sha256, probe facts)."""
    from . import post

    r = post.export(c.project(), out, master=master, proxy=not no_proxy)
    for f in r["files"]:
        click.echo(f"{f['path']}  {f['bytes']} bytes  sha256 {f['sha256'][:16]}...")
    click.echo(r["manifest"])


@qa_group.command("delivery")
@click.option("--out", type=click.Path(path_type=Path), default=None, help="Delivery dir (default 13_delivery).")
@click.option("--report-dir", type=click.Path(path_type=Path), default=None, help="Where to write delivery_report.json (default qa/).")
@click.argument("files", nargs=-1, type=click.Path(path_type=Path))
@click.pass_obj
def qa_delivery_cmd(c: Ctx, out, report_dir, files):
    """ffprobe checks on the delivery files: duration, fps, resolution, audio spec, loudness, head/tail."""
    from . import post

    r = post.qa_delivery(c.project(), out, files=list(files) or None, report_dir=report_dir)
    for row in r["rows"]:
        for sev, msg in row["findings"]:
            click.echo(f"{sev:4} {row['file']}: {msg}")
    s = r["summary"]
    click.echo(f"{s['files']} delivery file(s): {s['fail']} FAIL, {s['warn']} WARN finding(s) "
               f"({s['files_failing']} row(s) failing) -> {r['report_file']}")
    if s["fail"]:
        sys.exit(1)


@cli.group("audio")
def audio_group():
    """Sound (M6): procedural library, cue-sheet scaffold and the sample-exact mixer."""


@audio_group.command("list")
@click.option("--json", "as_json", is_flag=True)
def audio_list(as_json):
    """The synth registry: recipe, description, placeholder flag and the shot lines it serves."""
    from .audio import synth

    rows = synth.list_recipes()
    if as_json:
        click.echo(json.dumps(rows, indent=1))
        return
    for r in rows:
        click.echo(f"{r['name']:34} {'PLACEHOLDER ' if r['placeholder'] else ''}{r['default_duration']:.3f}s  {r['desc']}")
    click.echo(f"{len(rows)} recipe(s); {sum(r['placeholder'] for r in rows)} placeholder(s)")


@audio_group.command("synth")
@click.option("--id", "ids", multiple=True, help="Recipe name (repeatable; default: every recipe).")
@click.option("--out", "out", type=click.Path(path_type=Path), default=None, help="Output directory (default 12_post/audio/lib/).")
@click.option("--seed", default=0, show_default=True)
@click.pass_obj
def audio_synth(c: Ctx, ids, out, seed):
    """Render library WAVs deterministically (one per recipe, default duration). Writes only into the output directory."""
    from .audiorun import synth_library

    r = synth_library(c.project(), out, list(ids) or None, seed=seed)
    click.echo(f"rendered {len(r['rendered'])} recipe(s) into {r['out']}")


@audio_group.command("scaffold")
@click.option("--out", type=click.Path(path_type=Path), default=None, help="Default 12_post/AUDIO_CUES.yaml (refuses to overwrite).")
@click.option("--force", is_flag=True, help="Overwrite an existing file.")
@click.pass_obj
def audio_scaffold(c: Ctx, out, force):
    """PROPOSED cue-sheet skeleton from sound_sync lines, anim events and the registry (the sound-designer edits it)."""
    from .audioscaffold import scaffold

    r = scaffold(c.project(), out, force=force)
    click.echo(f"scaffolded {r['out']}: {r['cues']} cue(s), {r['beds']} bed(s), {r['silence']} silence span(s), "
               f"{r['human_supply']} human-supply item(s), {r['notes']} note(s) about points it could not cover")
    click.echo("status PROPOSED; edit it, then `fm stamp 12_post/AUDIO_CUES.yaml` and `fm validate`")


@audio_group.command("mix")
@click.pass_obj
def audio_mix(c: Ctx):
    """Render AUDIO_CUES.yaml to 12_post/audio/mix_48k_stereo.wav plus one stem per layer; record the audio:mix node."""
    from .audiorun import mix_project

    r = mix_project(c.project())
    m = r["measure"]
    click.echo(f"mixed {r['placements']} placement(s) -> {r['wav']} ({r['samples']} samples; stems: {', '.join(r['stems']) or '-'})")
    click.echo(f"  peak {m['peak_dbfs']} dBFS, true peak {m['true_peak_dbfs']} dBTP, ~{m['lufs_approx']} LUFS"
               + (f"  (suggested mix.master_gain_db: {r['suggested_master_gain_db']})" if r["suggested_master_gain_db"] is not None else ""))
    for s in r["placeholders"]:
        click.secho(f"  PLACEHOLDER in the mix: {s}", fg="yellow")
    click.echo(f"recorded {r['derived']}; next: `fm qa audio`")


@qa_group.command("audio")
@click.option("--final", is_flag=True, help="Final-export mode: an UNKNOWN licence is a FAIL (default WARN).")
@click.option("--ffmpeg/--no-ffmpeg", "use_ffmpeg", default=None, help="Measure loudness with ffmpeg ebur128 (default: when available).")
@click.pass_obj
def qa_audio(c: Ctx, final, use_ffmpeg):
    """Sync, silence-map, level, length and licence checks on the rendered mix (qa/audio_report.json). Exit 1 on FAIL."""
    from .qa_audio import check

    r = check(c.project(), use_ffmpeg=use_ffmpeg, final=final)
    for row in r["rows"]:
        for sev, msg in row["findings"]:
            click.echo(f"{sev:4} {row['shot']}: {msg}")
    s = r["summary"]
    click.echo(f"audio: {s['fail']} FAIL, {s['warn']} WARN ({r.get('sync_points', 0)} sync point(s); "
               f"{r['human_supply_open']} human-supply item(s) still needed) -> qa/audio_report.json")
    if s["fail"]:
        sys.exit(1)


@cli.group()
def schema():
    """JSON Schemas for all data files (model-independent contracts)."""


@schema.command("export")
@click.option("--out", type=click.Path(path_type=Path), default=None)
@click.pass_obj
def schema_export(c: Ctx, out):
    out = out or (c.repo / "schemas" / "json")
    for name, model in EXPORTED.items():
        write_json(out / f"{name}.schema.json", model.model_json_schema())
    click.echo(f"wrote {len(EXPORTED)} schemas to {out}")


if __name__ == "__main__":
    main()
