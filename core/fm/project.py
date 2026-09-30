"""Locating the repository and projects, loading every managed file, and
computing content hashes.

A content hash covers only what constitutes the decision/artifact: status,
stamps and approval bookkeeping are excluded, so approving something never
changes its hash, while editing its substance always does.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import ValidationError

from .errors import FMError
from .io import canonical_json, hash_obj, load_json, load_yaml, normalize_text, read_front_matter, sha256_text
from .schemas import (
    SHOT_NON_CONTENT, ArtifactMeta, Brief, CanonEntry, CanonFile, ChangeRequest, DerivedRecord,
    AnimationTracks, SceneIndex, ShotSpec,
)
from .schemas.common import SLUG_RE

REPO_MARKER = Path("config") / "film_maker.yaml"
NON_ARTIFACT_DIRS = {"canon", "changes", "08_shots", ".fm", "references"}


# ------------------------------------------------------------------ helpers
def fmt_validation(exc: ValidationError) -> str:
    parts = []
    for err in exc.errors():
        loc = ".".join(str(x) for x in err["loc"]) or "(root)"
        parts.append(f"{loc}: {err['msg']}")
    return "; ".join(parts)


def find_repo(start: Path | None = None) -> Path:
    env = os.environ.get("FM_ROOT")
    if env:
        root = Path(env).resolve()
        if not (root / REPO_MARKER).exists():
            raise FMError(f"FM_ROOT={root} is not a FILM_MAKER repository (missing {REPO_MARKER})")
        return root
    cur = (start or Path.cwd()).resolve()
    for d in (cur, *cur.parents):
        if (d / REPO_MARKER).exists():
            return d
    raise FMError("not inside a FILM_MAKER repository (config/film_maker.yaml not found); set FM_ROOT")


def canon_hash(entry: CanonEntry) -> str:
    return hash_obj(entry.content())


def shot_hash(spec: ShotSpec) -> str:
    return hash_obj(spec.model_dump(mode="json", exclude=set(SHOT_NON_CONTENT)))


def md_artifact_hash(meta: dict, body: str) -> str:
    rest = {k: v for k, v in meta.items() if k != "fm"}
    return sha256_text(canonical_json(rest) + "\n---\n" + normalize_text(body))


def yaml_artifact_hash(data: dict) -> str:
    return hash_obj({k: v for k, v in data.items() if k != "fm"})


# ------------------------------------------------------------------ records
@dataclass
class CanonItem:
    entry: CanonEntry
    path: Path
    hash: str

    @property
    def ref(self) -> str:
        return f"canon:{self.entry.id}"


@dataclass
class ArtifactItem:
    meta: ArtifactMeta
    path: Path
    hash: str
    fmt: str  # "md" | "yaml"
    extra: dict = field(default_factory=dict)  # front-matter/top-level keys besides `fm`
    parsed: object | None = None  # typed model for kinds that have one (shot_animation -> AnimationTracks)

    @property
    def ref(self) -> str:
        return f"artifact:{self.meta.id}"


@dataclass
class ShotItem:
    spec: ShotSpec
    path: Path
    hash: str

    @property
    def ref(self) -> str:
        return f"shot:{self.spec.shot_id}"


@dataclass
class Loaded:
    """Everything in a project, plus problems found while loading."""

    canon: dict[str, CanonItem] = field(default_factory=dict)
    artifacts: dict[str, ArtifactItem] = field(default_factory=dict)
    shots: dict[str, ShotItem] = field(default_factory=dict)
    derived: dict[str, DerivedRecord] = field(default_factory=dict)
    changes: dict[str, tuple[ChangeRequest, Path]] = field(default_factory=dict)
    brief: Brief | None = None
    scene_index: SceneIndex | None = None
    errors: list[tuple[str, str]] = field(default_factory=list)  # (path, message)

    @property
    def anims(self) -> dict[str, ArtifactItem]:
        """shot id -> its `shot_animation` artifact (typed model in `.parsed`)."""
        return {it.parsed.shot_id: it for it in self.artifacts.values()
                if it.meta.kind == "shot_animation" and it.parsed is not None}

    def current_hash(self, ref: str) -> str | None:
        kind, _, ident = ref.partition(":")
        if kind == "canon":
            item = self.canon.get(ident)
        elif kind == "artifact":
            item = self.artifacts.get(ident)
        elif kind == "shot":
            item = self.shots.get(ident)
        else:
            rec = self.derived.get(ref)
            return rec.content_hash if rec else None
        return item.hash if item else None

    def exists(self, ref: str) -> bool:
        return self.current_hash(ref) is not None


# ------------------------------------------------------------------ project
class Project:
    def __init__(self, repo: Path, slug: str):
        if not SLUG_RE.match(slug):
            raise FMError(f"invalid project slug '{slug}' (lowercase letters, digits, underscore)")
        self.repo = repo
        self.slug = slug
        self.dir = repo / "projects" / slug

    # paths
    @property
    def fm_dir(self) -> Path: return self.dir / ".fm"
    @property
    def ledger_path(self) -> Path: return self.fm_dir / "ledger.jsonl"
    @property
    def state_path(self) -> Path: return self.dir / "state.yaml"
    @property
    def status_path(self) -> Path: return self.dir / "STATUS.md"
    @property
    def canon_dir(self) -> Path: return self.dir / "canon"
    @property
    def changes_dir(self) -> Path: return self.dir / "changes"
    @property
    def derived_dir(self) -> Path: return self.fm_dir / "derived"
    @property
    def shots_dir(self) -> Path: return self.dir / "08_shots"

    def exists(self) -> bool:
        return self.ledger_path.exists()

    def rel(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.dir.resolve()).as_posix()
        except ValueError:
            return str(path)

    # loading
    def load(self) -> Loaded:
        out = Loaded()
        self._load_canon(out)
        self._load_artifacts(out)
        self._load_shots(out)
        self._load_derived(out)
        self._load_changes(out)
        return out

    def _load_canon(self, out: Loaded) -> None:
        for path in sorted(self.canon_dir.glob("*.yaml")):
            try:
                data = load_yaml(path) or {}
                cf = CanonFile.model_validate(data)
            except ValidationError as exc:
                out.errors.append((self.rel(path), fmt_validation(exc)))
                continue
            except FMError as exc:
                out.errors.append((self.rel(path), str(exc)))
                continue
            if path.stem != cf.domain:
                out.errors.append((self.rel(path), f"file name must match domain '{cf.domain}'"))
            for e in cf.entries:
                if e.id in out.canon:
                    out.errors.append((self.rel(path), f"duplicate canon id '{e.id}'"))
                    continue
                out.canon[e.id] = CanonItem(e, path, canon_hash(e))

    def _artifact_files(self):
        for path in sorted(self.dir.rglob("*")):
            if not path.is_file() or path.suffix not in (".md", ".yaml"):
                continue
            rel_parts = path.relative_to(self.dir).parts
            if len(rel_parts) < 2 or rel_parts[0] in NON_ARTIFACT_DIRS:
                continue
            yield path

    def _load_artifacts(self, out: Loaded) -> None:
        for path in self._artifact_files():
            parsed = None
            try:
                if path.suffix == ".md":
                    meta, body = read_front_matter(path)
                    if "fm" not in meta:
                        continue
                    art_meta = ArtifactMeta.model_validate(meta["fm"])
                    h, fmt = md_artifact_hash(meta, body), "md"
                    extra = {k: v for k, v in meta.items() if k != "fm"}
                else:
                    data = load_yaml(path)
                    if not isinstance(data, dict) or "fm" not in data:
                        continue
                    art_meta = ArtifactMeta.model_validate(data["fm"])
                    if art_meta.kind == "brief":
                        out.brief = Brief.model_validate(data)
                    elif art_meta.kind == "scene_index":
                        out.scene_index = SceneIndex.model_validate(data)
                    elif art_meta.kind == "shot_animation":
                        parsed = AnimationTracks.model_validate(data)
                    h, fmt = yaml_artifact_hash(data), "yaml"
                    extra = {}
            except ValidationError as exc:
                out.errors.append((self.rel(path), fmt_validation(exc)))
                continue
            except FMError as exc:
                out.errors.append((self.rel(path), str(exc)))
                continue
            if art_meta.id in out.artifacts:
                out.errors.append((self.rel(path), f"duplicate artifact id '{art_meta.id}' "
                                   f"(also {self.rel(out.artifacts[art_meta.id].path)})"))
                continue
            out.artifacts[art_meta.id] = ArtifactItem(art_meta, path, h, fmt, extra, parsed)

    def _load_shots(self, out: Loaded) -> None:
        for path in sorted(self.shots_dir.glob("*.shot.yaml")):
            try:
                spec = ShotSpec.model_validate(load_yaml(path) or {})
            except ValidationError as exc:
                out.errors.append((self.rel(path), fmt_validation(exc)))
                continue
            except FMError as exc:
                out.errors.append((self.rel(path), str(exc)))
                continue
            if path.name != f"{spec.shot_id}.shot.yaml":
                out.errors.append((self.rel(path), f"file name must be {spec.shot_id}.shot.yaml"))
            if spec.shot_id in out.shots:
                out.errors.append((self.rel(path), f"duplicate shot '{spec.shot_id}'"))
                continue
            out.shots[spec.shot_id] = ShotItem(spec, path, shot_hash(spec))

    def _load_derived(self, out: Loaded) -> None:
        for path in sorted(self.derived_dir.rglob("*.json")):
            try:
                rec = DerivedRecord.model_validate(load_json(path))
            except (ValidationError, ValueError) as exc:
                out.errors.append((self.rel(path), str(exc)))
                continue
            out.derived[rec.ref] = rec

    def _load_changes(self, out: Loaded) -> None:
        for path in sorted(self.changes_dir.glob("CHANGE-*.yaml")):
            try:
                cr = ChangeRequest.model_validate(load_yaml(path) or {})
            except ValidationError as exc:
                out.errors.append((self.rel(path), fmt_validation(exc)))
                continue
            out.changes[cr.id] = (cr, path)


def list_projects(repo: Path) -> list[str]:
    pdir = repo / "projects"
    if not pdir.exists():
        return []
    return sorted(p.name for p in pdir.iterdir() if (p / ".fm" / "ledger.jsonl").exists())


def resolve_project(repo: Path, name: str | None) -> Project:
    """Explicit name > FM_PROJECT > the project containing cwd > the only project."""
    name = name or os.environ.get("FM_PROJECT")
    if not name:
        cwd = Path.cwd().resolve()
        pdir = (repo / "projects").resolve()
        if pdir in cwd.parents:
            name = cwd.relative_to(pdir).parts[0]
    if not name:
        projects = list_projects(repo)
        if len(projects) == 1:
            name = projects[0]
        elif not projects:
            raise FMError("no projects yet; create one with `fm init <slug>`")
        else:
            raise FMError(f"several projects exist ({', '.join(projects)}); pass --project")
    proj = Project(repo, name)
    if not proj.exists():
        raise FMError(f"project '{name}' not found under {repo / 'projects'}")
    return proj
