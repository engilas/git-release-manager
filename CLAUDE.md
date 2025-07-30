# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GRM (Git Release Manager) is a Python CLI tool for managing Git releases with strict, predefined commit messages and automated changelog updates. It enforces semantic versioning and provides a structured release workflow.

## Development Commands

### Installation and Setup
```bash
# Install in development mode
pip install -e .

# Install with development dependencies
pip install -r requirements-dev.txt
pip install -e .
```

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=grm --cov-report=html

# Run specific test file
pytest tests/test_cli.py -v

# Run specific test
pytest tests/test_cli.py::test_function_name -v
```

### Code Quality
```bash
# Format code
black grm tests

# Lint code
flake8 grm tests

# Type checking
mypy grm

# Run all quality checks
black grm tests && flake8 grm tests && mypy grm
```

### Running the CLI
```bash
# After installation, use the CLI
grm r           # Create release (interactive)
grm r -m        # Create minor release
grm r -p        # Create patch release
grm f           # Finish release
```

## Architecture

### Core Components

- **`cli.py`**: Entry point with Click-based CLI commands (`grm r` and `grm f`)
- **`git_operations.py`**: Git operations wrapper using GitPython
- **`version_manager.py`**: Semantic versioning logic and version parsing
- **`changelog.py`**: CHANGELOG.md manipulation following Keep a Changelog format
- **`utils.py`**: Utility functions for user interaction and colored output

### Release Workflow

1. **Create Release** (`grm r`):
   - Validates preconditions (clean working directory, on main/master branch)
   - Determines next version using semantic versioning
   - Creates `release/<version>` branch
   - Moves unreleased content from CHANGELOG.md to version section
   - Commits with message "Changelog"

2. **Finish Release** (`grm f`):
   - Merges release branch to integration branch (main/master)
   - Creates version tag
   - Merges back to develop branch (if exists)
   - Deletes release branch (local and remote)
   - All merge commits use message "Finish <version>"

### Branch Strategy

- **Integration Branch**: `main` (preferred) or `master` (auto-detected)
- **Development Branch**: `develop` (optional, auto-detected)
- **Release Branches**: `release/<version>` (temporary)

### Key Design Patterns

- **Validation-First**: All operations validate preconditions before execution
- **Interactive Prompts**: User confirmation required for destructive operations
- **Clean Separation**: Each module has single responsibility (Git, versioning, changelog, CLI)
- **Error Handling**: Custom exceptions with user-friendly error messages

### Testing Architecture

- **Fixtures**: Comprehensive pytest fixtures for temporary repos, Git setup, and test data
- **Isolation**: Each test uses temporary directories and repositories
- **Coverage**: Tests cover CLI commands, Git operations, version management, and changelog manipulation
- **Mocking**: Uses pytest-mock for isolating external dependencies

## Dependencies

- **Core**: Click (CLI), GitPython (Git operations), Colorama (colored output)
- **Development**: pytest, pytest-mock, pytest-cov, black, flake8, mypy

## File Structure

```
grm/
├── grm/                    # Main package
│   ├── cli.py             # CLI interface and command handlers
│   ├── git_operations.py  # Git operations wrapper
│   ├── version_manager.py # Semantic versioning logic
│   ├── changelog.py       # CHANGELOG.md manipulation
│   └── utils.py          # Utility functions
├── tests/                 # Test suite
├── integration-test/      # Integration test project
└── setup.py              # Package configuration
```