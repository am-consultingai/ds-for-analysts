"""Looks for features that already know the answer: a leak.

    python leakage.py --spec ml_spec.yaml [--panel runs/latest/02_panel.csv] [--out runs/latest]

Ranks the accounts in each training month by one feature at a time and measures precision@K.
A single column that finds most leavers on its own is suspect. Date columns from the
one-row-per-account table are listed too: they are often filled in on the day the data was
pulled, so they can see the future. Writes 07_leakage.json and 07_leakage.md.
"""
import argparse

from baseline import evaluate_baseline
from build_panel import source_of
from common import load_spec, precision_at_k, read_panel, write_step
from modeling import make_xy
from split import time_split

SUSPECT = 0.60   # one feature alone above this (or twice today's rule) is suspect


def to_markdown(r):
    k = r["k"]
    lines = [f"Today's rule on the training months: precision@{k} = {r['baseline']:.2f}.", "",
             f"Features that rank leavers best **on their own** (training months):", "",
             f"| Feature | Made from | precision@{k} alone | Suspect? |", "|---|---|---|---|"]
    for f in r["features"][:10]:
        lines.append(f"| {f['feature']} | {f['source']} | {f['precision']:.2f} | {'**yes**' if f['suspect'] else ''} |")
    if r["date_features"]:
        lines += ["", "Made from dates in the one-row-per-account table. Ask when these dates were filled in:", ""]
        lines += [f"- {d['feature']} ← {d['source']}" for d in r["date_features"]]
    lines += ["", "**Suggested changes**" if r["suggestions"] else "**No suspects.**"]
    lines += [f"- {s}" for s in r["suggestions"]]
    return "\n".join(lines)


def run(spec, panel_path, out):
    train, _ = time_split(read_panel(panel_path), spec)
    k = spec["metric"]["k"]
    base = evaluate_baseline(train, spec)[f"precision_at_{k}"]
    X, y = make_xy(train, spec)
    found = []
    for c in X.columns:
        v = X[c].fillna(X[c].median())
        if v.nunique() <= 1:
            continue
        p = max(precision_at_k(y, v, train["snapshot"], k), precision_at_k(y, -v, train["snapshot"], k))
        found.append({"feature": c, "source": source_of(c, spec), "precision": round(p, 3),
                      "suspect": p >= max(SUSPECT, 2 * base)})
    found.sort(key=lambda f: -f["precision"])
    dates = [{"feature": f"days_since_{c.removesuffix('_date')}", "source": c} for c in spec.get("date_columns", [])
             if f"days_since_{c.removesuffix('_date')}" in X.columns]
    suggestions = []
    for f in found:
        if f["suspect"]:
            col = f["source"].split(" ")[0]
            suggestions.append(f"`{f['feature']}` finds {f['precision']:.0%} leavers on its own. "
                               f"If `{col}` was filled in after the snapshot date, add it to `excluded_columns` "
                               "in ml_spec.yaml and re-run from /build-panel.")
    result = {"k": k, "baseline": round(base, 3), "features": found, "date_features": dates, "suggestions": suggestions}
    md = to_markdown(result)
    write_step(out, "07_leakage", result, md)
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
