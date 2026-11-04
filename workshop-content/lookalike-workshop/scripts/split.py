"""Splits the trials by start date: the model learns on earlier trials and is tested on later ones.

    python split.py --spec ml_spec.yaml [--panel runs/latest/02_panel.csv] [--out runs/latest]

Training: trials that start before `test_from`. Test: trials from `test_from` to the last one in the
data. No gap is needed: each trial's outcome is known 30 days after it starts, by the start of the next round.
Writes 03_split.json and 03_split.md.
"""
import argparse

import pandas as pd

from common import load_spec, read_panel, write_step


def is_test(panel, spec):
    """True for test trials: those that start on or after `test_from`."""
    sp = spec["split"]
    if sp.get("method") != "time":
        raise ValueError("Only a time split is allowed when the data has a time column.")
    return (panel["trial_start"] >= pd.Timestamp(sp["test_from"])).to_numpy()


def time_split(panel, spec):
    """Returns (train, test)."""
    test = is_test(panel, spec)
    return panel[~test].reset_index(drop=True), panel[test].reset_index(drop=True)


def describe(train, test, spec):
    rule = spec["baseline"]["rule"]
    return {side: {"trials": len(d), "accounts": int(d.iloc[:, 0].nunique()), "buyers": int(d["label"].sum()),
                   "label_rate": round(float(d["label"].mean()), 4), "first": str(d["trial_start"].min().date()),
                   "last": str(d["trial_start"].max().date()), "months": int(d["trial_start"].nunique()),
                   "rule_hits": int(d.eval(rule).sum())}
            for side, d in (("train", train), ("test", test))}


def to_markdown(result):
    lines = ["| Side | First trial month | Last trial month | Months | Trials | Bought | Rate | Picked by today's rule |",
             "|---|---|---|---|---|---|---|---|"]
    for side in ("train", "test"):
        d = result[side]
        lines.append(f"| {side} | {d['first']} | {d['last']} | {d['months']} | {d['trials']:,} | {d['buyers']} | "
                     f"{d['label_rate']:.0%} | {d['rule_hits']} |")
    lines += ["", "Split by trial start date. Every training trial's outcome is known by the time the first test trial starts."]
    return "\n".join(lines)


def run(spec, panel_path, out):
    train, test = time_split(read_panel(panel_path), spec)
    result = describe(train, test, spec)
    md = to_markdown(result)
    write_step(out, "03_split", result, md)
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
