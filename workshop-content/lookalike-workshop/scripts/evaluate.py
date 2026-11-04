"""Scores each trained model and today's rule on the same test months, and suggests a model.

    python evaluate.py --spec ml_spec.yaml [--panel runs/latest/02_panel.csv] [--out runs/latest]

For each model: training AUC (memory) and test AUC (skill), the gap, and its picks on the test months
(each month its top K of that month's trials: buyers, and sales per month from `leads` leads). Three
warnings: a model that doesn't beat today's rule; a big gap (it memorised); a training score too good
to be true. The suggestion follows the spec's `selection`: among models whose check score is close to
the best one, the first in `simplest_first`. The analyst decides. Writes 06_eval.json and 06_eval.md.
"""
import argparse
import json
from pathlib import Path

import joblib

from baseline import evaluate_baseline
from common import auc, load_spec, picks, precision_at_k, read_panel, write_step
from modeling import NAMES, make_xy, proba
from split import is_test, time_split

MAX_GAP = 0.10     # training AUC minus test AUC above this: memorised
TOO_GOOD = 0.99    # training AUC at or above this is too good to be true


def suggest(train_info, spec):
    sel = spec["selection"]
    checks = {n: m["check_auc"] for n, m in train_info["models"].items()}
    top = max(checks.values())
    close = [n for n in sel["simplest_first"] if n in checks and checks[n] >= top - sel["close_to_best"]]
    return {"model": close[0], "best_check": top, "close": close, "checks": checks}


def to_markdown(r, spec):
    m = spec["metric"]
    b = r["baseline"]
    lines = [f"Test months: {r['test_months']} ({r['test_first']} – {r['test_last']}). Each month, every method keeps its "
             f"top {m['k']} of the {m['leads']} trials.", "",
             "| | Training AUC (memory) | Test AUC (skill) | Gap | Buyers in picks | Sales per month |",
             "|---|---|---|---|---|---|",
             f"| Today's rule | | {b['auc']:.2f} | | {b['buyers']} of {b['picks']} | {b['sales_per_month']} |"]
    for x in r["models"].values():
        lines.append(f"| {x['name']} ({x['settings_label']}) | {x['train_auc']:.2f} | {x['test_auc']:.2f} | "
                     f"{x['gap']:+.2f} | {x['buyers']} of {x['picks']} | {x['sales_per_month']} |")
    months = list(b["by_month"])
    lines += ["", f"Buyers in each test month's top {m['k']}:", "",
              "| | " + " | ".join(mo[:7] for mo in months) + " | Total |", "|---|" + "---|" * (len(months) + 1),
              "| Today's rule | " + " | ".join(str(b["by_month"][mo]) for mo in months) + f" | {b['buyers']} |"]
    for x in r["models"].values():
        lines.append(f"| {x['name']} | " + " | ".join(str(x["by_month"][mo]) for mo in months) + f" | {x['buyers']} |")
    lines += ["", "**Warnings**" if r["flags"] else "**No warnings.**"]
    lines += [f"- {f}" for f in r["flags"]]
    s = r["suggestion"]
    lines += ["", "**Suggested model** (the spec's rule: the simplest model whose check score is within "
                  f"{spec['selection']['close_to_best']} of the best): **{NAMES[s['model']]}**.",
              "Check scores: " + ", ".join(f"{NAMES[n]} {v:.3f}" for n, v in s["checks"].items())
              + f". Close to the best ({s['best_check']:.3f}): " + ", ".join(NAMES[n] for n in s["close"]) + ".",
              "The analyst decides. The choice goes to `final_model` in ml_spec.yaml."]
    return "\n".join(lines)


def run(spec, panel_path, out):
    panel = read_panel(panel_path)
    X, y = make_xy(panel, spec)
    folder = Path(out) / "05_models"
    cols = json.loads((folder / "features.json").read_text())
    X = X.reindex(columns=cols, fill_value=0.0)
    train_info = json.loads((Path(out) / "05_train.json").read_text())
    trn = ~is_test(panel, spec)
    _, test = time_split(panel, spec)
    k, leads = spec["metric"]["k"], spec["metric"]["leads"]
    base = evaluate_baseline(test, spec)
    result = {"test_months": int(test["trial_start"].nunique()), "test_first": str(test["trial_start"].min().date()),
              "test_last": str(test["trial_start"].max().date()), "baseline": base, "models": {}, "flags": []}
    pbt = train_info["picked_by_training"]
    entries = [(n, f"{n}.joblib", NAMES[n], train_info["models"][n]["settings_label"]) for n in spec["models"]]
    entries.append(("picked_by_training", "picked_by_training.joblib", f"{NAMES[pbt['model']]}, picked by training score",
                    pbt["settings_label"]))
    for key, file, name, settings_label in entries:
        model = joblib.load(folder / file)
        ptr, pte = proba(model, X[trn]), proba(model, X[~trn])
        x = {"name": name, "settings_label": settings_label, "train_auc": round(auc(y[trn], ptr), 3),
             "test_auc": round(auc(y[~trn], pte), 3),
             "train_precision": round(precision_at_k(y[trn], ptr, panel.loc[trn, "trial_start"], k), 3),
             **picks(y[~trn], pte, test["trial_start"], k, leads)}
        x["gap"] = round(x["train_auc"] - x["test_auc"], 3)
        result["models"][key] = x
        if x["test_auc"] <= base["auc"]:
            result["flags"].append(f"{name} does not beat today's rule on the test months (AUC {x['test_auc']:.2f} "
                                   f"against {base['auc']:.2f}).")
        if x["gap"] > MAX_GAP:
            result["flags"].append(f"{name}: AUC falls from {x['train_auc']:.2f} on the training trials to "
                                   f"{x['test_auc']:.2f} on the test months. It memorised the training trials.")
        if x["train_auc"] >= TOO_GOOD:
            result["flags"].append(f"{name}: training AUC {x['train_auc']:.2f} is too good to be true. "
                                   "A model this perfect on the past has memorised it, or a feature leaks the answer.")
    result["suggestion"] = suggest(train_info, spec)
    md = to_markdown(result, spec)
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
