---
name: evaluate
description: Step 7 of the ML pipeline, evaluate. Runs scripts/baseline.py and scripts/evaluate.py to compare the trained model with today's rule on the same test months, using precision@50 and recall@50, training months beside test months, with warnings. Use for /evaluate or to judge how good the model is.
---

# Step 7 · Evaluate

**Start the reply with these two lines:**

```
Skill: /evaluate · Step 7 · Evaluate
Purpose: Check whether the model beats today's rule, honestly.
```

**Before each command, show it on its own line** as `Running: <the exact command>`.

## Run

Needs a trained model in `runs/latest/05_models/`. If it's missing, run `/train` first.

```
.venv/bin/python scripts/baseline.py --spec ml_spec.yaml --out runs/latest
.venv/bin/python scripts/evaluate.py --spec ml_spec.yaml --out runs/latest
```

## Report

Read `runs/latest/06_eval.md` and report:
1. **precision@50** on the test months, model against today's rule, in calls: "about 19 real leavers in 50 calls, against 15".
2. **recall@50**: the share of all leavers those 50 calls reach.
3. **Training months against test months.** A big drop means the model memorised the past, or a feature leaks the answer.
4. The real leavers in each test month's top 50. Point out any month where the model collapses.
5. **Every warning, word for word.** Don't soften them.

Use precision and recall only. Not accuracy, not AUC.

If there is a warning about a leak, or a result too good to be true, say plainly that no number can be trusted yet, and suggest `/leakage-check`.

## Stop

Ask: **"Does it beat today's rule? Is it too good to be true?"** Then stop.
