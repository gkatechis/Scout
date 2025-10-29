# Contributing to Scout

Thank you for your interest in contributing to Scout! This document provides guidelines for contributing to the project.

## Development Setup

1. **Fork and clone the repository**:

   ```bash
   git clone <<<https://github.com/yourusername/Scout.git>>>
   cd Scout

```text

2. **Run the automated setup**:

   ```bash
   ./setup.sh

```text

3. **Activate the virtual environment**:

   ```bash
   source venv/bin/activate

```text

## Code Style

We follow standard Python conventions with automated code formatting and linting.

### Linters and Formatters

The project uses:

- **flake8**: Python linting for code quality and style

- **black**: Code formatting (line length: 127)

- **isort**: Import statement sorting (black-compatible profile)

- **pytest**: Testing framework with coverage reporting

### Running Linters Locally

Before submitting a pull request, run these commands to check your code:

```bash

## Check for Python syntax errors and undefined names

flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics

## Check code style (warnings only)

flake8 src/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

## Format code with black

black src/ tests/

## Sort imports

isort --profile black src/ tests/

```text

### Pre-commit Checks

To verify your changes meet our standards:

```bash

## Run linters

black --check src/ tests/
isort --check-only --profile black src/ tests/
flake8 src/

## Run tests

pytest tests/ -v

```text

## Testing

### Running Tests

Run the full test suite:

```bash
pytest tests/ -v

```text

Run tests with coverage:

```bash
pytest tests/ -v --cov=src --cov-report=term

```text

### Writing Tests

- Add tests for all new functionality

- Tests should be in the `tests/` directory

- Follow existing test patterns

- Aim for high test coverage (>80%)

See [TESTING.md](TESTING.md) for detailed testing documentation.

## Pull Request Process

1. **Create a feature branch**:

   ```bash
   git checkout -b feature/your-feature-name

```text

2. **Make your changes**:

   - Write clear, concise commit messages

   - Follow the code style guidelines

   - Add tests for new functionality

   - Update documentation as needed

3. **Run linters and tests**:

   ```bash
   black src/ tests/
   isort --profile black src/ tests/
   pytest tests/ -v

```text

4. **Commit your changes**:

   ```bash
   git add .
   git commit -m "Brief description of changes"

```text

5. **Push to your fork**:

   ```bash
   git push origin feature/your-feature-name

```text

6. **Open a Pull Request**:

   - Provide a clear description of your changes

   - Reference any related issues

   - Include screenshots/examples if applicable

### PR Requirements

- [ ] All tests pass

- [ ] Code is formatted with black

- [ ] Imports are sorted with isort

- [ ] No flake8 errors

- [ ] Documentation is updated

- [ ] New functionality includes tests

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration. On every push and pull request:

1. **Test Job**: Runs tests on Python 3.10, 3.11, and 3.12
2. **Lint Job**: Checks code style with flake8, black, and isort

You can view CI results in the "Actions" tab of the GitHub repository.

### CI Configuration

The CI pipeline is configured in `.github/workflows/ci.yml` and:

- Runs on push to `master`/`main` branches

- Runs on all pull requests

- Tests across multiple Python versions

- Uploads coverage reports to Codecov

- Continues on linting warnings (won't block PR merges)

## Development Tools

### Debug Logging

Enable debug output for troubleshooting:

```bash

## Verbose output (INFO level)

mcpindexer --verbose <command>

## Debug output (DEBUG level, saves to ~/.mcpindexer/logs/mcpindexer.log)

mcpindexer --debug <command>

```text

### Verification

Test your installation:

```bash
mcpindexer check

```text

## Issue Tracking

For AI agents working on this project, we use [Beads](https://github.com/steveyegge/beads) for issue tracking. See [AGENTS.MD](AGENTS.MD) for details.

## Getting Help

- **Documentation**: See [README.md](README.md), [QUICKSTART.md](QUICKSTART.md), and [docs/CONFIGURATION.md](docs/CONFIGURATION.md)

- **Issues**: Report bugs or request features via GitHub Issues

## Code of Conduct

- Be respectful and inclusive

- Provide constructive feedback

- Focus on what is best for the community

- Show empathy towards other community members

## License

By contributing to Scout, you agree that your contributions will be licensed under the same license as the project.
