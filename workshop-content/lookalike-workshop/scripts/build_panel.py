"""Builds the trial panel: one row per trial, with features from before it and its outcome.

    python build_panel.py --spec ml_spec.yaml [--out runs/latest]

Each trial starts on the 1st of a month. Its snapshot is the month before: a monthly row is
known only at the end of its month, so that is the last month we fully know when the trial
is chosen. The features are made from the monthly tables up to the snapshot, with the same
code as the churn project. The target is the trials table's outcome column. Only the
features listed in the spec are kept. Everything specific to the project comes from the spec.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from common import load_spec, read_table

ROLL = 3  # months in "recent" windows


def _months_between(a, b):
    return (b.year - a.year) * 12 + (b.month - a.month)


def _nanmean(m, axis=1):
    with np.errstate(invalid="ignore", divide="ignore"):
        cnt = np.sum(~np.isnan(m), axis=axis)
        tot = np.nansum(m, axis=axis)
        return np.where(cnt > 0, tot / np.maximum(cnt, 1), np.nan)


def load_monthly(spec):
    """Reads, de-duplicates and joins the monthly tables. Returns the long table and row counts."""
    ent, tcol = spec["entity_id"], spec["time_column"]
    steps, merged = [], None
    for rel in spec["tables"]["monthly"]:
        df = read_table(spec, rel)
        before = len(df)
        df = df.drop_duplicates(subset=[ent, tcol], keep="first")
        steps.append({"step": f"{Path(rel).name}: drop duplicate {ent} x {tcol}", "rows_before": before, "rows_after": len(df)})
        merged = df if merged is None else merged.merge(df, on=[ent, tcol], how="outer")
    merged[tcol] = pd.to_datetime(merged[tcol])
    return merged, steps


def account_features(spec, snapshots):
    """Every account on each snapshot month: the features, plus whether it pays and its tenure.

    Returns (features, steps). The feature code is the churn project's, unchanged.
    """
    ent, tcol, vcol = spec["entity_id"], spec["time_column"], spec["value_column"]
    ordinal = spec.get("ordinal", {})
    accounts = read_table(spec, spec["tables"]["accounts"])
    long, steps = load_monthly(spec)

    months = pd.date_range(long[tcol].min(), long[tcol].max(), freq="MS")
    ids = np.sort(accounts[ent].unique())
    row = {e: i for i, e in enumerate(ids)}
    col = {m: j for j, m in enumerate(months)}
    ri = long[ent].map(row).to_numpy()
    ci = long[tcol].map(col).to_numpy()

    def wide(series):
        m = np.full((len(ids), len(months)), np.nan)
        m[ri, ci] = series.to_numpy(dtype=float)
        return m

    # Which columns are numbers, which are ordinal levels, which are text we skip.
    numeric, levels = {}, {}
    for c in long.columns:
        if c in (ent, tcol) or c in spec.get("ignore_columns", []):
            continue
        s = long[c]
        if pd.api.types.is_numeric_dtype(s):
            numeric[c] = wide(s)
        elif s.dropna().isin(list(ordinal) + ["Not Relevant"]).mean() > 0.9:
            levels[c] = wide(s.map(ordinal).astype(float))

    acc = accounts.set_index(ent).loc[ids]
    V = numeric[vcol]
    created = pd.to_datetime(acc[spec["created_column"]]).to_numpy()
    feats = []
    for snap in sorted(pd.to_datetime(pd.Series(snapshots)).unique()):
        s = col[pd.Timestamp(snap)]
        snap = months[s]
        tenure = np.array([_months_between(pd.Timestamp(c), snap) for c in created])
        lo3, lo6 = max(s - ROLL + 1, 0), max(s - 2 * ROLL + 1, 0)
        f = {ent: ids, "snapshot": snap}
        f["pays"] = V[:, s] > 0
        f["tenure_months"] = tenure
        for c, M in numeric.items():
            if c == vcol:
                continue
            recent, earlier = _nanmean(M[:, lo3:s + 1]), _nanmean(M[:, lo6:lo3])
            f[c] = M[:, s]
            f[f"{c}_mean_3m"] = recent
            f[f"{c}_trend_3v3"] = (recent - earlier) / (np.abs(earlier) + 1)
            f[f"{c}_null_6m"] = np.isnan(M[:, lo6:s + 1]).sum(1)
        for c, M in levels.items():
            f[f"{c}_level"] = M[:, s]
            f[f"{c}_level_mean_3m"] = _nanmean(M[:, lo3:s + 1])
        if levels:
            f["products_medium_plus"] = sum(np.nan_to_num(M[:, s]) >= 2 for M in levels.values())
        # The value column: level, 3-month change, consecutive months of decline.
        f[vcol] = V[:, s]
        back = V[:, max(s - 3, 0)]
        f[f"{vcol}_chg_3m"] = (V[:, s] - back) / (np.abs(back) + 1)
        run = np.zeros(len(ids), dtype=int)
        alive = np.ones(len(ids), dtype=bool)
        thr = float(spec.get("value_decline_threshold", 0.0))
        for k in range(s, max(s - 12, 0), -1):
            down = alive & (V[:, k] < V[:, k - 1] * (1 - thr))
            run += down
            alive &= down
        f[f"{vcol}_down_run"] = run
        for name, (num, den) in spec.get("ratios", {}).items():
            d = acc[den].to_numpy(dtype=float)
            f[name] = numeric[num][:, s] / d
            f[f"{name}_mean_3m"] = _nanmean(numeric[num][:, lo3:s + 1]) / d
        if "contract" in spec:
            start = pd.to_datetime(acc[spec["contract"]["start_column"]]).to_numpy()
            cycle = acc[spec["contract"]["term_years_column"]].to_numpy(dtype=int) * 12
            since = np.array([_months_between(pd.Timestamp(c), snap) for c in start])
            f["months_to_renewal"] = (cycle - since % cycle) % cycle
        for c in spec.get("static_columns", []):
            f[c] = acc[c].to_numpy()
        for c in spec.get("presence_columns", []):
            f[f"has_{c}"] = acc[c].notna().to_numpy().astype(int)
        feats.append(pd.DataFrame(f))
    return pd.concat(feats, ignore_index=True), steps


def feature_columns(spec):
    """The features the model uses: the spec's fixed list."""
    return list(spec["features"])


def build_panel(spec):
    """One row per trial: id, snapshot (the month before), trial start, label, and the spec's features."""
    ent, lab = spec["entity_id"], spec["label"]
    trials = read_table(spec, spec["tables"]["trials"])
    trials["trial_start"] = pd.to_datetime(trials[lab["date_column"]])
    trials["snapshot"] = trials["trial_start"] - pd.DateOffset(months=1)
    trials["label"] = (trials[lab["column"]] == lab["positive"]).astype(int)
    feats, steps = account_features(spec, trials["snapshot"].unique())
    steps.append({"step": "trials", "rows_before": None, "rows_after": len(trials)})
    panel = trials[[ent, "snapshot", "trial_start", "label"]].merge(feats, on=[ent, "snapshot"], how="inner")
    steps.append({"step": "trials with a monthly history at the snapshot", "rows_before": len(trials), "rows_after": len(panel)})
    n = len(panel)
    keep = panel["pays"] & (panel["tenure_months"] >= spec["eligibility"]["min_tenure_months"])
    panel = panel[keep]
    steps.append({"step": f"keep eligible at the snapshot: {spec['value_column']} > 0 and tenure >= "
                          f"{spec['eligibility']['min_tenure_months']} months", "rows_before": n, "rows_after": len(panel)})
    panel = panel[[ent, "snapshot", "trial_start", "label"] + feature_columns(spec)]
    panel = panel.sort_values(["trial_start", ent]).reset_index(drop=True)
    return panel, steps


def build_pool(spec):
    """The accounts that could get a trial now: the last month in the data, eligible as the spec says."""
    ent, el = spec["entity_id"], spec["eligibility"]
    long, _ = load_monthly(spec)
    last = long[spec["time_column"]].max()
    feats, _ = account_features(spec, [last])
    steps = [{"step": f"accounts on {last:%b %Y}", "rows_before": None, "rows_after": len(feats)}]

    def keep(mask, text):
        nonlocal feats
        n = len(feats)
        feats = feats[mask]
        steps.append({"step": text, "rows_before": n, "rows_after": len(feats)})

    keep(feats["pays"], f"pays ({spec['value_column']} > 0)")
    keep(feats["tenure_months"] >= el["min_tenure_months"], f"tenure >= {el['min_tenure_months']} months")
    if el.get("not_licensed"):
        keep(feats[f"{el['not_licensed']}_level"].isna(), f"no {el['not_licensed']} licence")
    if el.get("not_trialed"):
        keep(~feats[ent].isin(read_table(spec, spec["tables"]["trials"])[ent]), "never had a trial")
    if el.get("not_bought"):
        keep(~feats[ent].isin(read_table(spec, spec["tables"]["purchases"])[ent]), "never bought")
    pool = feats[[ent, "snapshot"] + feature_columns(spec)].sort_values(ent).reset_index(drop=True)
    return pool, steps


def source_of(feature, spec):
    """The input column a feature was made from, so the analyst can ask "could I have known this?"."""
    for c in spec.get("presence_columns", []):
        if feature == f"has_{c}":
            return f"{c} (accounts table)"
    for c in spec.get("static_columns", []):
        if feature == c or feature.startswith(c + "_"):       # one-hot columns such as region_EMEA
            return f"{c} (accounts table)"
    if feature == "months_to_renewal":
        return "contract start and term (accounts table)"
    if feature == "products_medium_plus":
        return "product levels (monthly)"
    if feature == "tenure_months":
        return f"{spec.get('created_column')} (accounts table)"
    for name, (num, den) in spec.get("ratios", {}).items():
        if feature.startswith(name):
            return f"{num} / {den}"
    base = feature
    for suffix in ("_mean_3m", "_trend_3v3", "_null_6m", "_level_mean_3m", "_level", "_chg_3m", "_down_run"):
        base = base.removesuffix(suffix)
    return f"{base} (monthly)"


def window_of(feature, spec):
    """How much history a feature looks at, counted back from the snapshot month."""
    if feature in spec.get("static_columns", []) or feature.startswith("has_"):
        return "no time: today's value"
    if feature in ("tenure_months", "months_to_renewal"):
        return "counted from a date to the snapshot"
    if feature.endswith("_trend_3v3"):
        return "6 months: last 3 against the 3 before"
    if feature.endswith("_mean_3m"):
        return "3 months: average"
    if feature.endswith("_chg_3m"):
        return "change over 3 months"
    return "1 month: the snapshot month"


def snapshot_section(panel, spec):
    """Explains the trial row, with a timeline drawn for one real trial that bought."""
    ent = spec["entity_id"]
    row = panel[panel["label"] == 1].sort_values(["trial_start", ent]).iloc[-1]
    snap, start = row["snapshot"], row["trial_start"]
    before = [snap - pd.DateOffset(months=i) for i in range(2 * ROLL - 1, -1, -1)]
    cell, pad = 6, " " * 12
    seg = lambda text, n: "<" + f" {text} ".center(n * cell - 2, "-") + ">"
    bar = len(pad) + len(before) * cell
    end = start + pd.Timedelta(days=30)
    trial = "<-- 30-day trial: not used -->"
    drawing = [
        f"Example: {row[ent]}, trial starting {start:%-d %b %Y}", "",
        pad + "".join(f"{m:%b}".ljust(cell) for m in before) + "| " + f"{start:%b}".ljust(cell),
        "features x".ljust(len(pad)) + seg(f"previous {ROLL}", ROLL) + seg(f"last {ROLL}", ROLL) + "|",
        "trial".ljust(len(pad)) + " " * (len(before) * cell) + "| " + trial,
        "target y".ljust(len(pad)) + " " * (len(before) * cell + 2 + len(trial)) + f"^ bought? known {end:%-d %b}",
        " " * (bar - len("snapshot ^") + 1) + "snapshot ^"]
    first, last = panel["trial_start"].min(), panel["trial_start"].max()
    return ["### The trial row", "",
            "One row = one trial: what we knew before it started, and whether the account bought.", "",
            "```", *drawing, "```", "",
            f"- **Features (x)** use only months up to the **snapshot**, the month before the trial: the last {ROLL} "
            f"months, and the {ROLL} before them for trends. The trial month itself is already in-trial data.",
            f"- **Target (y)** is 1 if the account bought {spec['label']['product']} at the end of its 30-day trial "
            f"(for this trial, known on {end:%-d %b %Y}). Nothing from the trial itself is used. For {row[ent]} it is 1.",
            f"- **Trials** start on the 1st of each month, from {first:%b %Y} to {last:%b %Y} "
            f"({panel['trial_start'].nunique()} months).", ""]


def features_by_table(panel, feats, spec):
    """How many model features each input table gives, counting one yes/no feature per value of a text column."""
    owner = {}
    for rel in spec["tables"]["monthly"]:
        for c in pd.read_csv(Path(spec["_root"]) / rel, nrows=0).columns:
            owner.setdefault(c, Path(rel).stem)
    accounts = Path(spec["tables"]["accounts"]).stem
    counts = {}
    for f in feats:
        src = source_of(f, spec).split(" ")[0]
        if f == "products_medium_plus":       # counted from the level columns: same table as them
            src = next(c.removesuffix("_level") for c in feats if c.endswith("_level"))
        table = accounts if "(accounts table)" in source_of(f, spec) else owner.get(src, accounts)
        counts[table] = counts.get(table, 0) + _width(panel[f])
    return counts


def _width(s):
    return 1 if pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s) else s.astype(str).nunique()


def run(spec, out):
    """Builds the panel, writes 02_panel.csv, 02_panel.json and 02_features.md, and returns a one-line summary."""
    panel, steps = build_panel(spec)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    panel.to_csv(out / "02_panel.csv", index=False)
    feats = feature_columns(spec)
    model_features = sum(_width(panel[c]) for c in feats)
    by_table = features_by_table(panel, feats, spec)
    summary = {"rows": len(panel), "accounts": int(panel[spec["entity_id"]].nunique()),
               "months": int(panel["trial_start"].nunique()), "buyers": int(panel["label"].sum()),
               "label_rate": round(float(panel["label"].mean()), 4), "features": feats,
               "model_features": model_features, "features_by_table": by_table, "steps": steps}
    (out / "02_panel.json").write_text(json.dumps(summary, indent=1, default=str))
    lines = [f"**{summary['rows']:,} rows**: one per trial, {summary['months']} monthly rounds "
             f"({panel['trial_start'].min():%b %Y} – {panel['trial_start'].max():%b %Y}). "
             f"**{summary['buyers']} bought** ({summary['label_rate']:.0%}). **{len(feats)} features**, "
             f"**{model_features} model columns** (text columns such as region become one yes/no column per value).", ""]
    lines += ["### Features by table", "", "| Table | Model columns |", "|---|---|"]
    lines += [f"| {t} | {n} |" for t, n in by_table.items()]
    lines += [f"| **Total** | **{model_features}** |", ""]
    lines += snapshot_section(panel, spec)
    lines += ["### Rows at each step", "", "| Step | Rows before | Rows after |", "|---|---|---|"]
    for s in steps:
        before = "" if s["rows_before"] is None else f"{s['rows_before']:,}"
        lines.append(f"| {s['step']} | {before} | {s['rows_after']:,} |")
    lines += ["", "### The features", "", "For every feature, ask: could I have known this before the trial started?", "",
              "| # | Feature | Made from | Looks at |", "|---|---|---|---|"]
    lines += [f"| {i} | {f} | {source_of(f, spec)} | {window_of(f, spec)} |" for i, f in enumerate(feats, 1)]
    (out / "02_features.md").write_text("\n".join(lines) + "\n")
    return (f"{summary['rows']} trials, {summary['buyers']} bought ({summary['label_rate']:.1%}), "
            f"{len(feats)} features, {model_features} model columns")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default="ml_spec.yaml")
    ap.add_argument("--out", default="runs/latest")
    a = ap.parse_args()
    print(run(load_spec(a.spec), a.out))


if __name__ == "__main__":
    main()
