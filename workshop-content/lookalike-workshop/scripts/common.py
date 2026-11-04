"""Shared helpers for the workshop scripts: the spec, reading tables, metrics."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.metrics import roc_auc_score


def load_spec(path):
    """Reads ml_spec.yaml. Table paths in it are relative to the spec's folder."""
    path = Path(path).resolve()
    spec = yaml.safe_load(path.read_text())
    spec["_root"] = path.parent
    return spec


def table_path(spec, rel):
    return Path(spec["_root"]) / rel


def read_table(spec, rel):
    """Reads a CSV the way the scripts expect: only empty cells are missing.

    pandas' default would also read the text "NA" (North America) as missing.
    """
    return pd.read_csv(table_path(spec, rel), keep_default_na=False, na_values=[""])


def _top(y, score, groups, k):
    df = pd.DataFrame({"y": np.asarray(y), "s": np.asarray(score, dtype=float), "g": np.asarray(groups)})
    df["tie"] = np.arange(len(df))
    return df, {g: d.sort_values(["s", "tie"], ascending=[False, True]).head(k) for g, d in df.groupby("g", sort=True)}


def precision_at_k(y, score, groups, k):
    """Average over groups (trial months) of the share of buyers in each group's top k."""
    _, tops = _top(y, score, groups, k)
    return float(np.mean([t["y"].mean() for t in tops.values()]))


def recall_at_k(y, score, groups, k):
    df, tops = _top(y, score, groups, k)
    total = df["y"].sum()
    return float(sum(t["y"].sum() for t in tops.values()) / total) if total else float("nan")


def hits_per_group(y, score, groups, k):
    """Buyers in each group's top k, by group (trial month)."""
    _, tops = _top(y, score, groups, k)
    return {str(pd.Timestamp(g).date()): int(t["y"].sum()) for g, t in tops.items()}


def picks(y, score, groups, k, leads):
    """What a method's picks give: buyers among them, the number of picks, and whole sales a month from `leads` leads."""
    hits = hits_per_group(y, score, groups, k)
    p = precision_at_k(y, score, groups, k)
    return {"buyers": int(sum(hits.values())), "picks": k * len(hits), "precision": round(p, 3),
            "sales_per_month": int(round(p * leads)), "by_month": hits}


def auc(y, score):
    return float(roc_auc_score(np.asarray(y), np.asarray(score, dtype=float)))


def write_step(out, name, result, markdown):
    """Writes <name>.json for the next script and <name>.md for the analyst."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{name}.json").write_text(json.dumps(result, indent=1, default=str))
    (out / f"{name}.md").write_text(markdown + "\n")


def read_panel(path):
    return pd.read_csv(path, parse_dates=["snapshot", "trial_start"], keep_default_na=False, na_values=[""])
