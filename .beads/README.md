# Beads Issue Tracking with Git Hooks

This project uses [Beads](https://github.com/steveyegge/beads) for issue tracking with customized git hooks to filter sensitive issues.

## How It Works

- **Local Database**: `.beads/Scout.db` (gitignored) - contains ALL issues
- **Version Control**: `.beads/issues.jsonl` (tracked) - contains only PUBLIC issues
- **Git Hooks**: Automatically filter issues labeled "zendesk" or "internal" before committing

## Git Hooks Installed

### pre-commit
Exports issues to JSONL before each commit, filtering out issues with:
- `zendesk` label
- `internal` label

### post-merge
Imports issues from JSONL after git pull/merge

## Keeping Issues Private

To keep an issue local-only (not pushed to remote):

```bash
# Label the issue as zendesk or internal
bd label add <issue-id> zendesk

# The hook will automatically exclude it from version control
# It stays in your local database but won't be pushed
```

## Viewing All Issues (Including Private)

```bash
# List all issues in local database
bd list

# List only public issues (what's tracked in git)
cat .beads/issues.jsonl | python3 -c "import sys, json; [print(json.loads(line)['id']) for line in sys.stdin]"
```

## Hook Source

Based on: https://github.com/steveyegge/beads/tree/main/examples/git-hooks

Customized to add label-based filtering for private/internal issues.
