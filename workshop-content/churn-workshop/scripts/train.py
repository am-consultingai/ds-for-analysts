"""Trains the models the spec lists, on the training months only.

    python train.py --spec ml_spec.yaml [--panel runs/latest/02_panel.csv] [--out runs/latest]

Writes 05_models/<model>.joblib and 05_models/features.json, then 05_train.json and 05_train.md:
the rows used, churn events per feature, and the logistic regression's largest weights.
"""
import argparse
import json
from pathlib import Path

import joblib

from common import load_spec, read_panel, write_step
from modeling import logistic, make_xy, xgboost
from split import time_split

NAMES = {"logistic": "Logistic regression", "xgboost": "XGBoost"}
MIN_EVENTS_PER_FEATURE = 10   # rule of thumb for logistic regression


def make_model(name, spec):
    return logistic() if name == "logistic" else xgboost(seed=spec.get("seed", 0))


def largest_weights(model, columns, n=12):
    """Weights on scaled features: the sign is the direction, the size is the strength."""
    lr = model[-1]
    pairs = sorted(zip(columns, lr.coef_[0]), key=lambda t: -abs(t[1]))[:n]
    return [{"feature": f, "weight": round(float(w), 3)} for f, w in pairs], round(float(lr.intercept_[0]), 3)


def to_markdown(r):
    epf = r["events_per_feature"]
    lines = [f"Trained on **{r['rows']:,} rows** ({r['first']} – {r['last']}): **{r['churn_events']:,} churn events**, "
             f"**{r['features']} features**.", "",
             f"Churn events per feature: **{epf}** (rule of thumb: at least {MIN_EVENTS_PER_FEATURE})."]
    if epf < MIN_EVENTS_PER_FEATURE:
        lines.append("Below the rule of thumb: the model may memorise. Compare the training and test scores in /evaluate.")
    for info in r["models"].values():
        if "top_weights" not in info:
            lines += ["", f"**{info['name']}** trained."]
            continue
        lines += ["", f"**{info['name']}**: the largest weights. A plus pushes toward leaving, a minus toward staying. "
                      "Weights show association, not cause.", "",
                  "| Feature | Weight | Pushes toward |", "|---|---|---|"]
        lines += [f"| {w['feature']} | {w['weight']:+.2f} | {'leaving' if w['weight'] > 0 else 'staying'} |"
                  for w in info["top_weights"]]
    return "\n".join(lines)


def run(spec, panel_path, out):
    train, _ = time_split(read_panel(panel_path), spec)
    X, y = make_xy(train, spec)
    events = int(train.loc[train["label"] == 1, spec["entity_id"]].nunique())
    folder = Path(out) / "05_models"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "features.json").write_text(json.dumps(list(X.columns)))
    result = {"rows": len(train), "first": str(train["snapshot"].min().date()), "last": str(train["snapshot"].max().date()),
              "positive_rows": int(y.sum()), "churn_events": events, "features": X.shape[1],
              "events_per_feature": round(events / X.shape[1], 1), "models": {}}
    for name in spec.get("models", ["logistic"]):
        model = make_model(name, spec).fit(X, y)
        joblib.dump(model, folder / f"{name}.joblib")
        info = {"name": NAMES[name]}
        if name == "logistic":
            info["top_weights"], info["intercept"] = largest_weights(model, X.columns)
        result["models"][name] = info
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
