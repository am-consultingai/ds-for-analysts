---
name: evaluate
description: Step 7 of the ML pipeline, evaluate. Runs scripts/baseline.py and scripts/evaluate.py to compare every trained model with today's rule on the same test months: training AUC (memory) against test AUC (skill), buyers in picks and sales per month, with warnings and the spec's suggested model. The analyst chooses the final model. Use for /evaluate or to judge and choose a model.
---

# Step 7 · Evaluate

**Start the reply with these two lines:**

```
Skill: /evaluate · Step 7 · Evaluate
Purpose: Memory or skill: which model beats today's rule on months it has never seen?
```

**Before each command, show it on its own line** as `Running: <the exact command>`.

## Run

Needs trained models in `runs/latest/05_models/`. If they're missing, run `/train` first.

```
.venv/bin/python scripts/baseline.py --spec ml_spec.yaml --out runs/latest
.venv/bin/python scripts/evaluate.py --spec ml_spec.yaml --out runs/latest
```

## Report

Read `runs/latest/06_eval.md` and report:
1. **The table**, against today's rule: for each model, training AUC (**memory**: how well it knows the trials it learned from) and test AUC (**skill**: how well it does on months it has never seen), the gap, buyers in picks and sales per month. Translate one line into plain words: "about 10 sales a month from 20 leads, against 6 with today's rule".
2. **The model picked by training score**, as the warning: perfect on the past, the worst on new months. Never pick a model by its training score.
3. The buyers in each test month's picks. Point out any month where every model fails: one month swings a lot.
4. **Every warning, word for word.** Don't soften them.
5. **The suggested model** and why: among the models whose check score (from `/train`) is close to the best, the simplest. Say that the test months were not used to choose it: they only confirm it.

Don't use accuracy.

## Stop

Ask: **"Which model do we use? The suggestion is the simplest one that scores close to the best."** On the answer, show the change (`final_model: <tree | logistic | forest | xgboost>` in `ml_spec.yaml`), apply it after a yes, then stop.
