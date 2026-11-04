---
name: score
description: Step 8 of the ML pipeline, score. Runs scripts/score.py to score the accounts that can get a trial now with the chosen model (final_model in ml_spec.yaml), and produces this month's 20 trial leads with their chance of buying, ARR and reasons. Use for /score or to see who should get a trial this month.
---

# Step 8 · Score

**Start the reply with these two lines:**

```
Skill: /score · Step 8 · Score
Purpose: Pick this month's trial leads: the accounts most likely to buy after a trial.
```

**Before each command, show it on its own line** as `Running: <the exact command>`.

A new x, the learned f, a predicted y: the accounts that can get a trial now, ranked.

## Check first

1. Read `final_model` in `ml_spec.yaml`. If it is empty, say the model hasn't been chosen yet and run `/evaluate` first.
2. Read `runs/latest/06_eval.json`. If the chosen model doesn't beat today's rule, say the list can't be trusted, and ask whether to go on anyway.

## Run

```
.venv/bin/python scripts/score.py --spec ml_spec.yaml --out runs/latest
```

## Report

Read `runs/latest/08_score.md` and report:
1. Who could get a trial: the month, and the accounts left at each step (pays, tenure, no Audiences licence, never had a trial, never bought).
2. The 20 leads: the expected number of buyers (the sum of their chances).
3. The top 10 rows, with what pushes each account's score up, in plain words.
4. **A tie at the cut, if there is one, word for word**: accounts the model can't tell apart, where only some fit in the leads.
5. Where the full list is: `runs/latest/08_leads.csv`. The first 20 rows are this month's trials.
6. The plan for next month: compare these predictions with what happened, and judge the model over several months, not one.

Add once: a chance of buying after a trial doesn't say whether the trial caused the purchase.

## Stop

Ask: **"Would you give CSMs this list?"** Then stop.
