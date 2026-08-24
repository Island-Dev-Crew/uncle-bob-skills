#!/usr/bin/env python3
"""stability-check.py — component stability gate (SDP + SAP), computed not argued.

  Ce(c) = distinct components c depends on        Ca(c) = distinct components depending on c
  I(c)  = Ce / (Ca + Ce)          instability, 0 = maximally stable, 1 = maximally unstable
  A(c)  = abstract_types / total_types            abstractness
  D(c)  = |A(c) + I(c) - 1|                       distance from the main sequence

Verdicts:
  SDP  edge X -> Y breaches when I(X) < I(Y)  — X depends on something less stable than itself.
       Equal instability passes: the ceiling case is tolerated, not rejected.
  SAP  component c breaches when D(c) > --max-distance.

Input JSON (structural parse, no pattern matching — there is no regex here to fool):
  {"components": {"name": {"abstract": int, "total": int}, ...},
   "edges": [["from", "to"], ...]}

Exit: 0 green · 1 violations found · 2 usage / IO / malformed input (fail closed —
      an unjudgeable graph never passes, and a spec error is never a verdict).
"""
import argparse
import json
import os
import sys

EPS = 1e-9


def build(spec):
    """Return (metrics, edges, errors). metrics/edges are None when errors is non-empty."""
    errors = []
    if not isinstance(spec, dict):
        return None, None, ["top level must be a JSON object"]
    comps, raw_edges = spec.get("components"), spec.get("edges")
    if not isinstance(comps, dict) or not comps:
        errors.append("'components' must be a non-empty object")
    if not isinstance(raw_edges, list):
        errors.append("'edges' must be a list of [from, to] pairs")
    if errors:
        return None, None, errors

    metrics = {}
    for name, rec in sorted(comps.items()):
        if not isinstance(rec, dict):
            errors.append(f"component '{name}': expected an object with 'abstract' and 'total'")
            continue
        a, t = rec.get("abstract"), rec.get("total")
        if any(isinstance(v, bool) or not isinstance(v, int) for v in (a, t)):
            errors.append(f"component '{name}': 'abstract' and 'total' must be integers")
            continue
        if t < 1 or a < 0 or a > t:
            errors.append(f"component '{name}': need total >= 1 and 0 <= abstract <= total (got {a}/{t})")
            continue
        metrics[name] = {"A": a / t, "ce": set(), "ca": set()}

    edges = set()
    for i, e in enumerate(raw_edges, 1):
        if not (isinstance(e, list) and len(e) == 2 and all(isinstance(x, str) for x in e)):
            errors.append(f"edge {i}: expected a [from, to] pair of strings")
            continue
        src, dst = e
        undeclared = [n for n in (src, dst) if n not in comps]
        if undeclared:
            errors.append(f"edge {i} ({src} -> {dst}): undeclared component(s) {', '.join(undeclared)}")
            continue
        if src == dst:
            errors.append(f"edge {i}: self-dependency '{src}' is not a component coupling")
            continue
        edges.add((src, dst))
    if not errors and not edges:
        errors.append("no edges: nothing to judge (an empty gate cannot pass)")
    if errors:
        return None, None, errors

    for src, dst in edges:
        metrics[src]["ce"].add(dst)
        metrics[dst]["ca"].add(src)
    for m in metrics.values():
        ce, ca = len(m["ce"]), len(m["ca"])
        m["Ce"], m["Ca"] = ce, ca
        m["I"] = None if ce + ca == 0 else ce / (ce + ca)
        m["D"] = None if m["I"] is None else abs(m["A"] + m["I"] - 1)
    return metrics, sorted(edges), []


def judge(metrics, edges, max_distance):
    violations = []
    for src, dst in edges:
        i_src, i_dst = metrics[src]["I"], metrics[dst]["I"]
        if i_src < i_dst - EPS:
            violations.append(
                f"SDP-BREACH  {src} -> {dst}  I({src})={i_src:.2f} < I({dst})={i_dst:.2f}"
                "  depends on something less stable than itself"
            )
    for name in sorted(metrics):
        m = metrics[name]
        if m["D"] is None or m["D"] <= max_distance + EPS:
            continue
        side = "concrete-and-stable" if m["A"] + m["I"] < 1 else "abstract-and-unstable"
        violations.append(
            f"SAP-BREACH  {name}  D={m['D']:.2f} > {max_distance:.2f}"
            f"  A={m['A']:.2f} I={m['I']:.2f}  {side}"
        )
    return violations


def main() -> int:
    p = argparse.ArgumentParser(description="Component stability gate: SDP order and SAP distance.")
    p.add_argument("spec", help="components JSON: {'components': {...}, 'edges': [[from, to], ...]}")
    p.add_argument("--max-distance", type=float, default=0.5,
                   help="SAP breach when D > this (default 0.5; the number is advisory, tune it empirically)")
    args = p.parse_args()

    if not 0.0 <= args.max_distance <= 1.0:
        print(f"ERROR --max-distance must be in 0..1 (got {args.max_distance})", file=sys.stderr)
        return 2
    try:
        with open(args.spec, encoding="utf-8") as fh:
            spec = json.load(fh)
    except (OSError, json.JSONDecodeError) as e:
        print(f"ERROR cannot read spec '{args.spec}': {e}", file=sys.stderr)
        return 2

    metrics, edges, errors = build(spec)
    if errors:
        for e in errors:
            print(f"ERROR {e}", file=sys.stderr)
        return 2

    isolated = 0
    for name in sorted(metrics):
        m = metrics[name]
        if m["I"] is None:
            isolated += 1
            print(f"ISOLATED   {name}  Ca=0 Ce=0  I undefined - excluded from both verdicts")
            continue
        print(f"metric     {name}  I={m['I']:.2f} A={m['A']:.2f} D={m['D']:.2f}  Ca={m['Ca']} Ce={m['Ce']}")

    violations = judge(metrics, edges, args.max_distance)
    for v in violations:
        print(v)
    print(f"{len(metrics)} components, {len(edges)} edges, {isolated} isolated (unjudged), "
          f"{len(violations)} violations at max-distance {args.max_distance:.2f}")
    return 1 if violations else 0


if __name__ == "__main__":
    # The exit-code contract has to survive the interpreter's own shutdown. CPython flushes
    # the std streams after main() returns, and if that flush raises — a pipe whose reader
    # has already gone, which is the ordinary `gate.py … | head` idiom — it REPLACES the
    # status this script chose with 120, a code no table here names. An unhandled exception
    # is the other leak, and the worse one: it exits 1, and 1 is a VERDICT here, so a crash
    # would be read as a real finding about the code under test.
    try:
        _code = main()
    except SystemExit as _exc:                 # argparse raises this from inside
        _code = _exc.code if isinstance(_exc.code, int) else (0 if _exc.code is None else 1)
    except KeyboardInterrupt:
        _code = 2
    except BaseException as _exc:              # an exception is not a verdict
        try:
            print(f"error: internal failure: {type(_exc).__name__}: {_exc}", file=sys.stderr)
        except BaseException:
            pass
        _code = 2
    for _stream, _fd in ((sys.stdout, 1), (sys.stderr, 2)):
        try:
            if _stream is not None:
                _stream.flush()
        except BaseException:
            if _code in (0, 1):                # output that never landed is not a verdict
                _code = 2
            try:                               # so the shutdown flush cannot raise again
                os.dup2(os.open(os.devnull, os.O_WRONLY), _fd)
            except BaseException:
                pass
    sys.exit(_code)
