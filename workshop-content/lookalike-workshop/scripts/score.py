"""Scores the accounts that can get a trial now, and picks this month's leads.

    python score.py --spec ml_spec.yaml [--panel runs/latest/02_panel.csv] [--out runs/latest] [--model tree]

The model is `final_model` in the spec (or --model), with the settings /train chose for it, refitted
on every trial in the data. The pool is the last month in the data, filtered by the spec's eligibility.
Each account gets a chance of buying after a trial, its ARR, and what pushes its score up (logistic
regression: the largest contributions; decision tree: its group). Writes 08_leads.csv, 08_score.json and 08_score.md.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from build_panel import build_pool
from common import load_spec, read_panel, write_step
from modeling import NAMES, make_model, make_xy, proba


def reasons(model, name, X, n=3):
    """Why an account scores high: logistic regression's largest contributions, or the tree's group."""
    if name == "logistic":
        contrib = model[:-1].transform(X) * model[-1].coef_[0]
        cols = np.array(X.columns)
        return ["; ".join(cols[i]) for i in np.argsort(-contrib, axis=1)[:, :n]]
    if name == "tree":
        t = model[-1].tree_
        path = model[-1].decision_path(model[:-1].transform(X))
        cols, out = list(X.columns), []
        for r in range(X.shape[0]):
            nodes = path.indices[path.indptr[r]:path.indptr[r + 1]]
            conds = []
            for a, b in zip(nodes[:-1], nodes[1:]):
                f, thr = cols[t.feature[a]], t.threshold[a]
                conds.append(f"{f} {'<=' if b == t.children_left[a] else '>'} {thr:.2f}")
            out.append(" and ".join(conds))
        return out
    return [""] * len(X)     # forest and XGBoost: hundreds of trees, no short reason


def money(v):
    return f"${v / 1e6:.1f}M" if v >= 1e6 else f"${v / 1e3:.0f}K"


def to_markdown(r, top):
    lines = [f"Scored **{r['eligible']} accounts** that can get a trial (as of {r['month']}) with **{r['model']}**, "
             f"refitted on all {r['training_trials']} trials.", "",
             f"The {r['leads']} leads: about **{r['expected_buyers']:.0f} expected to buy** after a trial "
             f"(the sum of their chances).", "",
             "| Rank | Account | Chance of buying | ARR | Pushed up most by |", "|---|---|---|---|---|"]
    for _, row in top.iterrows():
        lines.append(f"| {row['rank']} | {row['account']} | {row['chance_of_buying']:.2f} | {money(row['arr'])} | {row['pushed_up_by']} |")
    if r["tie"]:
        t = r["tie"]
        lines += ["", f"**Tie at the cut:** {t['accounts']} accounts share a chance of {t['chance']:.2f}, and "
                      f"{t['in_leads']} of them fit in the {r['leads']} leads. The model can't tell them apart, so "
                      "which of them get a trial is arbitrary here (by account ID). A model with finer scores would separate them."]
    lines += ["", "### Who could get a trial", "", "| Step | Accounts before | Accounts after |", "|---|---|---|"]
    for s in r["pool_steps"]:
        before = "" if s["rows_before"] is None else f"{s['rows_before']:,}"
        lines.append(f"| {s['step']} | {before} | {s['rows_after']:,} |")
    lines += ["", f"The full ranked list is in 08_leads.csv. The first {r['leads']} rows are this month's trials.",
              "", "**Next month:** compare these predictions with what happened. Judge the model over several months, "
                  "not one: a month of picks swings a lot."]
    return "\n".join(lines)


def run(spec, panel_path, out, model_name=None):
    name = model_name or spec.get("final_model")
    if not name:
        raise SystemExit("No model chosen yet: set final_model in ml_spec.yaml at /evaluate, or pass --model.")
    ent, leads = spec["entity_id"], spec["metric"]["leads"]
    settings = json.loads((Path(out) / "05_train.json").read_text())["models"][name]["settings"]
    panel = read_panel(panel_path)
    pool, steps = build_pool(spec)
    both = pd.concat([panel.assign(_pool=0), pool.assign(label=0, _pool=1)], ignore_index=True)
    X, y = make_xy(both, spec)
    is_pool = (both["_pool"] == 1).to_numpy()
    model = make_model(name, settings, spec.get("seed", 0)).fit(X[~is_pool], y[~is_pool])
    Xp = X[is_pool].reset_index(drop=True)
    p = proba(model, Xp)
    ranked = pd.DataFrame({"account": pool[ent], "chance_of_buying": p.round(3), "arr": pool[spec["value_column"]],
                           "pushed_up_by": reasons(model, name, Xp)})
    ranked = ranked.sort_values(["chance_of_buying", "account"], ascending=[False, True]).reset_index(drop=True)
    ranked.insert(0, "rank", np.arange(1, len(ranked) + 1))
    Path(out).mkdir(parents=True, exist_ok=True)
    ranked.to_csv(Path(out) / "08_leads.csv", index=False)
    top = ranked.head(leads)
    tie = None
    if len(ranked) > leads:
        cut = top["chance_of_buying"].iloc[-1]
        same = ranked["chance_of_buying"] == cut
        if same.sum() > (top["chance_of_buying"] == cut).sum():
            tie = {"chance": float(cut), "accounts": int(same.sum()), "in_leads": int((top["chance_of_buying"] == cut).sum())}
    result = {"tie": tie, "model": NAMES[name], "model_key": name, "settings": settings, "month": str(pool["snapshot"].iloc[0].date()),
              "training_trials": int((~is_pool).sum()), "eligible": len(ranked), "leads": min(leads, len(ranked)),
              "expected_buyers": round(float(top["chance_of_buying"].sum()), 1), "pool_steps": steps}
    md = to_markdown(result, top)
    write_step(out, "08_score", result, md)
    return md


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default="ml_spec.yaml")
    ap.add_argument("--panel", default="runs/latest/02_panel.csv")
    ap.add_argument("--out", default="runs/latest")
    ap.add_argument("--model", help="score with this model instead of final_model (tree, logistic, forest, xgboost)")
    a = ap.parse_args()
    print(run(load_spec(a.spec), a.panel, a.out, a.model))


if __name__ == "__main__":
    main()
