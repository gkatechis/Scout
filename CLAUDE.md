# Project Instructions

## Issue Tracking

Use `bd` (Dependency-Aware Issue Tracker) for all issue tracking in this project.

**DO NOT use TodoWrite or markdown-based task lists.** Instead, use `bd` commands for:

- Creating issues

- Tracking dependencies between issues

- Viewing ready work

- Updating issue status

### Getting Started with bd

Run `bd quickstart` to see full functionality and command reference.

### Common Commands

```bash
bd create "Issue description"                  # Create new issue
bd list                                         # List all issues
bd ready                                        # Show issues ready to work on
bd update ISSUE_ID --status in_progress        # Update issue status
bd close ISSUE_ID                              # Close completed issue
bd dep add ISSUE_1 ISSUE_2                     # Add dependency

```text

### Integration Notes

- Issues are stored in `.beads/` directory

- Use `bd ready` to find unblocked work

- Dependencies prevent duplicate effort

- Perfect for AI-supervised workflows
