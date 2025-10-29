# AI Agent Instructions for Scout

This file contains instructions for AI coding agents working on the Scout project.

## Task Management with Beads

This project uses **Beads** for issue tracking and task management when working with AI coding agents. Beads is a sophisticated issue tracking system designed specifically for AI agents to manage complex, long-horizon tasks.

### Why Beads?

- **Memory for AI agents**: Track tasks across multiple sessions
- **Dependency management**: Handle blocking relationships and hierarchical tasks
- **Git-integrated**: All issues are version-controlled and shareable
- **Automatic work detection**: Find what's ready to work on next

### First-Time Setup

If Beads is not yet installed or initialized for this project, complete these steps:

#### 1. Install Beads

Choose one installation method:

```bash
# Option 1: Homebrew (macOS/Linux)
brew tap steveyegge/beads && brew install bd

# Option 2: Quick install script
curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/main/install.sh | bash

# Option 3: Go install
go install github.com/steveyegge/beads/cmd/bd@latest
```

#### 2. Initialize Beads in this project

```bash
cd /path/to/Scout
bd init
```

This creates a `.beads/` directory and `beads.db` file for tracking issues.

#### 3. Verify installation

```bash
bd list
```

Should show an empty list or existing issues.

### Core Workflow for AI Agents

When starting work on this project, follow this workflow:

#### 1. Check for ready work

```bash
bd ready
```

This shows issues that are ready to work on (not blocked by dependencies).

#### 2. Create new issues as needed

```bash
# Create a new task
bd create "Add support for Java language parsing"

# Create with description
bd create "Fix memory leak in indexer" --description "ChromaDB connections not being closed properly"

# Create with priority
bd create "Urgent: Fix broken tests" --priority high
```

#### 3. Link related issues

```bash
# Issue A blocks issue B (B cannot start until A is done)
bd link --blocks <issue-A-id> <issue-B-id>

# Issue B is a child of issue A (hierarchical relationship)
bd link --parent <issue-A-id> <issue-B-id>

# Issue A is related to issue B (informational)
bd link --related <issue-A-id> <issue-B-id>
```

#### 4. Update issue status

```bash
# Mark issue as in progress
bd start <issue-id>

# Mark issue as complete
bd close <issue-id>

# Add notes/comments
bd comment <issue-id> "Fixed by implementing TreeSitter Java grammar"
```

#### 5. View project status

```bash
# List all issues
bd list

# Show specific issue details
bd show <issue-id>

# View dependency graph
bd graph
```

### Best Practices for AI Agents

1. **Start every session by checking ready work**: Run `bd ready` to see what tasks are available
2. **Break down large tasks**: Create parent-child relationships for complex features
3. **Track blockers explicitly**: Use `--blocks` links to prevent premature work
4. **Close issues when done**: Mark completed work to unblock dependent tasks
5. **Document decisions**: Use `bd comment` to record why certain approaches were chosen
6. **Commit Beads database**: The `.beads/` directory and `beads.db` should be committed to git
7. **Always prompt for private labels**: When creating new issues, use AskUserQuestion to determine if the issue should be labeled as private (see Private Issue Labeling below)

### Private Issue Labeling

This project uses git hooks to filter private issues from version control. **Always prompt the user** when creating new issues to determine if they should be kept private.

**When to prompt:**
- Creating any new issue with `bd create`
- When issue content mentions: Zendesk, internal projects, proprietary systems, private repositories

**How to prompt:**
Use AskUserQuestion with:
- Question: "Should this issue be kept private (local-only)?"
- Options:
  - "Public" - Issue will be pushed to remote repository
  - "Private (Zendesk)" - Label with `zendesk` (filtered from git)
  - "Private (Internal)" - Label with `internal` (filtered from git)

**After creating the issue:**
```bash
# If user selected private, apply the label:
bd label add <issue-id> zendesk
# or
bd label add <issue-id> internal
```

The pre-commit hook automatically filters labeled issues from `.beads/issues.jsonl` before pushing to remote.

### Common Beads Commands Reference

```bash
bd create <title>                    # Create new issue
bd list                              # List all issues
bd ready                             # Show ready-to-work issues
bd show <id>                         # Show issue details
bd start <id>                        # Mark as in progress
bd close <id>                        # Mark as completed
bd comment <id> <message>            # Add comment
bd link --blocks <blocker> <blocked> # Add blocking dependency
bd link --parent <parent> <child>    # Add parent-child relationship
bd graph                             # View dependency graph
bd search <query>                    # Search issues
bd edit <id>                         # Edit issue details
```

### Integration with Development Workflow

#### When starting a new feature:

1. Create a parent issue for the feature
2. Create child issues for implementation steps
3. Link blockers where necessary
4. Work through `bd ready` items sequentially

#### When fixing bugs:

1. Create issue describing the bug
2. Link to any related feature issues
3. Start work with `bd start <id>`
4. Close when fixed and tested

#### When blocked:

1. Document the blocker with `bd comment`
2. Create a new issue for the blocking task
3. Link with `--blocks` relationship
4. Move to next ready item from `bd ready`

## Project-Specific Guidelines

### Code Style

- Follow PEP 8 for Python code
- Use type hints for all function signatures
- Document classes and complex functions with docstrings

### Testing

- Run tests before closing issues: `python3 -m pytest tests/ -v`
- Add tests for new features
- Update integration tests when changing core functionality

### Indexing

- Use incremental indexing when possible
- Test with small repos before large ones
- Verify cross-repo dependencies after changes

### MCP Integration

- Test MCP tools after server changes
- Verify `.mcp.json` configuration stays valid
- Document new MCP tools in README

## Getting Help

- **Beads documentation**: https://github.com/steveyegge/beads
- **Scout issues**: Check `bd list` for current project issues
- **Project README**: See README.md for installation and usage

## For Human Developers

If you're a human reading this: This file is primarily for AI coding agents, but you're welcome to use Beads too! It's an excellent way to track project work and collaborate with AI assistants. Just make sure to:

1. Install Beads (see instructions above)
2. Run `bd ready` to see what needs work
3. Update issue statuses as you work
4. Commit the Beads database to share progress

The AI agents following these instructions will maintain the issue database and help drive the project forward systematically.
