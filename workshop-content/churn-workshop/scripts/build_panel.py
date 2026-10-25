"""Builds the snapshot panel: one row per entity per snapshot date.

    python build_panel.py --spec ml_spec.yaml [--out runs/latest]

Features use only data from on or before the snapshot month. The label is
whether the event happens in the following `horizon_months`. Snapshots whose
horizon runs past the data are dropped (no label yet). Everything specific to
the project comes from the spec.
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


def build_panel(spec, include_excluded=False, latest_only=False):
    """Returns (panel, steps). `include_excluded=True` keeps the spec's excluded columns (for leak demos).

    `latest_only=True` builds only the last month in the data, which has no label yet: the rows to score.
    """
    ent, tcol, vcol = spec["entity_id"], spec["time_column"], spec["value_column"]
    horizon = int(spec["label"]["horizon_months"])
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
    # The event: the value goes from above 0 to 0. First such month per entity.
    prev = np.c_[np.full(len(ids), np.nan), V[:, :-1]]
    ev = (V == 0) & (prev > 0)
    event_idx = np.where(ev.any(1), ev.argmax(1), -1)

    first = col[pd.Timestamp(spec["snapshots"]["first"])]
    last = col[pd.Timestamp(spec["snapshots"]["last"])]
    last = min(last, len(months) - 1 - horizon)            # censoring: the label window must be complete
    if latest_only:
        first = last = len(months) - 1
    created = pd.to_datetime(acc[spec["created_column"]]).to_numpy()
    feats = []
    for s in range(first, last + 1):
        snap = months[s]
        tenure = np.array([_months_between(pd.Timestamp(c), snap) for c in created])
        lo3, lo6 = max(s - ROLL + 1, 0), max(s - 2 * ROLL + 1, 0)
        f = {ent: ids, "snapshot": snap}
        f["label"] = ((event_idx > s) & (event_idx <= s + horizon)).astype(int)
        f["eligible"] = (V[:, s] > 0) & (tenure >= spec["eligibility"]["min_tenure_months"])
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
        for c in spec.get("date_columns", []):
            if c in spec.get("excluded_columns", []) and not include_excluded:
                continue
            f[f"days_since_{c.removesuffix('_date')}"] = (snap - pd.to_datetime(acc[c])).dt.days.to_numpy()
        for c in spec.get("static_columns", []):
            f[c] = acc[c].to_numpy()
        for c in spec.get("presence_columns", []):
            f[f"has_{c}"] = acc[c].notna().to_numpy().astype(int)
        feats.append(pd.DataFrame(f))

    panel = pd.concat(feats, ignore_index=True)
    steps.append({"step": "all entity x snapshot rows", "rows_before": None, "rows_after": len(panel)})
    n = len(panel)
    panel = panel[panel["eligible"]].drop(columns="eligible").reset_index(drop=True)
    steps.append({"step": f"keep eligible: {vcol} > 0 and tenure >= {spec['eligibility']['min_tenure_months']} months",
                  "rows_before": n, "rows_after": len(panel)})
    return panel, steps


def feature_columns(panel, spec):
    """Every column except the id, the date, the label and the value used for ARR at risk."""
    return [c for c in panel.columns if c not in (spec["entity_id"], "snapshot", "label")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default="ml_spec.yaml")
    ap.add_argument("--out", default="runs/latest")
    a = ap.parse_args()
    spec = load_spec(a.spec)
    print(run(spec, a.out))


def source_of(feature, spec):
    """The input column a feature was made from, so the analyst can ask "could I have known this?"."""
    for c in spec.get("date_columns", []):
        if feature == f"days_since_{c.removesuffix('_date')}":
            return f"{c} (accounts table)"
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


def snapshot_section(panel, spec):
    """Explains the snapshot, with a timeline drawn for one real account whose target is 1."""
    h, ent = int(spec["label"]["horizon_months"]), spec["entity_id"]
    snap = panel.loc[panel["label"] == 1, "snapshot"].max()
    acc = panel.loc[(panel["label"] == 1) & (panel["snapshot"] == snap), ent].min()
    before = [snap - pd.DateOffset(months=i) for i in range(2 * ROLL - 1, -1, -1)]
    after = [snap + pd.DateOffset(months=i) for i in range(1, h + 1)]
    cell, pad = 6, " " * 12
    seg = lambda text, n: "<" + f" {text} ".center(n * cell - 2, "-") + ">"
    bar = len(pad) + len(before) * cell
    drawing = [
        f"Example: {acc}, on the {snap:%-d %b %Y} snapshot", "",
        pad + "".join(f"{m:%b}".ljust(cell) for m in before) + "| " + "".join(f"{m:%b}".ljust(cell) for m in after),
        "features x".ljust(len(pad)) + seg(f"previous {ROLL}", ROLL) + seg(f"last {ROLL}", ROLL) + "|",
        "target y".ljust(len(pad)) + " " * (len(before) * cell) + "| " + seg(f"next {h}", h),
        " " * (bar - len("snapshot date ^") + 1) + "snapshot date ^"]
    first, last = panel["snapshot"].min(), panel["snapshot"].max()
    return ["### The snapshot", "",
            "One row = one account on one **snapshot date**: what we knew on that date, and what happened next.", "",
            "```", *drawing, "```", "",
            f"- **Features (x)** use only months up to the snapshot: the last {ROLL} months, and the {ROLL} before them for trends.",
            f"- **Target (y)** looks at the {h} months after it: 1 if ARR drops to 0 in that window. For {acc} it is 1.",
            f"- **Snapshots** come once a month, from {first:%b %Y} to {last:%b %Y} ({panel['snapshot'].nunique()} in all). "
            f"The last is {last:%b %Y} because its target needs the {h} months after it.",
            f"- **On each snapshot**, an account gets a row only if it pays that month (ARR above 0) and has at least "
            f"{spec['eligibility']['min_tenure_months']} months of tenure. Accounts that already left, or only just "
            "started, have no row that month.", ""]


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
        n = 1 if pd.api.types.is_numeric_dtype(panel[f]) and not pd.api.types.is_bool_dtype(panel[f]) \
            else panel[f].astype(str).nunique()
        counts[table] = counts.get(table, 0) + n
    return counts


def run(spec, out):
    """Builds the panel, writes 02_panel.csv, 02_panel.json and 02_features.md, and returns a one-line summary."""
    panel, steps = build_panel(spec)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    panel.to_csv(out / "02_panel.csv", index=False)
    feats = feature_columns(panel, spec)
    # Text columns become one yes/no column per value when the model is trained.
    model_features = sum(1 if pd.api.types.is_numeric_dtype(panel[c]) and not pd.api.types.is_bool_dtype(panel[c])
                         else panel[c].astype(str).nunique() for c in feats)
    summary = {"rows": len(panel), "entities": int(panel[spec["entity_id"]].nunique()),
               "snapshots": int(panel["snapshot"].nunique()), "label_rate": round(float(panel["label"].mean()), 4),
               "features": feats, "model_features": model_features, "steps": steps}
    (out / "02_panel.json").write_text(json.dumps(summary, indent=1, default=str))
    lines = [f"**{summary['rows']:,} rows**: {summary['entities']:,} accounts × {summary['snapshots']} monthly snapshots "
             f"({panel['snapshot'].min():%b %Y} – {panel['snapshot'].max():%b %Y}). "
             f"Label rate {summary['label_rate']:.1%}. **{model_features} features** "
             f"({len(feats)} columns; text columns such as region become one yes/no feature per value).", ""]
    by_table = features_by_table(panel, feats, spec)
    summary["features_by_table"] = by_table
    (out / "02_panel.json").write_text(json.dumps(summary, indent=1, default=str))
    lines += ["### Features by table", "", "| Table | Features |", "|---|---|"]
    lines += [f"| {t} | {n} |" for t, n in by_table.items()]
    lines += [f"| **Total** | **{model_features}** |", "",
              "Text columns count as one yes/no feature per value (segment, region, package type and level, auto-renewal).", ""]
    lines += snapshot_section(panel, spec)
    lines += ["### Rows at each step", "", "| Step | Rows before | Rows after |", "|---|---|---|"]
    for s in steps:
        before = "" if s["rows_before"] is None else f"{s['rows_before']:,}"
        lines.append(f"| {s['step']} | {before} | {s['rows_after']:,} |")
    lines += ["", "### The features", "", "For every feature, ask: could I have known this on the snapshot date?", "",
              "| # | Feature | Made from |", "|---|---|---|"]
    lines += [f"| {i} | {f} | {source_of(f, spec)} |" for i, f in enumerate(feats, 1)]
    (out / "02_features.md").write_text("\n".join(lines) + "\n")
    return (f"{summary['rows']} rows, {summary['entities']} entities, {summary['snapshots']} snapshots, "
            f"label rate {summary['label_rate']:.1%}, {model_features} features")


if __name__ == "__main__":
    main()
