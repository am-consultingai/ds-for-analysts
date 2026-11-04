---
name: leakage-check
description: Part of step 7, evaluate. Runs scripts/leakage.py to check that no feature already knows the answer: it scores each model column on its own (AUC) on the training trials, against the spec's threshold. Use for /leakage-check, when a result looks too good, or after adding a feature.
---

# Step 7 · Leakage check

**Start the reply with these two lines:**

```
Skill: /leakage-check · Step 7 · Leakage check
Purpose: Make sure no feature already knows the answer.
```

**Before each command, show it on its own line** as `Running: <the exact command>`.

A leak is a feature, an x, that already contains the answer, y: here, anything known only after the trial started. It makes a model look brilliant on the past and fail on new trials.

## Run

```
.venv/bin/python scripts/leakage.py --spec ml_spec.yaml --out runs/latest
```

## Report

Read `runs/latest/07_leakage.md` and report:
1. The threshold from the spec, in plain words: one column alone with an AUC this high finds buyers far better than any honest signal here.
2. The strongest single columns, what they are made from, and their AUC.
3. The verdict, word for word: "No suspects", or each suspect with the column it was made from.

## Stop

If there are no suspects, ask: **"Is there any feature we couldn't have known before the trial started?"** Then stop.

For each suspect, ask: **"Remove it, keep it, or find out how that column is filled in?"** On remove:
1. Show the change: remove it from `features` in `ml_spec.yaml`. Apply it after a yes.
2. Re-run from feature engineering to evaluation in one go:
   ```
   .venv/bin/python scripts/pipeline.py --spec ml_spec.yaml --out runs/latest --from build_panel --to evaluate
   ```
3. Report the new evaluation the way `/evaluate` does, next to the numbers from before the change.

Then stop.
