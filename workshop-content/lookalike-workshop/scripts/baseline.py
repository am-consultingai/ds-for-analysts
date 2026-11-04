"""Scores today's rule the same way the models are scored, on the same test months.

    python baseline.py --spec ml_spec.yaml [--panel runs/latest/02_panel.csv] [--out runs/latest]

The spec gives the rule (which accounts it picks) and a score that orders the rest. Each test
month, the rule's top K of that month's trials are its picks. Writes 04_baseline.json and 04_baseline.md.
"""
import argparse

import numpy as np

from common import auc, load_spec, picks, read_panel, write_step
from split import time_split


def baseline_score(panel, spec):
    """Accounts the rule picks first, ordered by the rule's score; the rest after them, by the same score."""
    b = spec["baseline"]
    flag = panel.eval(b["rule"]).to_numpy()
    score = np.nan_to_num(panel.eval(b["score"]).to_numpy(dtype=float))
    return flag * (np.abs(score).max() + 1) * 10 + score, flag


def evaluate_baseline(rows, spec):
    m = spec["metric"]
    score, flag = baseline_score(rows, spec)
    y = rows["label"].to_numpy()
    p = picks(y, score, rows["trial_start"], m["k"], m["leads"])
    return {"rule": spec["baseline"]["rule"], "auc": round(auc(y, score), 3), **p,
            "rule_hits_per_month": [int(v) for v in rows.assign(f=flag).groupby("trial_start")["f"].sum()],
            "trial_conversion": round(float(y.mean()), 3)}


def to_markdown(r, spec):
    m = spec["metric"]
    return "\n".join([
        f"Today's rule: `{r['rule']}`, then by `{spec['baseline']['score']}`. Scored on the test months.", "",
        "| Measure | Value | In plain words |", "|---|---|---|",
        f"| AUC | {r['auc']:.2f} | the chance a buyer is ranked above a non-buyer; 0.50 is a coin flip |",
        f"| buyers in picks | {r['buyers']} of {r['picks']} | each month the rule's top {m['k']} of the {m['leads']} trials; "
        f"{r['precision']:.0%} bought |",
        f"| sales per month | {r['sales_per_month']} | from {m['leads']} leads a month, at that rate |",
        f"| accounts the rule picks, per month | {min(r['rule_hits_per_month'])}–{max(r['rule_hits_per_month'])} | "
        f"the rest of the {m['k']} are ordered by {spec['baseline']['score']} |",
        "", f"For context: the average test trial converted at {r['trial_conversion']:.0%}.", "",
        f"**The numbers to beat: AUC {r['auc']:.2f}, {r['buyers']} buyers in {r['picks']} picks, "
        f"{r['sales_per_month']} sales a month.**"])


def run(spec, panel_path, out):
    _, test = time_split(read_panel(panel_path), spec)
    result = evaluate_baseline(test, spec)
    md = to_markdown(result, spec)
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
