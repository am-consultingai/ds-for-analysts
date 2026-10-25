"""Scores each trained model and today's rule on the same months, and flags results to distrust.

    python evaluate.py --spec ml_spec.yaml [--panel runs/latest/02_panel.csv] [--out runs/latest]

Reports precision@K and recall@K on the training months and on the test months, and the real
leavers in each test month's top K. Three flags: the model doesn't beat today's rule; precision
falls a lot from the training months to the test months (it memorised, or a feature leaks);
a training score too good to be true. Writes 06_eval.json and 06_eval.md.
"""
import argparse
import json
from pathlib import Path

import joblib

from baseline import evaluate_baseline
from common import hits_per_group, load_spec, precision_at_k, read_panel, recall_at_k, write_step
from modeling import make_xy, proba
from split import time_split
from train import NAMES

MAX_GAP = 0.10        # training minus test precision above this: memorised, or a leak
TOO_GOOD = 0.80       # training precision above this (or twice the rule's) is too good to be true


def scores(y, p, rows, k):
    return {"precision": round(precision_at_k(y, p, rows["snapshot"], k), 3),
            "recall": round(recall_at_k(y, p, rows["snapshot"], k), 3)}


def to_markdown(r):
    k, b = r["k"], r["baseline"]
    lines = [f"| | precision@{k}, training months | precision@{k}, test months | recall@{k}, test months |",
             "|---|---|---|---|",
             f"| Today's rule | {b['train']['precision']:.2f} | {b['test']['precision']:.2f} | {b['test']['recall']:.2f} |"]
    for m in r["models"].values():
        lines.append(f"| {m['name']} | {m['train']['precision']:.2f} | {m['test']['precision']:.2f} | {m['test']['recall']:.2f} |")
    months = list(b["by_month"])
    lines += ["", f"Real leavers in each test month's top {k}:", "",
              "| | " + " | ".join(months) + " |", "|---|" + "---|" * len(months),
              "| Today's rule | " + " | ".join(str(b["by_month"][m]) for m in months) + " |"]
    for m in r["models"].values():
        lines.append(f"| {m['name']} | " + " | ".join(str(m["by_month"][x]) for x in months) + " |")
    lines += ["", "**Warnings**" if r["flags"] else "**No warnings.**"]
    lines += [f"- {f}" for f in r["flags"]]
    return "\n".join(lines)


def run(spec, panel_path, out):
    train, test = time_split(read_panel(panel_path), spec)
    k = spec["metric"]["k"]
    cols = json.loads((Path(out) / "05_models" / "features.json").read_text())

    def xy(rows):
        X, y = make_xy(rows, spec)
        return X.reindex(columns=cols, fill_value=0.0), y

    (Xtr, ytr), (Xte, yte) = xy(train), xy(test)
    btr, bte = evaluate_baseline(train, spec), evaluate_baseline(test, spec)
    base = {"train": {"precision": round(btr[f"precision_at_{k}"], 3), "recall": round(btr[f"recall_at_{k}"], 3)},
            "test": {"precision": round(bte[f"precision_at_{k}"], 3), "recall": round(bte[f"recall_at_{k}"], 3)},
            "by_month": bte[f"hits_in_top_{k}_by_month"]}
    result = {"k": k, "baseline": base, "models": {}, "flags": []}
    for name in spec.get("models", ["logistic"]):
        model = joblib.load(Path(out) / "05_models" / f"{name}.joblib")
        ptr, pte = proba(model, Xtr), proba(model, Xte)
        m = {"name": NAMES[name], "train": scores(ytr, ptr, train, k), "test": scores(yte, pte, test, k),
             "by_month": hits_per_group(yte, pte, test["snapshot"], k)}
        result["models"][name] = m
        tr, te = m["train"]["precision"], m["test"]["precision"]
        if te <= base["test"]["precision"]:
            result["flags"].append(f"{m['name']} does not beat today's rule on the test months "
                                   f"(precision@{k} {te:.2f} against {base['test']['precision']:.2f}).")
        if tr - te > MAX_GAP:
            result["flags"].append(f"{m['name']}: precision@{k} falls from {tr:.2f} on the training months to {te:.2f} "
                                   "on the test months. It memorised, or a feature leaks the answer. Run /leakage-check.")
        if tr > max(TOO_GOOD, 2 * base["train"]["precision"]):
            result["flags"].append(f"{m['name']}: {tr:.2f} on the training months is too good to be true for churn. "
                                   "Look for a leak before trusting any number.")
    md = to_markdown(result)
    write_step(out, "06_eval", result, md)
    return md


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default="ml_spec.yaml")
    ap.add_argument("--panel", default="runs/latest/02_panel.csv")
    ap.add_argument("--out", default="runs/latest")
    a = ap.parse_args()
    print(run(load_spec(a.spec), a.panel, a.out))


if __name__ == "__main__":
    main()
