"""python -m fm.audio  list | render | mix | measure   (fm audio subcommands are wired later)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import mix, synth


def _params(items):
    out = {}
    for it in items or []:
        k, _, v = it.partition("=")
        try:
            out[k] = json.loads(v)
        except json.JSONDecodeError:
            out[k] = v
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m fm.audio", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="list recipes as JSON")
    r = sub.add_parser("render", help="render one recipe to a WAV")
    r.add_argument("recipe"); r.add_argument("--out", required=True)
    r.add_argument("--seconds", type=float); r.add_argument("--frames", type=float)
    r.add_argument("--seed", type=int, default=0); r.add_argument("--param", action="append", help="key=json-value")
    r.add_argument("--bits", type=int, default=24)
    m = sub.add_parser("mix", help="render a JSON cue spec to stems and master")
    m.add_argument("spec"); m.add_argument("--out-dir", required=True); m.add_argument("--bits", type=int, default=24)
    q = sub.add_parser("measure", help="peak / true peak / rms / approx LUFS of a WAV")
    q.add_argument("wav")
    a = ap.parse_args(argv)

    if a.cmd == "list":
        print(json.dumps(synth.list_recipes(), indent=2))
    elif a.cmd == "render":
        if a.seconds is None and a.frames is None:
            dur = synth.REGISTRY[a.recipe]["default_duration"]
        else:
            dur = a.seconds if a.seconds is not None else a.frames / synth.FPS
        x = synth.render(a.recipe, dur, a.seed, _params(a.param))
        mix.write_wav(a.out, x, synth.SR, a.bits)
        print(json.dumps({"out": a.out, **mix.measure(x)}, sort_keys=True))
    elif a.cmd == "mix":
        spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
        paths = mix.mix_from_spec(spec).write(a.out_dir, bits=a.bits)
        print(json.dumps({k: str(v) for k, v in paths.items()}, indent=2))
    elif a.cmd == "measure":
        print(mix._main_measure(a.wav))
    return 0


if __name__ == "__main__":
    sys.exit(main())
