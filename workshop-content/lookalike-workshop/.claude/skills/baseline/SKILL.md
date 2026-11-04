---
name: baseline
description: Step 2 of the ML pipeline, today's rule. Scores the rule the business uses today to pick trials (the baseline in ml_spec.yaml) on the test months, with AUC, buyers in picks and sales per month: the numbers any model must beat. Use for /baseline or to see how good the current rule is.
---

# Step 2 · Today's rule

**Start the reply with these two lines:**

```
Skill: /baseline · Step 2 · Today's rule
Purpose: Score the rule used today: the numbers any model must beat.
```

**Before each command, show it on its own line** as `Running: <the exact command>`.

The baseline is the rule used today, scored exactly like the models will be. A model that can't beat it isn't worth using.

## Run

The rule is scored on the test months, so the panel must exist. If `runs/latest/02_panel.csv` is missing, say so and run `/build-panel` first.

```
.venv/bin/python scripts/baseline.py --spec ml_spec.yaml --out runs/latest
```

## Report

Read `runs/latest/04_baseline.md` and report:
- the rule, in words: Strategic, Enterprise or Mid-Market accounts with SKAN or Analytics at Medium or above come first, then the rest by ARR;
- **AUC**: the chance a buyer is ranked above a non-buyer (0.50 is a coin flip);
- **buyers in picks**: each test month the rule picks its top 8 of the 20 trialed accounts; how many of those picks bought;
- **sales per month**: what that rate gives from 20 leads a month;
- how many accounts the rule actually picks each month, and the average trial's conversion, for context;
- the sentence "These are the numbers to beat."

## Stop

Ask: **"Is this really how trials are picked today?"** If a different rule is described, write it as a `baseline.rule` expression over the panel's columns, show the change to `ml_spec.yaml`, and apply it only after a yes. Then stop.
