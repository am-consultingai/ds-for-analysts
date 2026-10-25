---
name: leakage-check
description: Part of step 7, evaluate. Runs scripts/leakage.py to find features that already know the answer: it ranks leavers by each feature alone and lists dates filled in on the day the data was pulled. Use for /leakage-check, when /evaluate warns about a leak, or when a result looks too good.
---

# Step 7 · Leakage check

**Start the reply with these two lines:**

```
Skill: /leakage-check · Step 7 · Leakage check
Purpose: Find features that already know the answer.
```

**Before each command, show it on its own line** as `Running: <the exact command>`.

A leak is a feature, an x, that already contains the answer, y. It makes a model look brilliant on the past and fail on new months.

## Run

```
.venv/bin/python scripts/leakage.py --spec ml_spec.yaml --out runs/latest
```

## Report

Read `runs/latest/07_leakage.md` and report:
1. Today's rule on the training months, as the reference.
2. The features that find the most leavers **on their own**. Anything marked suspect finds far more than any honest signal could.
3. For each suspect: the column it was made from, and the likely story. A date in the one-row-per-account table, such as a last login, is usually taken on the day the data was pulled. For an account that already left, it shows they stopped logging in, which is the answer itself.

## Stop

For each suspect, ask: **"Remove it, keep it, or find out how that column is filled in?"**

On remove:
1. Show the change: add the source column to `excluded_columns` in `ml_spec.yaml`. Apply it after a yes.
2. Re-run from feature engineering to evaluation in one go:
   ```
   .venv/bin/python scripts/pipeline.py --spec ml_spec.yaml --out runs/latest --from build_panel --to evaluate
   ```
3. Report the new evaluation the way `/evaluate` does, next to the numbers from before the fix.

Then stop.
