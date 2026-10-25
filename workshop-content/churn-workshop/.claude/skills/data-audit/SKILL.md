---
name: data-audit
description: Step 3 of the ML pipeline, check the data. Runs scripts/audit.py on the tables listed in ml_spec.yaml and reports problems (text read as missing, duplicates, rows after churn, missing values) before any modelling. Use for /data-audit or to check the data.
---

# Step 3 · Check the data

**Start the reply with these two lines:**

```
Skill: /data-audit · Step 3 · Check the data
Purpose: Find the problems in the data before they find you.
```

**Before each command, show it on its own line** as `Running: <the exact command>`.

## Run

This is usually the first step that runs Python. If `.venv` doesn't exist in the project folder, connect the workshop environment first:

```
./link-env.sh
```

If it ends with an ERROR, show its message and stop: the setup command from the workshop page has to run first. If `.venv` already exists, skip this.

```
.venv/bin/python scripts/audit.py --spec ml_spec.yaml --out runs/latest
```

## Report

Read `runs/latest/01_audit.md` and report:
1. The tables: rows, columns, first and last month.
2. Each finding: what it is, how many rows, and why it matters, in plain words.
3. How the pipeline already handles each one, so it's clear what is fixed and what is a choice:

| Finding | Handled by |
|---|---|
| Text read as missing ("NA" = North America) | The scripts read only empty cells as missing |
| Duplicate account-months | `/build-panel` keeps the first row and reports the counts |
| Rows after churn (ARR = 0) | Those months are not scored: an account must have ARR above 0 |
| Many accounts start in the first month | They existed before the data begins. Tenure comes from `created_date`, not from the first row |
| Missing values (CSM name, traffic) | Kept as information: `has_csm_name`, and missing-month counts |

Don't fix anything in the data. Don't calculate anything that isn't in the report.

## Stop

Ask: **"Go or no-go? Is any of these a problem to fix before going on?"** Then stop.
