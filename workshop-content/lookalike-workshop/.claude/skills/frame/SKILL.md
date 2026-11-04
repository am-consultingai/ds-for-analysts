---
name: frame
description: Step 1 of the ML pipeline, define the question. Reviews or writes the question, target, decision, eligibility and the measures in ml_spec.yaml. Use for /frame, when starting a new project, or to change what is predicted.
---

# Step 1 · Define the question

**Start the reply with these two lines:**

```
Skill: /frame · Step 1 · Define the question · Script: none (this step is a conversation about ml_spec.yaml)
Purpose: Write down what we predict, and for which decision.
```

## On this project

`ml_spec.yaml` is already filled in for the look-alike question. Go through its first section one item at a time, in plain words, and ask about each:

| Spec field | Ask |
|---|---|
| `question` | Is this the question? |
| `decision` | Who acts on the list, how, and how often? (CSMs start trials with 20 accounts on the 1st of each month.) |
| `label` | The target is `converted` = Yes in the trials table: the account bought after its 30-day trial. Does that match how the business counts a sale? |
| `eligibility` | Who can get a trial? (Pays, at least `min_tenure_months` of tenure, no Audiences licence, never had a trial, never bought.) |
| `metric` | `leads`: how many trials can the CSMs start each month? |

Say once, in two sentences: we only know the outcome for accounts that had a trial. So to compare methods on past months, each one picks its top `k` (8) of the 20 trialed accounts that month, and we count how many bought; the business itself gets `leads` (20) leads a month.

## On a new project

Ask for the same five items, then write a new `ml_spec.yaml` using this one as the template. Fill in only the answers given. Mark anything unknown with `# TODO: ask` instead of guessing.

## Rules

- Change the spec only after a yes to the exact change. Show the lines before and after.
- A change to the target, the eligibility or the measures means every later step must run again.

## Stop

Ask: **"Will anyone act on this answer, and is the target defined the way the business counts it?"** Then stop.
