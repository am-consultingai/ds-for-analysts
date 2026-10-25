"""Runs the whole ML pipeline from the spec, the same way every time.

    python pipeline.py --spec ml_spec.yaml [--out runs/latest] [--from audit] [--to score] [--compare runs/other]

Steps 1 and 2 (the question and today's rule) are read from the spec and shown first. Then:
check the data (audit), feature engineering (build_panel), split, today's rule scored on the
test months (baseline), train, evaluate, leakage, score. Writes
manifest.json (hashes of the spec and the data, package versions) and 00_pipeline.json/.md
with the headline numbers. --compare says whether another run's headline numbers match.
"""
import argparse
import hashlib
import json
import platform
import sys
from datetime import datetime
from pathlib import Path

import audit
import baseline
import build_panel
import evaluate
import leakage
import score
import split
import train
from common import load_spec, table_path

STEPS = ["audit", "build_panel", "split", "baseline", "train", "evaluate", "leakage", "score"]
LABELS = {"audit": "3 · Check the data", "build_panel": "4 · Feature engineering", "split": "5 · Split",
          "baseline": "2 · Today's rule, scored", "train": "6 · Train", "evaluate": "7 · Evaluate",
          "leakage": "7 · Leakage check", "score": "8 · Score"}


def framing(spec):
    """Steps 1 and 2 have no script: they are decisions written in the spec. Show them first."""
    k, b = spec["metric"]["k"], spec["baseline"]
    return "\n".join([
        "## 1 · Define the question\n",
        f"- **Question:** {spec['question']}",
        f"- **Decision:** {spec['decision'].replace(' K ', f' {k} ')}",
        f"- **Target:** `{spec['value_column']}` goes from above 0 to 0 within {spec['label']['horizon_months']} months",
        f"- **Who is scored:** accounts with `{spec['value_column']}` above 0 and at least "
        f"{spec['eligibility']['min_tenure_months']} months of tenure",
        f"- **Measured on:** the top {k} each month, with precision@{k} and recall@{k}",
        "\n## 2 · Today's rule\n",
        f"- **Rule:** `{b['rule']}`, ranked by `{b['score']}`",
        "- Scored after the split, on the same test months as the model."])


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]


def manifest(spec, spec_path):
    import numpy, pandas, sklearn, xgboost
    tables = [spec["tables"]["accounts"]] + list(spec["tables"]["monthly"])
    return {"when": datetime.now().isoformat(timespec="seconds"), "spec": sha(spec_path),
            "data": {t: sha(table_path(spec, t)) for t in tables}, "seed": spec.get("seed", 0),
            "python": platform.python_version(),
            "packages": {m.__name__: m.__version__ for m in (numpy, pandas, sklearn, xgboost)}}


def headline(out):
    """The numbers that must come out the same on every run."""
    out = Path(out)
    rd = lambda n: json.loads((out / f"{n}.json").read_text())
    panel, ev, sc = rd("02_panel"), rd("06_eval"), rd("08_score")
    h = {"panel rows": panel["rows"], "features": panel["model_features"],
         "rule precision@k (test)": ev["baseline"]["test"]["precision"],
         "rule recall@k (test)": ev["baseline"]["test"]["recall"]}
    for m in ev["models"].values():
        h[f"{m['name']} precision@k (train)"] = m["train"]["precision"]
        h[f"{m['name']} precision@k (test)"] = m["test"]["precision"]
        h[f"{m['name']} recall@k (test)"] = m["test"]["recall"]
    h["warnings"] = len(ev["flags"])
    h["ARR at risk, top k"] = round(sc["arr_at_risk_top_k"])
    return h


def run(spec_path, out, first="audit", last="score"):
    spec = load_spec(spec_path)
    panel = str(Path(out) / "02_panel.csv")
    calls = {"audit": lambda: audit.run(spec, out), "build_panel": lambda: build_panel.run(spec, out),
             "split": lambda: split.run(spec, panel, out), "baseline": lambda: baseline.run(spec, panel, out),
             "train": lambda: train.run(spec, panel, out), "evaluate": lambda: evaluate.run(spec, panel, out),
             "leakage": lambda: leakage.run(spec, panel, out), "score": lambda: score.run(spec, panel, out)}
    if first == "audit":
        print(framing(spec))
    for step in STEPS[STEPS.index(first):STEPS.index(last) + 1]:
        print(f"\n## {LABELS[step]}\n\nScript: scripts/{step}.py\n")
        print(calls[step]())
    Path(out, "manifest.json").write_text(json.dumps(manifest(spec, spec_path), indent=1))
    if last == "score" and first == "audit":
        h = headline(out)
        Path(out, "00_pipeline.json").write_text(json.dumps(h, indent=1))
        Path(out, "00_pipeline.md").write_text("| Number | Value |\n|---|---|\n" +
                                               "\n".join(f"| {k} | {v} |" for k, v in h.items()) + "\n")
        return h


def compare(a, b):
    ha, hb = (json.loads(Path(x, "00_pipeline.json").read_text()) for x in (a, b))
    rows = [(k, ha.get(k), hb.get(k)) for k in dict.fromkeys(list(ha) + list(hb))]
    print(f"\n| Number | {a} | {b} | Same? |\n|---|---|---|---|")
    for k, x, y in rows:
        print(f"| {k} | {x} | {y} | {'yes' if x == y else '**NO**'} |")
    same = all(x == y for _, x, y in rows)
    print("\nAll numbers match." if same else "\nSome numbers differ: check what changed in the spec or the data.")
    return same


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default="ml_spec.yaml")
    ap.add_argument("--out", default="runs/latest")
    ap.add_argument("--from", dest="first", default="audit", choices=STEPS)
    ap.add_argument("--to", dest="last", default="score", choices=STEPS)
    ap.add_argument("--compare", help="another run folder to compare the headline numbers with")
    a = ap.parse_args()
    run(a.spec, a.out, a.first, a.last)
    if a.compare:
        sys.exit(0 if compare(a.compare, a.out) else 1)


if __name__ == "__main__":
    main()
