"""Scores today's rule the same way the models are scored, on the same test months.

    python baseline.py --spec ml_spec.yaml [--panel runs/latest/02_panel.csv] [--out runs/latest]

The spec gives the rule (which accounts it flags) and a score to rank them by.
Writes 04_baseline.json and 04_baseline.md.
"""
import argparse

import numpy as np

from common import hits_per_group, load_spec, precision_at_k, read_panel, recall_at_k, write_step
from split import time_split


def baseline_score(panel, spec):
    """Flagged accounts first, ranked by the rule's score; unflagged ones after them."""
    b = spec["baseline"]
    flag = panel.eval(b["rule"]).to_numpy()
    score = panel.eval(b["score"]).to_numpy(dtype=float)
    return flag.astype(float) * 1000 + np.nan_to_num(score), flag


def evaluate_baseline(rows, spec):
    k = spec["metric"]["k"]
    score, flag = baseline_score(rows, spec)
    y = rows["label"].to_numpy()
    return {"rule": spec["baseline"]["rule"],
            "flagged_per_snapshot": round(float(flag.sum() / rows["snapshot"].nunique()), 1),
            "leavers_per_snapshot": round(float(y.sum() / rows["snapshot"].nunique()), 1),
            f"precision_at_{k}": precision_at_k(y, score, rows["snapshot"], k),
            f"recall_at_{k}": recall_at_k(y, score, rows["snapshot"], k),
            f"hits_in_top_{k}_by_month": hits_per_group(y, score, rows["snapshot"], k)}


def to_markdown(r, k):
    p, rc = r[f"precision_at_{k}"], r[f"recall_at_{k}"]
    return "\n".join([
        f"Today's rule: `{r['rule']}`, scored on the test months.", "",
        "| Measure | Value | In plain words |", "|---|---|---|",
        f"| precision@{k} | {p:.2f} | of the {k} accounts called each month, about {p * k:.0f} were really leaving |",
        f"| recall@{k} | {rc:.2f} | those calls reached {rc:.0%} of the ~{r['leavers_per_snapshot']:.0f} accounts that left each month |",
        f"| accounts flagged per month | {r['flagged_per_snapshot']:.0f} | the rest of the {k} are ranked by the rule's score |",
        "", f"**The numbers to beat: precision@{k} = {p:.2f}, recall@{k} = {rc:.2f}.**"])


def run(spec, panel_path, out):
    _, test = time_split(read_panel(panel_path), spec)
    k = spec["metric"]["k"]
    result = evaluate_baseline(test, spec)
    md = to_markdown(result, k)
    write_step(out, "04_baseline", result, md)
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
