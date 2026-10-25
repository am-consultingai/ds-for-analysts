---
name: build-panel
description: Step 4 of the ML pipeline, feature engineering. Runs scripts/build_panel.py to turn the monthly tables into one row per account per month, with features from before each date and the target from the 90 days after. Use for /build-panel, after a change to ml_spec.yaml, or for questions about features.
---

# Step 4 · Feature engineering

**Start the reply with these two lines:**

```
Skill: /build-panel · Step 4 · Feature engineering
Purpose: Turn monthly history into features (x) and the target (y): one row per account per month.
```

**Before each command, show it on its own line** as `Running: <the exact command>`.

Each row is one account on one date: what we knew on that date (the features, x) and what happened in the next 90 days (the target, y).

## Run

```
.venv/bin/python scripts/build_panel.py --spec ml_spec.yaml --out runs/latest
```

## Report

Read `runs/latest/02_features.md` and report:
1. **The snapshot.** Copy the timeline drawing exactly as written, inside a code block, then explain it in two or three short sentences: one row is one account on one snapshot date, features look back, the target looks 3 months ahead, and an account has a row only in months when it pays and has enough tenure.
2. The rows: accounts × monthly snapshots, the label rate, and the row counts at each step (duplicates dropped, accounts not eligible).
3. **The features by table**, copied from the "Features by table" table, with the total. Quote these numbers; never count features yourself. If the total is one more than the slides' 54, the extra one is `days_since_last_login`, made from `last_login_date`. Then say how they are made: last value, 3-month average, last 3 months against the 3 before, missing months, ARR change, downgrade months in a row, months to renewal, and the account's fixed columns.
4. The feature list, grouped by the table each one comes from (the "Made from" column).

## Stop

Ask to go through the list with one question: **"Could I have known this on the snapshot date?"** Columns from the one-row-per-account table deserve the hardest look: some are filled in on the day the data was pulled.

If a column must go, show the change (add it to `excluded_columns` in `ml_spec.yaml`), apply it after a yes, and run this step again. Then stop.
