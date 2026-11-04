---
name: train
description: Step 6 of the ML pipeline, train. Runs scripts/train.py: each model in ml_spec.yaml (decision tree, logistic regression, random forest, XGBoost) tries a few settings and keeps the one with the best check score on later training months. Reports buyers per feature, the chosen settings, logistic regression's weights and the tree's groups. Use for /train or to build the models.
---

# Step 6 · Train

**Start the reply with these two lines:**

```
Skill: /train · Step 6 · Train
Purpose: Try four models, a few settings each, and keep the best setting of each.
```

**Before each command, show it on its own line** as `Running: <the exact command>`.

## Run

Needs `runs/latest/02_panel.csv`. If it's missing, run `/build-panel` first. This step takes a minute or two.

```
.venv/bin/python scripts/train.py --spec ml_spec.yaml --out runs/latest
```

## Report

Read `runs/latest/05_train.md` and report:
1. The trials, buyers and model columns the models learned from, and the buyers per model column against the rule of thumb (at least 10). If it is below, say what it means: the models may memorise, and `/evaluate` will show it.
2. **How each setting was judged**, in one sentence: it was fitted on earlier training months and checked on a later one, the same way the data is split. The check score is an AUC.
3. The table: each model, how many settings it tried, the best setting and its check score.
4. The warning example kept for `/evaluate`: the setting with the best **training** score.
5. Logistic regression's largest weights, in plain words: "higher Analytics level, more likely to buy". A plus pushes toward buying, a minus away from it.
6. The decision tree's groups: for each, the conditions, how many training trials and how often they bought.
7. Two cautions, briefly: weights show association, not cause; and features that move together share the credit, so one of a pair can get a surprising sign.

Don't report how good the models are yet. That is `/evaluate`.

## Stop

Ask: **"Enough buyers per feature? Do the weights and the tree's groups make business sense?"** Then stop.
