---
name: build-panel
description: Step 4 of the ML pipeline, feature engineering. Runs scripts/build_panel.py to turn each trial into one row, with features from the month before it started and the outcome of the trial. Use for /build-panel, after a change to ml_spec.yaml, or for questions about features.
---

# Step 4 · Feature engineering

**Start the reply with these two lines:**

```
Skill: /build-panel · Step 4 · Feature engineering
Purpose: Turn each trial into features (x) from before it started, and its outcome (y).
```

**Before each command, show it on its own line** as `Running: <the exact command>`.

Each row is one trial: what we knew before it started (the features, x) and whether the account bought (the target, y). The features are made with the same code as the churn project.

## Run

```
.venv/bin/python scripts/build_panel.py --spec ml_spec.yaml --out runs/latest
```

## Report

Read `runs/latest/02_features.md` and report:
1. **The trial row.** Copy the timeline drawing exactly as written, inside a code block, then explain it in two or three short sentences: one row is one trial; the features look back from the snapshot, the month before the trial, because the trial month itself is already in-trial data; the target is whether the account bought.
2. The rows: trials, monthly rounds, how many bought, and the row counts at each step.
3. **The features by table**, copied from the "Features by table" table, with the total. Quote these numbers; never count features yourself. The spec keeps a fixed list of 20 features; text columns such as region become one yes/no column per value.
4. The feature list with what each one is made from and **how much history it looks at** (the "Looks at" column): one month, a 3-month average, a trend over 6 months, a change over 3 months, a count from a date, or no time at all.

## Stop

Ask to go through the list with one question: **"Could I have known this before the trial started?"** Columns from the one-row-per-account table deserve the hardest look.

If a feature must go, show the change (remove it from `features` in `ml_spec.yaml`), apply it after a yes, and run this step again. Then stop.
