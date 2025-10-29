# Troubleshooting Guide

This guide covers common issues and their solutions when using Scout.

## Installation Issues

### Python version conflicts or dependency errors

**Symptoms**:
- "ModuleNotFoundError" when running scout
- "version conflict" errors during installation
- Dependencies fail to install

**Solutions**:

1. **Verify you're using Python 3.10+**:
   ```bash
   python3 --version
   ```

2. **Create a fresh virtual environment with a specific Python version**:
   ```bash
   # Remove old venv if it exists
   rm -rf venv

   # Create new venv with specific Python version
   python3.11 -m venv venv  # or python3.10, python3.12, etc.
   source venv/bin/activate

   # Upgrade pip first
   pip install --upgrade pip setuptools wheel

   # Install dependencies
   pip install -e .
   ```

3. **Still having issues?** Try installing with dev dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

### "ModuleNotFoundError: No module named 'tree_sitter'"

**Solution**: Make sure virtual environment is activated and dependencies are installed

```bash
source venv/bin/activate
pip install -e ".[dev]"
```

## Debug Logging

For troubleshooting issues, you can enable debug logging with the `--debug` or `--verbose` flags:

```bash
# Enable verbose output (INFO level logging)
scout --verbose <command>

# Enable debug output (DEBUG level logging, saves to file)
scout --debug <command>
```

Debug logs are written to: `~/.scout/logs/scout.log`

This is helpful when:
- Investigating indexing failures
- Understanding performance bottlenecks
- Reporting bugs (include log excerpts)

## Indexing Issues

### Slow indexing

**Causes**:
- Large files with many symbols
- Complex nested structures
- First-time embedding generation

**Solutions**:
- Use file filters to skip test/build directories
- Increase chunk size target
- Use GPU-accelerated embeddings (if available)

### Interrupted indexing

**Symptoms**:
- Repository stuck in "indexing" status
- Indexing process was killed or crashed

**Solutions**:
```bash
# Check for stuck repositories
scout status

# Recover automatically
scout recover
```

### Out of memory

**Causes**:
- Indexing too many repos at once
- Very large monoliths

**Solutions**:
- Index repos individually
- Increase system memory
- Use incremental indexing (git commit-based)

## Search Issues

### Poor search results

**Causes**:
- Query too generic
- Code not indexed
- Wrong language filter

**Solutions**:
- Use more specific queries ("JWT token validation" vs "auth")
- Check `list_repos` to verify indexing
- Try without language filter
- Increase `n_results` parameter

### Stale results after code changes

**Solutions**:
```bash
# Force reindex specific repo
python3 -c "
from scout.indexer import MultiRepoIndexer, EmbeddingStore
import os
db_path = os.path.expanduser('~/.scout/db')
store = EmbeddingStore(db_path, 'mcp_code_index')
indexer = MultiRepoIndexer(store)
indexer.repo_indexers['my-repo'].reindex(force=True)
"

# Or use CLI
scout reindex-changed
```

## Git Integration Issues

### Git hooks not triggering

**Causes**:
- Hook not executable
- Hook overwritten
- Virtual environment not activated

**Solutions**:
```bash
# Check hook exists and is executable
ls -la /path/to/repo/.git/hooks/post-merge

# Make executable
chmod +x /path/to/repo/.git/hooks/post-merge

# Test manually
cd /path/to/repo && .git/hooks/post-merge
```

## Getting Help

If you're still experiencing issues:
1. Check debug logs: `~/.scout/logs/scout.log`
2. Run installation check: `scout check`
3. Report issues on GitHub: https://github.com/gkatechis/Scout/issues

Include in your report:
- Output of `scout check`
- Relevant log excerpts
- Steps to reproduce the issue
