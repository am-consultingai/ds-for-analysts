---
name: ml-pipe-design
description: The whole flow, start to finish. Checks the environment, creates or resumes a project in projects/<name>/, then runs /profile-data, /frame, /run-steps and /report in order. Use for /ml-pipe-design, or when the analyst wants to start a new question or continue one.
---

# The whole flow

**Start the reply with these two lines:**

```
Skill: /ml-pipe-design · The whole flow
Purpose: Turn your question and your data into a ranked list you can judge, asking you only business questions.
```

**Before each command, show it on its own line** as `Running: <the exact command>`.

## 1. The environment

1. If `.venv` is missing, run `./link-env.sh`. If it ends with an ERROR, show its message and stop.
2. Check the packages:
   ```
   .venv/bin/python -c "import pandas, numpy, sklearn, scipy, statsmodels, joblib, yaml, matplotlib, seaborn; print('OK')"
   ```
   If it fails, name the missing package, say the shared environment needs it, and stop. Never install anything.

## 2. The project

Ask, one at a time:

1. **"What short name should this project have?"** Letters, numbers and dashes. Suggest nothing from any field; if asked, suggest `project-1`.
2. **"Which data should I use?"** Suggested answer: `data/sample/`. Any folder of CSV files inside the kit, or a path the analyst gives.

If `projects/<name>/` already exists, **resume**: read `decisions.md` and `manifest.json`, say in one line where the project stopped, and continue from there.

Otherwise create:

```
projects/<name>/ml_spec.yaml      copy of templates/spec.yaml, with data_folder filled in
projects/<name>/decisions.md      the log (format below)
projects/<name>/scripts/
projects/<name>/checks/
projects/<name>/runs/
```

`decisions.md` starts as:

```
# Decisions

| # | Decision | Value | Who | Why |
|---|---|---|---|---|
| 1 | Data folder | <folder> | analyst | chosen at the start |
| 2 | Data science defaults | templates/spec.yaml `defaults:` | kit | the kit's fixed rules; see /decisions |
```

Every later decision adds one row. **Who** is `analyst` (answered a business question), `confirmed` (the kit read the data, the analyst said yes) or `kit` (a fixed rule). **Why** is one line.

## 3. The rest, in order

Follow each skill's instructions in turn, in work mode: stop only where a skill asks the analyst something or a check fails.

1. `/profile-data`: read the files, confirm which is which.
2. `/frame`: the business questions.
3. `/run-steps`: the steps, including `/size`, with the trust checks on each first run.
4. `/report`: the one-page result.

## Out of scope

If, at any point, the analyst's goal turns out to be predicting an amount, forecasting a total, splitting the rows into groups, or measuring what an action changes, say plainly that this kit answers one kind of question, "which rows will have an event within the next N periods", and stop. Don't force the question into that shape.
