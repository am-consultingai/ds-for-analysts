"""Trains the models the spec lists: each tries its settings and keeps the one with the best check score.

    python train.py --spec ml_spec.yaml [--panel runs/latest/02_panel.csv] [--out runs/latest]

The check is by time, like the split: for each of the last `check.months` training months, a setting
is fitted on the months before it and checked on that month (AUC). The best setting of each model is
then fitted on all training trials. The candidate with the best TRAINING score is kept too, as the
example of what not to do. Writes 05_models/, 05_train.json and 05_train.md.
"""
import argparse
import itertools
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.model_selection import cross_val_score

from common import auc, load_spec, read_panel, write_step
from modeling import NAMES, make_model, make_xy, proba
from split import is_test

MIN_BUYERS_PER_FEATURE = 10   # rule of thumb


def settings_grid(grid):
    keys = list(grid)
    return [dict(zip(keys, values)) for values in itertools.product(*(grid[k] for k in keys))]


def time_folds(start, months):
    """Fit on earlier months, check on each of the last `months` months."""
    ms = sorted(start.unique())[-months:]
    return [(np.flatnonzero(start < m), np.flatnonzero(start == m)) for m in ms]


def label(settings):
    return ", ".join(f"{k}={v}" for k, v in settings.items())


def largest_weights(model, columns, n=10):
    lr = model[-1]
    pairs = sorted(zip(columns, lr.coef_[0]), key=lambda t: -abs(t[1]))[:n]
    return [{"feature": f, "weight": round(float(w), 3)} for f, w in pairs]


def tree_rules(model, columns, depth=3):
    """The tree as groups of trials: the conditions that lead to each group, its size and how often it bought.
    Shown to `depth` levels; a deeper tree's lower splits are summed into their group at that level."""
    t, cols, groups = model[-1].tree_, list(columns), []

    def walk(node, conds, level):
        if t.children_left[node] == -1 or level == depth:
            n = int(t.n_node_samples[node])
            groups.append({"rule": " and ".join(conds) or "all trials", "trials": n,
                           "bought": round(float(t.value[node][0][1]), 3), "deeper": t.children_left[node] != -1})
            return
        f, thr = cols[t.feature[node]], t.threshold[node]
        walk(t.children_left[node], conds + [f"{f} <= {thr:.2f}"], level + 1)
        walk(t.children_right[node], conds + [f"{f} > {thr:.2f}"], level + 1)

    walk(0, [], 0)
    return groups


def to_markdown(r):
    epf = r["buyers_per_feature"]
    lines = [f"Trained on **{r['rows']} trials** ({r['first']} – {r['last']}): **{r['buyers']} bought**, "
             f"**{r['columns']} model columns**.", "",
             f"Buyers per model column: **{epf}** (rule of thumb: at least {MIN_BUYERS_PER_FEATURE})."]
    if epf < MIN_BUYERS_PER_FEATURE:
        lines.append("Below the rule of thumb: models may memorise. Compare training and test in /evaluate.")
    lines += ["", f"Each setting was checked on later training months ({r['check_months']} checks, each one month, "
                  "fitted on the months before it).", "",
              "| Model | Settings tried | Best settings | Check score (AUC) |", "|---|---|---|---|"]
    for m in r["models"].values():
        lines.append(f"| {m['name']} | {m['tried']} | {m['settings_label']} | {m['check_auc']:.3f} |")
    p = r["picked_by_training"]
    lines += ["", f"Kept as a warning example: the setting with the best **training** score, "
                  f"{NAMES[p['model']]} ({p['settings_label']}): training AUC {p['train_auc']:.2f}, "
                  f"check score {p['check_auc']:.3f}."]
    if "logistic" in r["models"]:
        lines += ["", "**Logistic regression**: the largest weights. A plus pushes toward buying, a minus away from it. "
                      "Weights show association, not cause.", "", "| Feature | Weight | Pushes toward |", "|---|---|---|"]
        lines += [f"| {w['feature']} | {w['weight']:+.2f} | {'buying' if w['weight'] > 0 else 'not buying'} |"
                  for w in r["models"]["logistic"]["top_weights"]]
    if "tree" in r["models"]:
        lines += ["", f"**Decision tree** ({r['models']['tree']['settings_label']}): the groups of training trials it makes.", "",
                  "| # | Group (the conditions) | Trials | Bought |", "|---|---|---|---|"]
        lines += [f"| {i} | {g['rule']}{' (splits further)' if g['deeper'] else ''} | {g['trials']} | {g['bought']:.0%} |"
                  for i, g in enumerate(r["models"]["tree"]["rules"], 1)]
    return "\n".join(lines)


def run(spec, panel_path, out):
    panel = read_panel(panel_path)
    X, y = make_xy(panel, spec)
    trn = ~is_test(panel, spec)
    Xt, yt, start = X[trn], y[trn], panel.loc[trn, "trial_start"].reset_index(drop=True)
    folds = time_folds(start, int(spec["check"]["months"]))
    folder = Path(out) / "05_models"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "features.json").write_text(json.dumps(list(X.columns)))
    seed = spec.get("seed", 0)
    result = {"rows": int(trn.sum()), "first": str(start.min().date()), "last": str(start.max().date()),
              "buyers": int(yt.sum()), "columns": X.shape[1], "buyers_per_feature": round(yt.sum() / X.shape[1], 1),
              "check_months": len(folds), "models": {}}
    best_train = None
    for name, grid in spec["models"].items():
        tried = []
        for st in settings_grid(grid):
            m = make_model(name, st, seed)
            check = float(cross_val_score(m, Xt, yt, cv=folds, scoring="roc_auc").mean())
            m.fit(Xt, yt)
            train_auc = auc(yt, proba(m, Xt))
            tried.append({"settings": st, "check_auc": check, "train_auc": train_auc, "model": m})
            if best_train is None or train_auc > best_train["train_auc"]:
                best_train = {"name": name, **tried[-1]}
        best = max(tried, key=lambda t: t["check_auc"])          # first of equals, in grid order
        joblib.dump(best["model"], folder / f"{name}.joblib")
        info = {"name": NAMES[name], "tried": len(tried), "settings": best["settings"], "settings_label": label(best["settings"]),
                "check_auc": round(best["check_auc"], 3), "train_auc": round(best["train_auc"], 3),
                "candidates": [{"settings": label(t["settings"]), "check_auc": round(t["check_auc"], 3),
                                "train_auc": round(t["train_auc"], 3)} for t in tried]}
        if name == "logistic":
            info["top_weights"] = largest_weights(best["model"], X.columns)
        if name == "tree":
            info["rules"] = tree_rules(best["model"], X.columns)
        result["models"][name] = info
    joblib.dump(best_train["model"], folder / "picked_by_training.joblib")
    result["picked_by_training"] = {"model": best_train["name"], "settings": best_train["settings"],
                                    "settings_label": label(best_train["settings"]),
                                    "train_auc": round(best_train["train_auc"], 3), "check_auc": round(best_train["check_auc"], 3)}
    md = to_markdown(result)
    write_step(out, "05_train", result, md)
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
