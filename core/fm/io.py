"""Deterministic file I/O: YAML, JSON, front-matter documents, content hashes."""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import yaml

from .errors import FMError


# ------------------------------------------------------------------- time
def now_iso() -> str:
    """UTC timestamp. FM_FIXED_TIME pins it (tests, reproducible demos)."""
    fixed = os.environ.get("FM_FIXED_TIME")
    if fixed:
        return fixed
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


# ------------------------------------------------------------------- text
def normalize_text(text: str) -> str:
    """LF line endings, no trailing whitespace per line, exactly one final newline.
    Makes hashes identical on Windows and Linux."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [ln.rstrip() for ln in text.split("\n")]
    return "\n".join(lines).strip("\n") + "\n"


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


# ------------------------------------------------------------------- yaml
_SafeLoader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)


class _Dumper(getattr(yaml, "CSafeDumper", yaml.SafeDumper)):
    pass


def _str_presenter(dumper, data):
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


_Dumper.add_representer(str, _str_presenter)
_Dumper.add_representer(tuple, lambda d, v: d.represent_list(list(v)))


def dump_yaml(data: Any) -> str:
    return yaml.dump(data, Dumper=_Dumper, sort_keys=False, allow_unicode=True, width=100)


def load_yaml(path: Path) -> Any:
    try:
        with open(path, encoding="utf-8") as fh:
            return yaml.load(fh, Loader=_SafeLoader)  # noqa: S506 - safe loader
    except yaml.YAMLError as exc:
        raise FMError(f"{path}: invalid YAML: {exc}") from exc


def write_yaml(path: Path, data: Any) -> None:
    atomic_write(path, dump_yaml(data))


# ------------------------------------------------------------------- json
def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def write_json(path: Path, data: Any) -> None:
    atomic_write(path, json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True, default=str) + "\n")


def load_json(path: Path) -> Any:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# ------------------------------------------------------------------- hashes
def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_obj(obj: Any) -> str:
    return sha256_text(canonical_json(obj))


def hash_file_bytes(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def short(h: str | None) -> str:
    if not h:
        return "-"
    return h.split(":", 1)[-1][:12]


# ------------------------------------------------------------ front matter
def read_front_matter(path: Path) -> tuple[dict, str]:
    """Split a Markdown document into (front-matter dict, body)."""
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        if text.rstrip().endswith("\n---"):
            end = text.rstrip().rfind("\n---")
            meta_txt, body = text[4:end], ""
        else:
            raise FMError(f"{path}: unterminated front-matter")
    else:
        meta_txt, body = text[4:end], text[end + 5:]
    try:
        meta = yaml.load(meta_txt, Loader=_SafeLoader) or {}  # noqa: S506
    except yaml.YAMLError as exc:
        raise FMError(f"{path}: invalid front-matter YAML: {exc}") from exc
    if not isinstance(meta, dict):
        raise FMError(f"{path}: front-matter must be a mapping")
    return meta, body


def write_front_matter(path: Path, meta: dict, body: str) -> None:
    atomic_write(path, "---\n" + dump_yaml(meta) + "---\n" + body)
