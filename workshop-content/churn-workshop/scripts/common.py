"""Shared helpers for the workshop scripts: the spec, reading tables, metrics."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


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


def precision_at_k(y, score, groups, k):
    """Average over groups (snapshot dates) of the share of churners in each group's top k."""
    df = pd.DataFrame({"y": np.asarray(y), "s": np.asarray(score, dtype=float), "g": np.asarray(groups)})
    df["tie"] = np.arange(len(df))
    out = []
    for _, g in df.groupby("g", sort=True):
        top = g.sort_values(["s", "tie"], ascending=[False, True]).head(k)
        out.append(top["y"].mean())
    return float(np.mean(out))


def recall_at_k(y, score, groups, k):
    df = pd.DataFrame({"y": np.asarray(y), "s": np.asarray(score, dtype=float), "g": np.asarray(groups)})
    df["tie"] = np.arange(len(df))
    hit = tot = 0
    for _, g in df.groupby("g", sort=True):
        top = g.sort_values(["s", "tie"], ascending=[False, True]).head(k)
        hit += top["y"].sum()
        tot += g["y"].sum()
    return float(hit / tot) if tot else float("nan")


def hits_per_group(y, score, groups, k):
    """Real events in each group's top k, by group (snapshot date)."""
    df = pd.DataFrame({"y": np.asarray(y), "s": np.asarray(score, dtype=float), "g": np.asarray(groups)})
    df["tie"] = np.arange(len(df))
    return {str(pd.Timestamp(g).date()): int(d.sort_values(["s", "tie"], ascending=[False, True]).head(k)["y"].sum())
            for g, d in df.groupby("g", sort=True)}


def write_step(out, name, result, markdown):
    """Writes <name>.json for the next script and <name>.md for the analyst."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{name}.json").write_text(json.dumps(result, indent=1, default=str))
    (out / f"{name}.md").write_text(markdown + "\n")


def read_panel(path):
    return pd.read_csv(path, parse_dates=["snapshot"], keep_default_na=False, na_values=[""])


def top_decile_lift(y, score):
    y = np.asarray(y)
    s = np.asarray(score, dtype=float)
    n = max(1, len(s) // 10)
    top = np.argsort(-s, kind="stable")[:n]
    return float(y[top].mean() / y.mean())
