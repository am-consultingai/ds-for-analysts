"""Looks for features that already know the answer: a leak.

    python leakage.py --spec ml_spec.yaml [--panel runs/latest/02_panel.csv] [--out runs/latest]

Scores each model column on its own on the training trials (AUC; a column that ranks buyers in
reverse counts as strongly as one that ranks them in order). A single column at or above the spec's
`leakage.suspect_auc` finds buyers far better than any honest signal here, and is suspect.
Writes 07_leakage.json and 07_leakage.md.
"""
import argparse

from build_panel import source_of
from common import auc, load_spec, read_panel, write_step
from modeling import make_xy
from split import is_test


def to_markdown(r):
    lines = [f"Each model column alone, on the training trials. Suspect at AUC {r['suspect_auc']:.2f} or more.", "",
             "| Feature | Made from | AUC alone | Suspect? |", "|---|---|---|---|"]
    for f in r["features"][:10]:
        lines.append(f"| {f['feature']} | {f['source']} | {f['auc']:.2f} | {'**yes**' if f['suspect'] else ''} |")
    lines += ["", "**Suspects**" if r["suggestions"] else
              f"**No suspects.** The strongest single column, `{r['features'][0]['feature']}`, reaches AUC "
              f"{r['features'][0]['auc']:.2f}, below {r['suspect_auc']:.2f}."]
    lines += [f"- {s}" for s in r["suggestions"]]
    return "\n".join(lines)


def run(spec, panel_path, out):
    panel = read_panel(panel_path)
    X, y = make_xy(panel, spec)
    trn = ~is_test(panel, spec)
    X, y = X[trn], y[trn]
    limit = float(spec["leakage"]["suspect_auc"])
    found = []
    for c in X.columns:
        v = X[c].fillna(X[c].median())
        if v.nunique() <= 1:
            continue
        a = auc(y, v)
        a = max(a, 1 - a)
        found.append({"feature": c, "source": source_of(c, spec), "auc": round(a, 3), "suspect": a >= limit})
    found.sort(key=lambda f: -f["auc"])
    suggestions = [f"`{f['feature']}` reaches AUC {f['auc']:.2f} on its own. If `{f['source'].split(' ')[0]}` could "
                   "only be known after the trial started, remove it from `features` in ml_spec.yaml and re-run from /build-panel."
                   for f in found if f["suspect"]]
    result = {"suspect_auc": limit, "features": found, "suggestions": suggestions}
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
