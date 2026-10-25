---
name: baseline
description: Step 2 of the ML pipeline, today's rule. Scores the rule the business uses today (the baseline in ml_spec.yaml) on the test months with precision@50 and recall@50: the numbers any model must beat. Use for /baseline or to see how good the current rule is.
---

# Step 2 · Today's rule

**Start the reply with these two lines:**

```
Skill: /baseline · Step 2 · Today's rule
Purpose: Score the rule used today: the numbers any model must beat.
```

**Before each command, show it on its own line** as `Running: <the exact command>`.

The baseline is the rule used today, scored exactly like the model will be. A model that can't beat it isn't worth using.

## Run

The rule is scored on the test months, so the panel must exist. If `runs/latest/02_panel.csv` is missing, say so and run `/build-panel` first.

```
.venv/bin/python scripts/baseline.py --spec ml_spec.yaml --out runs/latest
```

## Report

Read `runs/latest/04_baseline.md` and report:
- the rule, in words (`arr_down_run >= 3` = three downgrade months in a row);
- **precision@50**: of the 50 accounts called each month, how many were really leaving;
- **recall@50**: of all the accounts that left each month, how many those 50 calls reached;
- the sentence "These are the numbers to beat."

## Stop

Ask: **"Is this really the rule we use today?"** If a different rule is described, write it as a `baseline.rule` expression over the panel's columns, show the change to `ml_spec.yaml`, and apply it only after a yes. Then stop.
