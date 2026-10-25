"""Audits the raw tables before any modelling.

    python audit.py --spec ml_spec.yaml [--out runs/latest]

Reports shape and date range, text that pandas reads as missing, duplicates on
entity x time, rows after the event (ghost rows), events piled up in the first
month (the window edge) and columns with many missing values. Counts only: no
customer rows are printed.
"""
import argparse
from pathlib import Path

import pandas as pd

from common import load_spec, read_table, table_path, write_step

MISSING_WORDS = ["NA", "N/A", "None", "null", "NULL", "nan"]


def audit(spec):
    ent, tcol, vcol = spec["entity_id"], spec["time_column"], spec["value_column"]
    tables, findings = [], []
    paths = [spec["tables"]["accounts"]] + list(spec["tables"]["monthly"])
    for rel in paths:
        df = read_table(spec, rel)
        naive = pd.read_csv(table_path(spec, rel))           # how a default read sees it
        info = {"table": Path(rel).name, "rows": len(df), "columns": df.shape[1]}
        if tcol in df:
            info["first"], info["last"] = df[tcol].min(), df[tcol].max()
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
        if vcol in df:
            s = df.drop_duplicates(subset=[ent, tcol]).sort_values([ent, tcol])
            zero = s[vcol] == 0
            after = zero & zero.groupby(s[ent]).shift(1, fill_value=False)
            if after.any():
                findings.append({"check": "rows after the event", "table": info["table"], "column": vcol,
                                 "count": int(after.sum()),
                                 "detail": f"{s.loc[after, ent].nunique()} accounts keep rows with {vcol} = 0 after they churned"})
            firsts = s.groupby(ent)[tcol].min()
            edge = int((firsts == s[tcol].min()).sum())
            if edge > 0.25 * len(firsts):
                findings.append({"check": "window edge", "table": info["table"], "column": tcol,
                                 "count": edge,
                                 "detail": f"{edge} accounts start in the first month ({s[tcol].min()}): "
                                           "they existed before the data begins, so they look new"})
        for c in df.columns:
            share = df[c].isna().mean()
            if 0.05 <= share < 1 and c not in (tcol,):
                findings.append({"check": "many missing values", "table": info["table"], "column": c,
                                 "count": int(df[c].isna().sum()), "detail": f"{share:.0%} of rows are empty"})
    return {"tables": tables, "findings": findings}


def to_markdown(result):
    lines = ["| Table | Rows | Columns | First | Last |", "|---|---|---|---|---|"]
    for t in result["tables"]:
        lines.append(f"| {t['table']} | {t['rows']:,} | {t['columns']} | {t.get('first', '')} | {t.get('last', '')} |")
    lines += ["", "| # | Check | Where | Count | What it means |", "|---|---|---|---|---|"]
    for i, f in enumerate(result["findings"], 1):
        lines.append(f"| {i} | {f['check']} | {f['table']} · {f['column']} | {f['count']:,} | {f['detail']} |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default="ml_spec.yaml")
    ap.add_argument("--out", default="runs/latest")
    a = ap.parse_args()
    print(run(load_spec(a.spec), a.out))


def run(spec, out):
    result = audit(spec)
    write_step(out, "01_audit", result, to_markdown(result))
    return to_markdown(result)


if __name__ == "__main__":
    main()
