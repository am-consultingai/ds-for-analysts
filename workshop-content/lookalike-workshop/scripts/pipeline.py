"""Runs the whole ML pipeline from the spec, the same way every time.

    python pipeline.py --spec ml_spec.yaml [--out runs/latest] [--from audit] [--to score] [--compare runs/other]

Steps 1 and 2 (the question and today's rule) are read from the spec and shown first. Then:
check the data (audit), feature engineering (build_panel), split, today's rule scored on the
test months (baseline), train, evaluate, leakage, score. If `final_model` is not set yet, score
uses the model /evaluate suggests, and says so. Writes manifest.json (hashes of the spec and the
data, package versions) and 00_pipeline.json/.md with the headline numbers. --compare says whether
another run's headline numbers match.
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
    m, b, lab, el = spec["metric"], spec["baseline"], spec["label"], spec["eligibility"]
    return "\n".join([
        "## 1 · Define the question\n",
        f"- **Question:** {spec['question']}",
        f"- **Decision:** {spec['decision']}",
        f"- **Target:** `{lab['column']}` = {lab['positive']} in the trials table",
        f"- **Who can get a trial:** pays, at least {el['min_tenure_months']} months of tenure, no {el['not_licensed']} "
        "licence, never had a trial, never bought",
        f"- **Measured on:** AUC to compare models; in the past months, each method's top {m['k']} of the {m['leads']} "
        f"trials a month; for the business, sales per month from {m['leads']} leads",
        "\n## 2 · Today's rule\n",
        f"- **Rule:** `{b['rule']}`, then by `{b['score']}`",
        "- Scored after the split, on the same test months as the models."])


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]


def manifest(spec, spec_path):
    import numpy, pandas, sklearn, xgboost
    t = spec["tables"]
    tables = [t["accounts"]] + list(t["monthly"]) + [t["trials"], t["purchases"]]
    return {"when": datetime.now().isoformat(timespec="seconds"), "spec": sha(spec_path),
            "data": {x: sha(table_path(spec, x)) for x in tables}, "seed": spec.get("seed", 0),
            "python": platform.python_version(),
            "packages": {m.__name__: m.__version__ for m in (numpy, pandas, sklearn, xgboost)}}


def headline(out):
    """The numbers that must come out the same on every run."""
    rd = lambda n: json.loads((Path(out) / f"{n}.json").read_text())
    panel, ev, lk, sc = rd("02_panel"), rd("06_eval"), rd("07_leakage"), rd("08_score")
    h = {"trials": panel["rows"], "bought": panel["buyers"], "model columns": panel["model_features"],
         "rule test AUC": ev["baseline"]["auc"], "rule buyers in picks": ev["baseline"]["buyers"]}
    for m in ev["models"].values():
        h[f"{m['name']}: train AUC"] = m["train_auc"]
        h[f"{m['name']}: test AUC"] = m["test_auc"]
        h[f"{m['name']}: buyers in picks"] = m["buyers"]
    h["warnings"] = len(ev["flags"])
    h["suggested model"] = ev["suggestion"]["model"]
    h["leakage suspects"] = sum(f["suspect"] for f in lk["features"])
    h["eligible accounts"] = sc["eligible"]
    h["expected buyers in the leads"] = sc["expected_buyers"]
    return h


def run(spec_path, out, first="audit", last="score"):
    spec = load_spec(spec_path)
    panel = str(Path(out) / "02_panel.csv")

    def do_score():
        name = spec.get("final_model")
        if not name:
            name = json.loads((Path(out) / "06_eval.json").read_text())["suggestion"]["model"]
            print(f"final_model is not set in the spec: scoring with the model /evaluate suggests ({name}).\n")
        return score.run(spec, panel, out, name)

    calls = {"audit": lambda: audit.run(spec, out), "build_panel": lambda: build_panel.run(spec, out),
             "split": lambda: split.run(spec, panel, out), "baseline": lambda: baseline.run(spec, panel, out),
             "train": lambda: train.run(spec, panel, out), "evaluate": lambda: evaluate.run(spec, panel, out),
             "leakage": lambda: leakage.run(spec, panel, out), "score": do_score}
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
