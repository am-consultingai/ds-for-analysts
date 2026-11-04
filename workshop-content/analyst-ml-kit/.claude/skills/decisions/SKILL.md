---
name: decisions
description: Shows the project's decision log (what was decided, by whom, and why) and lets the analyst change any of the kit's choices, with the reason it was made. Use for /decisions, or when the analyst asks why something was done or wants something done differently.
---

# Who decided what

**Start the reply with these two lines:**

```
Skill: /decisions · Who decided what
Purpose: See every decision behind the result, and change one if you want.
```

## Show

Read `projects/<name>/decisions.md` and show it as it is, grouped: the analyst's answers, what the analyst confirmed, the kit's choices.

For the kit's defaults (row "Data science defaults"), list the values in `defaults:` of `ml_spec.yaml` only when asked, each with one plain line on what it does, from the comments in `templates/spec.yaml`.

## Change

The analyst can change anything. Never prompt them to.

1. Ask what they want changed and why, in their words.
2. **Translate the wish into the spec yourself.** The analyst says what they want ("use only the last two periods", "don't use that column"); you find the spec field.
3. Show the exact lines, before and after, and what will re-run (the re-run table in `/run-steps`). Wait for a yes.
4. Write the change; add a row to `decisions.md` with **Who** = `analyst` and their reason.
5. Re-run from the step the table names, through to the end.

A change to a kit choice changes only the spec, never a script: the scripts read every value from the spec.

## Refuse

Explain, in one sentence each, and don't make the change:

- A random split: it would judge the list on periods it has already learned from.
- Fitting on the test side before scoring: the judgement would no longer be fair.
- A feature from after its snapshot: it would know the answer.
