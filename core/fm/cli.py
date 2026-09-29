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
