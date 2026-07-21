# Issue tracker: GitHub

Issues and planning tickets for this repo live in GitHub Issues. Use `gh` for all operations.

## Conventions

- Create: `gh issue create --title "..." --body "..."`
- Read: `gh issue view <number> --comments`
- List: `gh issue list --state open --json number,title,body,labels,comments`
- Comment: `gh issue comment <number> --body "..."`
- Labels: `gh issue edit <number> --add-label "..."` or `--remove-label "..."`
- Close: `gh issue close <number> --comment "..."`

## Pull requests as a triage surface

No. External pull requests are not treated as feature requests by triage.

## Wayfinding operations

- Map: one issue labelled `wayfinder:map`; child issues use `wayfinder:research`, `wayfinder:prototype`, `wayfinder:grilling`, or `wayfinder:task`.
- Child issues should use GitHub sub-issues when available. Otherwise include `Part of #<map>` in the body.
- Use native GitHub issue dependencies for blocking. If unavailable, use `Blocked by: #<n>` in the body.
- Claim first with `gh issue edit <n> --add-assignee @me`.
- Resolve by commenting the answer, closing the issue, then linking the decision from the map.
