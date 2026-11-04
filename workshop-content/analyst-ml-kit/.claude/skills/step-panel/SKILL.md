---
name: step-panel
description: Step 2 of /run-steps. Builds the panel, one row per entity per snapshot, with features from data up to the snapshot and a label from the periods after it, plus the rows to score today. Writes scripts/02_panel.py on the first run. Use when /run-steps reaches the panel, or for /step-panel.
---

# Step 2 · Build the panel

**Start the reply with these two lines:**

```
Skill: /step-panel · Step 2 · Build the panel · Script: projects/<name>/scripts/02_panel.py
Purpose: Turn the history into rows that say what was known on a date, and what happened next.
```

Follow `.claude/skills/run-steps/contract.md` and, on the first run, `checks.md`.

Inputs: the spec, the files in `tables`. Outputs: `runs/02_panel.csv`, `runs/02_latest.csv`, `runs/02_panel.json`, `runs/02_panel.md`.

## Method

### The grid

1. Read each period file; drop duplicate `entity_id` × `time_column` rows, keeping the first (count them). Join the period files on `entity_id` × period (outer join). Convert the time column with `periods()`.
2. The full period range runs from the first to the last period in the data. Every entity gets every period; periods with no row are empty.
3. Never use: `entity_id`, `time_column`, anything in `columns.excluded`.

### The event

For each entity and period, a condition C from `label.event`:

| kind | C at period t |
|---|---|
| `category_value` | `column == value` |
| `reaches_zero` | `column == 0` |
| `above` / `below` | `column > value` / `column < value` |
| `drops_by` | `column < (1 − value) × column at t−1` |

An **event** happens at t when C is true at t, the column is not empty at t−1, and (except for `drops_by`) C was false at t−1.

### Snapshots

- A snapshot s is a period with at least `2 × recent_periods` periods of data before and including it, and the full `horizon_periods` after it.
- Take every `snapshot_every`-th period, counting back from the last snapshot allowed.
- **Label:** 1 if an event happens in s+1 … s+`horizon_periods`. **Event period:** the first such period (kept in the panel as `event_period`, used to count distinct events; never a feature).
- **Eligible rows only**, each drop counted with its reason: the entity has a row at s; `value_above_zero` → `value_column` > 0 at s; `min_tenure_periods` → tenure at s at least that; `exclude_in_event` → C is false at s (not for `drops_by`).

### Features (only periods up to and including s)

R = `defaults.recent_periods`.

| Name | From | Rule |
|---|---|---|
| `<c>` | each number column in the period files | the value at s |
| `<c>_mean` | same | mean of s−R+1 … s, ignoring empty |
| `<c>_trend` | same | (that mean − mean of s−2R+1 … s−R) / (\|earlier mean\| + 1) |
| `<c>_missing` | same | empty periods in s−2R+1 … s |
| `<c>_change` | `value_column` only | (value at s − value at s−R) / (\|value at s−R\| + 1) |
| `<c>_decline_run` | `value_column` only | periods in a row, ending at s and at most `max_run_periods`, where the value fell below the previous period × (1 − `decline_threshold`) |
| `<c>_level`, `<c>_level_mean` | `columns.ordinal` | the level number at s, and its mean over s−R+1 … s; values outside the levels are empty |
| `tenure_periods` | `columns.start_date`, else the entity's first period in the data | periods from it to s |
| `<c>` | `columns.fixed` | as it is |
| `has_<c>` | `columns.presence` | 1 if filled in, else 0 |
| `days_since_<c>` | `columns.dates` | days from the date to the start of period s |
| `<name>` | `extra_features` | `panel.eval(formula)` |

Period-file text columns that aren't in `columns.ordinal` are not used.

### Columns that restate the event or the value

- **Numbers:** any period-file number column (other than `value_column`) whose correlation, over all entity × period cells, with the value column, the value column at t−1, or its change from t−1, is at least `defaults.restate_corr` in size.
- **Text:** any text column with a value present in at least `defaults.restate_share` of event periods.

List them in the `.json` under `restates`, with the reason. They are not dropped by the script.

### Rows to score today

`02_latest.csv`: the same features at the last period in the data, for eligible entities, with no label.

### `.json` and `.md`

`.json`: rows, distinct entities, snapshots (first, last, count), label share, distinct events, `typical_positives_per_snapshot` (median over snapshots of rows with label 1), model columns (after one yes/no per text value), the feature list with the column each came from, `restates`, the row steps.

`.md`: one line with the rows, entities, snapshots and label share; a table of model columns by source file; a short plain description of the snapshot ("one row = one `<row>` on one date: what was known then, and whether `<event>` happened in the next `<h>` `<period>`s"); the row steps table; the feature list with its source.

### Built-in checks

- **No future data:** rebuild the features of the last snapshot from the data cut off after that period. They must equal the panel's rows for that snapshot exactly. If not, exit: "A feature uses data from after its date."
- Rows in = rows kept + rows dropped, by reason.
- `event_period` > snapshot on every row with label 1.

## After the script

1. **Restating columns** (confirm, one at a time): "`<column>` says the same as `<value column or event>` in other words, so the kit won't use it. All right?" On yes, add it to `columns.excluded` (log as `confirmed`) and re-run this step.
2. **`k: auto`**: ask the list-length question from the `size` skill.
3. Report the `.md` summary line and the row steps. Don't list every feature unless asked.
