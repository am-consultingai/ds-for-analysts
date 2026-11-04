---
name: frame
description: The interview. Asks the analyst the business questions one at a time, each with a suggested answer built from their own data, then fills ml_spec.yaml and decisions.md. No script. Use for /frame, after /profile-data, or to change what the project answers.
---

# The business questions

**Start the reply with these two lines:**

```
Skill: /frame · The business questions · Script: none (a conversation that fills ml_spec.yaml)
Purpose: Write down what you want to know ahead of time, and what you'll do with it.
```

Needs `runs/00_profile.json` and the confirmed `entity_id`, `time_column` and `tables` in the spec. If they're missing, run `/profile-data` first.

## How to ask

- **One question at a time**, in plain words, with a suggested answer. Wait for the answer before the next.
- **Business only.** Never mention models, features, metrics, thresholds, splits or sample sizes. Translate each answer into the spec yourself.
- **The analyst's words.** Until the analyst names things, say "one row of `<entities file>`" and use column and file names from the data. Once named, use their words from `terms:`.
- **No examples from any field.** If the analyst asks for an example, show how *their* data could be read, using their files and columns.
- After each answer, show the spec lines it fills, in plain words, and write them after a yes. Add a row to `decisions.md` (`analyst`, with their reason in one line).

## The questions, in order

| # | Ask | Suggested answer | Fills |
|---|---|---|---|
| 1 | "What do you call one row of `<entities file>`? And more than one?" | The ID column's name without `_id`, if it has one | `terms.row`, `terms.rows` |
| 2 | "What will this help decide, and who acts on it?" | None; this one is open | `decision`, `terms.actor` |
| 3 | "Which of these would mean the thing you want to know ahead of time has happened?" Then the **event menu** (below) | None; the analyst picks | `label.event` |
| 4 | "What do you call that?" | The menu item's own words | `terms.event` |
| 5 | Only if the event is on a number column: "Is `<column>` the one that shows how big each `<row>` is?" | Yes | `terms.value_column` |
| 6 | "How far ahead do you need to know, to have time to act?" | 3 `<period>`s | `label.horizon_periods`, and `split.gap_periods` (the same number; a `kit` row: "the test must not overlap the training answers") |
| 7 | "How often would `<actor>` get a new list?" | Every `<period>` | `snapshot_every` |
| 8 | "Which `<rows>` can `<actor>` act on?" | Build it from the data: those with `<value column>` above 0 (if there is one); those at least 3 `<period>`s since `<start date>` (if there is one); not those already `<event>` | `eligibility` |
| 9 | "How many `<rows>` can `<actor>` handle on one list?" | None. If "no limit", write `k: auto`; the panel step will suggest a length | `metric.k` |
| 10 | "How does `<actor>` choose today? Even a rough rule of thumb counts." | None. "Nobody chooses" is a valid answer | `baseline.words`, `baseline.rule`, `baseline.score` |
| 11 | "Out of the `<k>` on each list, how many more real `<event>`s than today's way would make switching worth it?" | `<k>`/10, rounded up (with `k: auto`, ask this after the panel step) | `metric.extra_hits` |
| 12 | The question as one sentence: "Which `<rows>` will `<event>` in the next `<h>` `<period>`s, so `<actor>` can `<decision>`?" Is that it? | The sentence | `question` |

### The event menu

Build it from `00_profile.json`, period files only, one line per item, with the column's values or range so the analyst recognises it:

- a text column takes a value: one line per value, "`<column>` becomes `<value>`"
- a number reaches 0: for number columns with some zeros and mostly values above 0
- a number drops by more than a share from one `<period>` to the next: ask the share; suggested 20%
- a number goes above, or below, a level: ask the level

The event happens in the period it starts: the condition is true that period and wasn't the period before (for "drops by", every period with such a drop counts). Write `label.event` as `{kind, column, value}` with `kind` one of `category_value`, `reaches_zero`, `drops_by`, `above`, `below`.

### Today's rule as an expression

Translate the analyst's words into `baseline.rule` (which rows it flags) and `baseline.score` (how flagged rows are ranked), using the panel column names below. Then read it back in plain words: "So today, `<actor>` looks at `<rows>` whose `<column>` fell `<n>` `<period>`s in a row, biggest fall first. Right?"

Panel column names (made by `/run-steps`, step panel): `<c>` (the latest value), `<c>_mean` (the mean of the last 3 periods), `<c>_trend` (the last 3 against the 3 before), `<c>_missing` (empty periods in the last 6), `<c>_change` and `<c>_decline_run` (value column only), `<c>_level` and `<c>_level_mean` (ordered text), `tenure_periods`, `has_<c>`, `days_since_<c>`, and the entities file's `fixed` columns as they are.

If the rule needs something not in that list, add it under `extra_features` as `{formula, reason: "today's rule"}`, with a pandas expression on the panel columns, and log it as `analyst`. If nobody chooses today, `rule` stays empty: the comparison is then with picking at random.

## Warnings to give, in plain words

- **Chosen rows.** If the analyst says the rows in the data were picked by someone (for example, only the ones a team already chose), warn: the result will describe rows like those picked so far, not all of them.
- **Out of scope.** If the answers show the goal is an amount, a total over time, groups, or what an action changes, say so and stop (see `/ml-pipe-design`).

## Stop

Show the filled spec sections in plain words, one line each. Ask: **"Is this what you want to know, and what you'll do with it?"** Then stop.
