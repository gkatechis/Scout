# Testing Guide

## Testing Installation on Clean Environment

### Option 1: Using Docker (Recommended)

Create a `Dockerfile` for testing:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install git (required for GitPython)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Run setup
RUN chmod +x setup.sh
RUN ./setup.sh

# Test installation
CMD ["python3", "-m", "scout", "check"]
```

Build and run:
```bash
docker build -t scout-test .
docker run scout-test
```

### Option 2: Using Python venv

Test in an isolated virtual environment:

```bash
# Clone to a fresh directory
cd /tmp
git clone https://github.com/yourusername/mcpIndexer.git
cd mcpIndexer

# Run setup script
./setup.sh

# Activate virtual environment
source venv/bin/activate

# Test CLI commands
python3 -m scout check
python3 -m scout --help
```

### Option 3: Using pip install

Test installation via pip:

```bash
# In a fresh virtual environment
python3 -m venv test_env
source test_env/bin/activate

# Install from local directory
pip install -e /path/to/mcpIndexer

# Test imports
python3 -c "from scout.indexer import MultiRepoIndexer; print('OK')"

# Test CLI
python3 -m scout check
```

## Pre-Release Checklist

Before releasing to GitHub, verify:

- [ ] No hardcoded paths in source code
- [ ] No organization-specific references
- [ ] `.gitignore` excludes all local data
- [ ] `.mcp.json` is not tracked (only `.mcp.json.example`)
- [ ] README has generic setup instructions
- [ ] LICENSE file exists
- [ ] `requirements.txt` is complete
- [ ] `pyproject.toml` is configured correctly
- [ ] Setup script works on clean environment
- [ ] Documentation is complete

## Unit Tests

Run the test suite:

```bash
# After setup.sh or pip install -e ., simply run:
pytest tests/ -v

# No PYTHONPATH export needed! pytest is configured in pyproject.toml

# With coverage
pytest tests/ --cov=scout --cov-report=html

# Specific test file
pytest tests/test_embeddings.py -v
```

## Manual Testing Checklist

### 1. Installation
- [ ] Setup script completes without errors
- [ ] Virtual environment is created
- [ ] Dependencies install successfully
- [ ] Configuration files are created

### 2. Indexing
- [ ] Can index a small repository
- [ ] Can index multiple repositories
- [ ] Progress updates work
- [ ] Error handling works for invalid paths

### 3. Search
- [ ] Semantic search returns relevant results
- [ ] Symbol search works
- [ ] Language filtering works
- [ ] Cross-repo dependencies detected

### 4. MCP Integration
- [ ] MCP server starts without errors
- [ ] All 13 tools are available
- [ ] Tools return proper results
- [ ] Error messages are clear

### 5. CLI Commands
- [ ] `python3 -m scout status` works
- [ ] `python3 -m scout check-updates` works
- [ ] `python3 -m scout reindex-changed` works

## Performance Testing

Test with different repository sizes:

### Small Repo (< 100 files)
Expected: < 5 seconds to index

### Medium Repo (100-1000 files)
Expected: < 30 seconds to index

### Large Repo (1000+ files)
Expected: < 2 minutes to index

## Compatibility Testing

Test on different platforms:

- [ ] macOS (arm64)
- [ ] macOS (x86_64)
- [ ] Linux (Ubuntu 20.04+)
- [ ] Linux (other distros)
- [ ] Windows (WSL)

Test with different Python versions:

- [ ] Python 3.10
- [ ] Python 3.11
- [ ] Python 3.12

## Common Issues to Test

1. **Missing dependencies**: Verify clear error messages
2. **Invalid paths**: Verify graceful error handling
3. **No git repository**: Verify indexing still works
4. **Large files**: Verify chunking doesn't hang
5. **Binary files**: Verify they're skipped properly
6. **Symlinks**: Verify they're handled correctly

## Reporting Test Results

When reporting test results, include:

1. Platform (OS, architecture)
2. Python version
3. Installation method used
4. Test results (pass/fail for each item)
5. Any errors or warnings encountered
6. Performance metrics (indexing speed, search latency)

## Continuous Testing

After initial release, set up:

1. GitHub Actions for automated testing
2. Pre-commit hooks for code quality
3. Regular compatibility checks
4. Performance benchmarks
