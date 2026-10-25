"""Splits the panel by time, with a gap, so the test set is always later than the training set.

    python split.py --spec ml_spec.yaml [--panel runs/latest/02_panel.csv] [--out runs/latest]

Training uses snapshots before (test_from - gap_months). The gap keeps training labels,
which look `horizon` months ahead, from overlapping the test period. Writes 03_split.json and 03_split.md.
"""
import argparse

import pandas as pd

from common import load_spec, read_panel, write_step


def time_split(panel, spec, test_from=None):
    """Returns (train, test). `test_from` overrides the spec, for backtests."""
    sp = spec["split"]
    if sp.get("method") != "time":
        raise ValueError("Only a time split is allowed when the data has a time column.")
    test_from = pd.Timestamp(test_from or sp["test_from"])
    train_end = test_from - pd.DateOffset(months=int(sp["gap_months"]))
    test_end = test_from + pd.DateOffset(months=6)
    train = panel[panel["snapshot"] < train_end]
    test = panel[(panel["snapshot"] >= test_from) & (panel["snapshot"] < test_end)]
    return train.reset_index(drop=True), test.reset_index(drop=True)


def describe(train, test):
    return {side: {"rows": len(d), "accounts": int(d.iloc[:, 0].nunique()), "label_rate": round(float(d["label"].mean()), 4),
                   "first": str(d["snapshot"].min().date()), "last": str(d["snapshot"].max().date()),
                   "months": int(d["snapshot"].nunique())}
            for side, d in (("train", train), ("test", test))}


def to_markdown(result, spec):
    lines = ["| Side | First month | Last month | Months | Rows | Accounts | Label rate |", "|---|---|---|---|---|---|---|"]
    for side in ("train", "test"):
        d = result[side]
        lines.append(f"| {side} | {d['first']} | {d['last']} | {d['months']} | {d['rows']:,} | {d['accounts']:,} | {d['label_rate']:.1%} |")
    lines += ["", f"Gap: {spec['split']['gap_months']} months between the last training month and the first test month, "
                  f"because each label looks {spec['label']['horizon_months']} months ahead."]
    return "\n".join(lines)


def run(spec, panel_path, out):
    train, test = time_split(read_panel(panel_path), spec)
    result = describe(train, test)
    md = to_markdown(result, spec)
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
