---
name: step-score
description: Step 9 of /run-steps. Refits the model on every labelled row, scores the latest period, and gives the ranked list with the main reasons for each row. Writes scripts/09_score.py on the first run. Use when /run-steps reaches scoring, or for /step-score.
---

# Step 9 · Today's list

**Start the reply with these two lines:**

```
Skill: /step-score · Step 9 · Today's list · Script: projects/<name>/scripts/09_score.py
Purpose: The list `<actor>` would get today, and why each `<row>` is on it.
```

Follow `.claude/skills/run-steps/contract.md` and, on the first run, `checks.md`.

Inputs: the spec, `runs/02_panel.csv`, `runs/02_latest.csv`. Outputs: `runs/09_ranked.csv`, `runs/09_score.json`, `runs/09_score.md`.

## Method

- **Refit** `logistic(spec)` on every labelled row of the panel (training side, gap and test side), with the same columns as step 6 (`features.keep`, or all). This is the only fit allowed to see test rows: judging is over.
- **Score** every row of `02_latest.csv`, its matrix built with `model_matrix` and `align`ed to the refit's columns; rank with `rank_order`.
- **Reasons:** for each row, the `defaults.reasons_per_row` columns adding most to its score (scaled value × weight, largest first, only those adding).
- `09_ranked.csv`: rank, entity ID, chance, `value_column` if there is one, reasons; every scored row.
- `.json`: the period scored, rows scored, rows used for the refit, the top K IDs, the expected `<event>`s in the top K (the sum of their chances).

The `.md`: one line ("`<n>` `<rows>` scored for `<period>`; the top `<k>` are expected to include about `<expected>` `<event>`s in the next `<h>` `<period>`s"), then the top K as a table (rank, ID, chance, value, reasons), then where the full list is.

**Built-in check:** every scored row is eligible under the spec's rules; the number of rows on the list is min(k, rows scored).

## Stop

The list is the one place entity rows are shown. Show the top K table.

Ask: **"Would `<actor>` act on this list?"** Then the final question: **"Go or no-go: use this list in place of today's way?"** Log the answer in `decisions.md` as `analyst`, then run `/report`.
