# Issue tracker: GitHub

Issues and specs for this repo live as GitHub issues on `hubertsangil/snip-sense`. Use the GitHub REST API or `gh` CLI for all operations.

## Repository Details
- **Remote:** `https://github.com/hubertsangil/snip-sense.git`
- **Owner/Repo:** `hubertsangil/snip-sense`
- **Default Branch:** `main`

## Conventions

- **Create an issue**: `gh issue create --title "..." --body "..."` (or via GitHub REST API `POST /repos/hubertsangil/snip-sense/issues`)
- **Read an issue**: `gh issue view <number> --json number,title,body,labels,comments`
- **List issues**: `gh issue list --state open --label ready-for-agent`
- **Apply / remove labels**: `gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- **Close**: `gh issue close <number> --comment "..."`

## Pull requests as a triage surface

**PRs as a request surface: no.**

## When a skill says "publish to the issue tracker"

Create a GitHub issue on `hubertsangil/snip-sense` with label `ready-for-agent`.

## When a skill says "fetch the relevant ticket"

Read the corresponding issue on GitHub or its local markdown mirror in `.scratch/snip-sense/issues/`.
