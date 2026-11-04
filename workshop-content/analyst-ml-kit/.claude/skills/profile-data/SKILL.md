---
name: profile-data
description: Describes the project's data files with facts only (tables, keys, time column, period length, value and text columns, date ranges), then asks the analyst to confirm which file is which, the ID column and the time column. Writes scripts/00_profile.py on the first run. Use for /profile-data or when the data folder changes.
---

# Read the data

**Start the reply with these two lines:**

```
Skill: /profile-data · Read the data · Script: projects/<name>/scripts/00_profile.py
Purpose: Know what's in the files before deciding anything.
```

**Before each command, show it on its own line** as `Running: <the exact command>`.

Before writing the script, read `.claude/skills/run-steps/contract.md`. This is the project's first script, so write `common.py` with it.

## Method

**Facts only.** The script and the reply describe the data. They never suggest what could be predicted, and never say what a column "is for".

Inputs: every `.csv` file in `data_folder` from the spec (sorted by name). Read with `read_csv` from `common.py`.

1. **Each file:** rows, columns.
2. **Each column:** its kind, the share of empty cells, the number of distinct values.
   - *number*: numeric after reading; min, median, max, share of zeros.
   - *date*: text where at least 95% of non-empty values parse as dates (`pd.to_datetime(..., errors="coerce")`); first and last date.
   - *text*: anything else; if it has at most `defaults.max_text_values` distinct values, the values and their counts.
   - *identifier*: text or number that is unique on every row of its file.
3. **The ID column:** a column present in every file (same name), with the most distinct values. Report it as the candidate.
4. **Which file is which:**
   - *entities file*: a file where the ID column is unique on every row. At most one.
   - *period files*: files where the ID repeats and a date column exists such that ID × that date is unique on at least 99% of rows. That date column is the candidate **time column** (it must have the same name in all period files).
5. **Period length:** the median gap between consecutive distinct dates of the time column, named as `day` (1), `week` (7), `month` (28–31), `quarter` (89–92) or `year` (365–366). If none fits, report "irregular".
6. **First and last period** in the period files, and the number of distinct periods.
7. **Column handling proposals**, written to the `.json` for the analyst's confirmation:
   - entities-file *identifier* columns other than the ID → `excluded`.
   - entities-file *number* columns → `fixed`.
   - entities-file *text* with at most `max_text_values` values → `fixed` (one yes/no per value, later).
   - entities-file *text* with more values: → `presence` when its fill share is inside `defaults.presence_band`, otherwise `excluded`.
   - entities-file *date* columns → `dates`. The earliest-starting date column whose dates are all on or before each ID's first period is the candidate `start_date` (report it, don't decide).
   - period-file *text* columns with 2 to `max_text_values` values → *possibly ordered*: list them with their values. Claude proposes an order from the value names; the analyst confirms.

Outputs: `runs/00_profile.json` (everything above) and `runs/00_profile.md` (one table of files, then one table of columns per file: column, kind, empty share, distinct values, range or values).

**Built-in checks:** every file has the ID column; at least one period file exists; the time column parses. If no usable time column exists, the script exits with: "No column marks the period of each row. Without one, there's no honest test." This is a stop (§3.2).

**Key numbers** for the independent check: listed in `checks.md`.

## Confirm with the analyst

One at a time, as "I read the data like this. Is that right?":

1. Which file has one row per `<ID>`, and which files have one row per `<ID>` per period. Name the files.
2. The ID column and the time column, and the period length ("one row per `<ID>` per month").
3. For each possibly ordered text column: "`<column>` has the values `<values>`. Do they have an order, from lowest to highest, like this: `<proposed order>`?" If yes, write `columns.ordinal.<column>` as `{level: 0, 1, 2, ...}`. Values outside the order become missing.
4. The start date: "Is `<column>` the date each `<ID>` started?" If none or no, `start_date` stays empty.

Then write to the spec: `entity_id`, `time_column`, `period`, `tables`, `columns`. Log each in `decisions.md`: the confirmed ones as `confirmed`, the column handling as `kit` with the rule as the reason.

Don't ask anything else here. Columns proposed as `excluded`, `fixed` and `presence` are kit decisions: list them in one line each, don't ask.
