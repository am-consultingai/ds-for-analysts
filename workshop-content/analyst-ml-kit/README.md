# Analyst ML kit

Bring a question and a folder of CSV files. The kit asks you the business questions, makes the data science decisions itself, writes and checks the code, and gives you a ranked list and a one-page report.

## Start

You need the shared Python environment from the setup command (`~/.venvs/ds-workshop`). Then, in this folder:

```bash
./link-env.sh
claude
```

In Claude, type:

```
/ml-pipe-design
```

It asks for a project name and which data to use, then walks you through the rest.

## What you'll be asked

Only business questions, one at a time, each with a suggested answer: what the result is for and who acts on it, how many cases fit on one list, how often, what counts as the event, how far ahead you need to know, who can be acted on, today's rule, how much better than today's rule it must be, when certain values are filled in, and finally go or no-go.

You'll never be asked about models, statistics or settings. Every choice the kit makes is logged with its reason; type `/decisions` to see them.

## Commands

| Command | What it does |
|---|---|
| `/ml-pipe-design` | The whole flow, start to finish |
| `/profile-data` | Describe the data files again |
| `/frame` | Answer the business questions again |
| `/size` | Check whether there's enough history to judge the result |
| `/run-steps` | Run the steps again after a change |
| `/decisions` | Who decided what, and why; change a kit choice |
| `/report` | Rebuild the one-page report |

## What's here

| | |
|---|---|
| `CLAUDE.md` | How Claude works in this kit |
| `.claude/skills/` | The method for each step, in words |
| `templates/spec.yaml` | The empty spec each project starts from |
| `data/sample/` | Sample data to try the kit on |
| `projects/` | One folder per question, created when you start |
