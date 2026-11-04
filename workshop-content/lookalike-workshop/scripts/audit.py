"""Audits the raw tables before any modelling.

    python audit.py --spec ml_spec.yaml [--out runs/latest]

Monthly and account tables: shape and date range, text that pandas reads as missing, duplicates on
entity x month, rows after churn (ghost rows), accounts piled up in the first month (the window
edge) and columns with many missing values. Trials and purchases: trials per month, the outcome's
values, accounts with more than one trial, and whether every buyer has a purchase. Counts only:
no customer rows are printed.
"""
import argparse
from pathlib import Path

import pandas as pd

from common import load_spec, read_table, table_path, write_step

MISSING_WORDS = ["NA", "N/A", "None", "null", "NULL", "nan"]


def check_tables(spec):
    ent, tcol, vcol = spec["entity_id"], spec["time_column"], spec["value_column"]
    t = spec["tables"]
    tables, findings = [], []
    dates = {t["trials"]: spec["label"]["date_column"], t["purchases"]: "purchase_date"}
    for rel in [t["accounts"]] + list(t["monthly"]) + [t["trials"], t["purchases"]]:
        df = read_table(spec, rel)
        naive = pd.read_csv(table_path(spec, rel))           # how a default read sees it
        info = {"table": Path(rel).name, "rows": len(df), "columns": df.shape[1]}
        when = tcol if tcol in df else dates.get(rel)
        if when:
            info["first"], info["last"] = df[when].min(), df[when].max()
        tables.append(info)
        # Text that pandas' default read silently turns into missing values.
        for c in df.columns:
            if not pd.api.types.is_numeric_dtype(df[c]) and not pd.api.types.is_bool_dtype(df[c]):
                words = df[c].isin(MISSING_WORDS)
                if words.any() and naive[c].isna().sum() > df[c].isna().sum():
                    top = df.loc[words, c].value_counts().index[0]
                    findings.append({"check": "text read as missing", "table": info["table"], "column": c,
                                     "count": int(words.sum()),
                                     "detail": f'"{top}" is a real value here, but pandas reads it as missing by default'})
        if tcol in df:
            d = int(df.duplicated(subset=[ent, tcol]).sum())
            if d:
                findings.append({"check": "duplicate rows", "table": info["table"], "column": f"{ent} x {tcol}",
                                 "count": d, "detail": "the same account and month appear more than once"})
        if vcol in df and tcol in df:
            s = df.drop_duplicates(subset=[ent, tcol]).sort_values([ent, tcol])
            zero = s[vcol] == 0
            after = zero & zero.groupby(s[ent]).shift(1, fill_value=False)
            if after.any():
                findings.append({"check": "rows after churn", "table": info["table"], "column": vcol,
                                 "count": int(after.sum()),
                                 "detail": f"{s.loc[after, ent].nunique()} accounts keep rows with {vcol} = 0 after they left"})
            firsts = s.groupby(ent)[tcol].min()
            edge = int((firsts == s[tcol].min()).sum())
            if edge > 0.25 * len(firsts):
                findings.append({"check": "window edge", "table": info["table"], "column": tcol, "count": edge,
                                 "detail": f"{edge} accounts start in the first month ({s[tcol].min()}): "
                                           "they existed before the data begins, so they look new"})
        for c in df.columns:
            share = df[c].isna().mean()
            if 0.05 <= share < 1 and c != tcol:
                findings.append({"check": "many missing values", "table": info["table"], "column": c,
                                 "count": int(df[c].isna().sum()), "detail": f"{share:.0%} of rows are empty"})
    return tables, findings


def check_trials(spec):
    """Facts about the trials and purchases that later steps rely on."""
    ent, lab = spec["entity_id"], spec["label"]
    tr = read_table(spec, spec["tables"]["trials"])
    pu = read_table(spec, spec["tables"]["purchases"])
    start = pd.to_datetime(tr[lab["date_column"]])
    per_month = start.dt.to_period("M").value_counts()
    buyers = set(tr.loc[tr[lab["column"]] == lab["positive"], ent])
    bought = set(pu.loc[pu["product"] == lab["product"], ent])
    return {"trials": len(tr), "months": int(per_month.size), "first": str(start.min().date()), "last": str(start.max().date()),
            "per_month_min": int(per_month.min()), "per_month_max": int(per_month.max()),
            "start_days": sorted(int(d) for d in start.dt.day.unique()),
            "lengths": sorted(int(v) for v in tr["trial_length_days"].unique()) if "trial_length_days" in tr else [],
            "outcome_values": {str(k): int(v) for k, v in tr[lab["column"]].value_counts().items()},
            "accounts_with_more_than_one_trial": int(tr[ent].duplicated().sum()),
            "buyers_without_purchase": len(buyers - bought),
            "purchases_by_source": {str(k): int(v) for k, v in pu["source"].value_counts().items()} if "source" in pu else {}}


def to_markdown(result):
    tv = result["trials"]
    lines = ["| Table | Rows | Columns | First | Last |", "|---|---|---|---|---|"]
    for t in result["tables"]:
        lines.append(f"| {t['table']} | {t['rows']:,} | {t['columns']} | {t.get('first', '')} | {t.get('last', '')} |")
    lines += ["", "| # | Check | Where | Count | What it means |", "|---|---|---|---|---|"]
    for i, f in enumerate(result["findings"], 1):
        lines.append(f"| {i} | {f['check']} | {f['table']} · {f['column']} | {f['count']:,} | {f['detail']} |")
    lines += ["", "### The trials", "", "| Fact | Value |", "|---|---|",
              f"| Trials | {tv['trials']} in {tv['months']} months ({tv['first']} – {tv['last']}) |",
              f"| Trials per month | {tv['per_month_min']}–{tv['per_month_max']} |",
              f"| Day of the month a trial starts | {', '.join(map(str, tv['start_days']))} |",
              f"| Trial length (days) | {', '.join(map(str, tv['lengths']))} |",
              f"| Outcome values | " + ", ".join(f"{k}: {v}" for k, v in tv["outcome_values"].items()) + " |",
              f"| Accounts with more than one trial | {tv['accounts_with_more_than_one_trial']} |",
              f"| Buyers with no purchase record | {tv['buyers_without_purchase']} |",
              f"| Purchases by source | " + ", ".join(f"{k}: {v}" for k, v in tv["purchases_by_source"].items()) + " |"]
    return "\n".join(lines)


def run(spec, out):
    tables, findings = check_tables(spec)
    result = {"tables": tables, "findings": findings, "trials": check_trials(spec)}
    md = to_markdown(result)
    write_step(out, "01_audit", result, md)
    return md


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default="ml_spec.yaml")
    ap.add_argument("--out", default="runs/latest")
    a = ap.parse_args()
    print(run(load_spec(a.spec), a.out))


if __name__ == "__main__":
    main()
