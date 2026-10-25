---
name: split
description: Step 5 of the ML pipeline, split. Runs scripts/split.py to split the panel by time with a gap: the model learns on earlier months and is tested on later months it has never seen. Use for /split or to explain how the model is tested.
---

# Step 5 · Split

**Start the reply with these two lines:**

```
Skill: /split · Step 5 · Split
Purpose: Learn on earlier months, test on later months the model has never seen.
```

**Before each command, show it on its own line** as `Running: <the exact command>`.

## Run

Needs `runs/latest/02_panel.csv`. If it's missing, run `/build-panel` first.

```
.venv/bin/python scripts/split.py --spec ml_spec.yaml --out runs/latest
```

## Report

Read `runs/latest/03_split.md` and report, for each side: the months, the rows, the accounts and the label rate. Explain the gap in one sentence: each target looks 90 days ahead, so without a gap the last training rows would see into the test months.

## Rules

- Split by time only. If a random split is requested, explain why not: rows from the test months would land in training, and the model would be tested on months it has already seen. The script refuses it too.

## Stop

Ask: **"Do both sides look sensible? Enough rows, and a similar label rate?"** Then stop.
