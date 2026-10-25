---
name: frame
description: Step 1 of the ML pipeline, define the question. Reviews or writes the question, target, decision and K in ml_spec.yaml. Use for /frame, when starting a new project, or to change what is predicted.
---

# Step 1 · Define the question

**Start the reply with these two lines:**

```
Skill: /frame · Step 1 · Define the question · Script: none (this step is a conversation about ml_spec.yaml)
Purpose: Write down what we predict, and for which decision.
```

## On this project

`ml_spec.yaml` is already filled in for churn. Go through its first section one item at a time, in plain words, and ask about each:

| Spec field | Ask |
|---|---|
| `question` | Is this the question? |
| `decision` | Who acts on the list, how, and how often? |
| `value_column` + `label` | Churn = ARR drops from above 0 to 0 within `horizon_months`. Does that match how the business counts churn? |
| `eligibility` | Which accounts are scored? (Active, at least `min_tenure_months` of tenure.) |
| `metric.k` | How many accounts can the CSMs call each month? |

## On a new project

Ask for the same five items, then write a new `ml_spec.yaml` using this one as the template. Fill in only the answers given. Mark anything unknown with `# TODO: ask` instead of guessing.

## Rules

- Change the spec only after a yes to the exact change. Show the lines before and after.
- A change to K or to the target means every later step must run again.

## Stop

Ask: **"Will anyone act on this answer, and is the target defined the way the business counts it?"** Then stop.
