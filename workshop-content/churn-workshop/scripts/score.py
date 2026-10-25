"""Scores this month's accounts and ranks them for the CSMs.

    python score.py --spec ml_spec.yaml [--panel runs/latest/02_panel.csv] [--out runs/latest]

The first model in the spec is refitted on every labelled month, with the same settings as
/train, then applied to the last month in the data, which has no label yet. Each account gets
a chance of leaving, its ARR, the ARR at risk (chance × ARR) and the three features that push
its score up most. Writes 08_ranked.csv, 08_score.json and 08_score.md.
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from build_panel import build_panel
from common import load_spec, read_panel, write_step
from modeling import make_xy, proba
from train import NAMES, make_model


def reasons(model, X, n=3):
    """For logistic regression: the features adding most to each account's score."""
    if not hasattr(model, "steps"):
        return [""] * len(X)
    contrib = model[:-1].transform(X) * model[-1].coef_[0]
    top = np.argsort(-contrib, axis=1)[:, :n]
    cols = np.array(X.columns)
    return ["; ".join(cols[i]) for i in top]


def money(v):
    return f"${v / 1e6:.1f}M" if v >= 1e6 else f"${v / 1e3:.0f}K"


def to_markdown(r, top):
    k = r["k"]
    lines = [f"Scored **{r['accounts']:,} active accounts** for **{r['month']}** with {r['model']}, "
             f"refitted on {r['training_rows']:,} labelled rows.", "",
             f"The top {k}: about **{r['expected_leavers_top_k']:.0f} expected to leave** in the next "
             f"{r['horizon_months']} months, **{money(r['arr_at_risk_top_k'])} ARR at risk** "
             f"out of {money(r['arr_top_k'])} ARR on the list.", "",
             "| Rank | Account | Chance of leaving | ARR | ARR at risk | Pushed up most by |", "|---|---|---|---|---|---|"]
    for _, row in top.head(10).iterrows():
        lines.append(f"| {row['rank']} | {row['account']} | {row['chance_of_leaving']:.2f} | {money(row['arr'])} | "
                     f"{money(row['arr_at_risk'])} | {row['pushed_up_by']} |")
    lines += ["", f"The full list is in 08_ranked.csv. The first {k} rows are this month's calls."]
    return "\n".join(lines)


def run(spec, panel_path, out):
    ent, vcol, k = spec["entity_id"], spec["value_column"], spec["metric"]["k"]
    panel = read_panel(panel_path)
    X, y = make_xy(panel, spec)
    name = spec.get("models", ["logistic"])[0]
    model = make_model(name, spec).fit(X, y)
    latest, _ = build_panel(spec, latest_only=True)
    Xn, _ = make_xy(latest, spec)
    Xn = Xn.reindex(columns=X.columns, fill_value=0.0)
    p = proba(model, Xn)
    ranked = pd.DataFrame({"account": latest[ent], "chance_of_leaving": p.round(3), "arr": latest[vcol],
                           "arr_at_risk": (p * latest[vcol]).round(0), "pushed_up_by": reasons(model, Xn)})
    ranked = ranked.sort_values(["chance_of_leaving", "account"], ascending=[False, True]).reset_index(drop=True)
    ranked.insert(0, "rank", np.arange(1, len(ranked) + 1))
    Path(out).mkdir(parents=True, exist_ok=True)
    ranked.to_csv(Path(out) / "08_ranked.csv", index=False)
    top = ranked.head(k)
    result = {"k": k, "month": str(latest["snapshot"].iloc[0].date()), "model": NAMES[name],
              "training_rows": len(panel), "accounts": len(ranked), "horizon_months": spec["label"]["horizon_months"],
              "expected_leavers_top_k": round(float(top["chance_of_leaving"].sum()), 1),
              "arr_top_k": float(top["arr"].sum()), "arr_at_risk_top_k": float(top["arr_at_risk"].sum()),
              "arr_at_risk_all": float(ranked["arr_at_risk"].sum())}
    md = to_markdown(result, top)
    write_step(out, "08_score", result, md)
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
