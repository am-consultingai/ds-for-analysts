---
name: score
description: Step 8 of the ML pipeline, score. Runs scripts/score.py to score this month's accounts with the model, and produces the ranked list for the CSMs with chance of leaving, ARR and ARR at risk. Use for /score or to see who to call this month.
---

# Step 8 · Score

**Start the reply with these two lines:**

```
Skill: /score · Step 8 · Score
Purpose: Rank this month's accounts by their chance of leaving.
```

**Before each command, show it on its own line** as `Running: <the exact command>`.

A new x, the learned f, a predicted y: this month's accounts, ranked.

## Check first

Read `runs/latest/06_eval.json`. If it has warnings, or the model doesn't beat today's rule, say the list can't be trusted yet, and ask whether to go on anyway.

## Run

```
.venv/bin/python scripts/score.py --spec ml_spec.yaml --out runs/latest
```

## Report

Read `runs/latest/08_score.md` and report:
1. The month scored and how many accounts.
2. The top 50: the expected number of leavers, and the ARR at risk (chance of leaving × ARR) against the ARR on the list.
3. The top 10 rows, with the features that push each account's score up most, in plain words.
4. Where the full list is: `runs/latest/08_ranked.csv`. The first 50 rows are this month's calls.

Add once: a chance of leaving shows risk, not whether a call will save the account.

## Stop

Ask: **"Would you act on this list?"** Then stop.
