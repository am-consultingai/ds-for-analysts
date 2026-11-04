---
name: step-audit
description: Step 1 of /run-steps. Finds problems in the raw files before any modelling, as counts only. Writes scripts/01_audit.py on the first run. Use when /run-steps reaches the audit, or for /step-audit.
---

# Step 1 · Check the data

**Start the reply with these two lines:**

```
Skill: /step-audit · Step 1 · Check the data · Script: projects/<name>/scripts/01_audit.py
Purpose: Find the problems in the data before they find you.
```

Follow `.claude/skills/run-steps/contract.md` and, on the first run, `checks.md`.

Inputs: the files in `tables` from the spec. Outputs: `runs/01_audit.json`, `runs/01_audit.md`.

## Method

For each file, report counts only, never rows:

| Check | Rule |
|---|---|
| Size | Rows, columns; first and last period (period files) |
| Text read as missing | Text columns where any of `defaults.missing_words` appears as a value. Report the count; the kit already reads them as text |
| Duplicates | Period files: rows with the same `entity_id` × `time_column`. The panel step keeps the first; report how many |
| Rows after the event | Only for `reaches_zero` events: rows where the event column stays at 0 after an earlier event period, per file and in distinct entities |
| Window edge | Share of entities whose first period is the data's first period. Above `defaults.edge_share`, report: "they existed before the data begins, so they look new" |
| Many missing | Columns at least `defaults.many_missing` empty, with the share |
| Unknown IDs | Period-file IDs missing from the entities file, and the reverse |

The `.md` is one table of files, then one table of findings: check, file · column, count, what it means in one plain sentence.

**Built-in check:** the time column parses as dates on every row of every period file. If not, exit with: "Some rows have no readable period, so they can't be placed in time." This is a stop.

## Report

Quote the two tables. Say what the kit does about each finding (duplicates: keeps the first; rows after the event: eligibility drops them; window edge: tenure is counted from the start date if there is one). Don't stop unless the built-in check failed.
