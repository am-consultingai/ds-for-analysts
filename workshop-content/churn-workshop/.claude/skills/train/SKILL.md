---
name: train
description: Step 6 of the ML pipeline, train. Runs scripts/train.py to fit the model listed in ml_spec.yaml (logistic regression) on the training months, and reports churn events per feature and the largest weights. Use for /train or to build the model.
---

# Step 6 · Train

**Start the reply with these two lines:**

```
Skill: /train · Step 6 · Train
Purpose: Find the weights (f) that best link past features to past outcomes.
```

**Before each command, show it on its own line** as `Running: <the exact command>`.

Logistic regression: each feature gets a weight, the weighted sum is the score, and the score becomes a probability between 0 and 1. Training finds the weights that best match past leavers.

## Run

Needs `runs/latest/02_panel.csv`. If it's missing, run `/build-panel` first.

```
.venv/bin/python scripts/train.py --spec ml_spec.yaml --out runs/latest
```

## Report

Read `runs/latest/05_train.md` and report:
1. The rows, churn events and features the model learned from, and the churn events per feature against the rule of thumb (at least 10).
2. The largest weights, in plain words: "more sessions, less likely to leave". A plus pushes toward leaving, a minus toward staying. The weights are on scaled features, so their sizes can be compared.
3. Two cautions, briefly: weights show association, not cause; and features that move together share the credit, so one of a pair can get a surprising sign.

Don't report how good the model is yet. That is `/evaluate`.

## Stop

Ask: **"Do the weights make business sense?"** Then stop.
