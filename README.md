⚠️ Mostly AI generated

# GRM - Git Release Manager

A Python-based CLI tool for managing Git releases with strict, predefined commit messages and automated changelog updates.

## Features

- **Semantic Versioning**: Automatic detection and management of SemVer tags (MAJOR.MINOR.PATCH)
- **Structured Releases**: Enforced release workflow with predefined commit messages
- **Changelog Management**: Automatic updating of CHANGELOG.md with proper formatting
- **Branch Management**: Automated creation and cleanup of release branches
- **Integration Branch Detection**: Smart detection of main vs master branches
- **Interactive Prompts**: User-guided decision making at each step
- **Comprehensive Testing**: Full test coverage with pytest

## Installation

### From Source

1. Clone the repository:

```bash
git clone https://github.com/your-username/grm.git
cd grm
```

2. Install in development mode:

```bash
pip install -e .
```

### From PyPI (future release)

```bash
pip install grm
```

### Development Installation

For development with all dependencies:

```bash
pip install -r requirements-dev.txt
pip install -e .
```

## Quick Start

After installation, you can start using GRM immediately:

```bash
# Initialize a new repository and create your first release
cd your-git-repo

# Ensure you have a CHANGELOG.md with unreleased content
# GRM will create one if it doesn't exist

# Create a release (interactive mode)
grm r

# Finish the release 
grm f
```

## Usage

GRM supports two main commands:

### 1. Create Release (`grm r`)

Creates a new release branch and updates the changelog.

```bash
# Interactive mode - prompts for version bump type
grm r

# Minor version bump (1.2.3 → 1.3.0)
grm r -m
grm r --minor

# Patch version bump (1.2.3 → 1.2.4)
grm r -p
grm r --patch
```

**What it does:**

1. Checks if you're on the correct branch (develop if it exists, otherwise main/master)
   - If you're on a different branch with no uncommitted changes, offers to switch to develop automatically
   - After switching, pulls the latest changes from the remote (if available)
2. Detects integration branch (main or master)
3. Reads existing SemVer tags to determine current version
4. Suggests next version based on bump type
5. Creates `release/<version>` branch
6. Moves unreleased content from CHANGELOG.md to new version section
7. Commits changelog with message "Changelog"

### 2. Finish Release (`grm f`)

Completes the release process by merging and tagging.

```bash
grm f
```

**What it does:**

1. Merges release branch to integration branch (main/master)
2. Creates tag with version number
3. Merges back to develop branch (if it exists)
4. Deletes release branch (local and remote)
5. All merge commits use message "Finish `<version>`"

## Prerequisites

- Git repository with clean working directory
- Must be on develop to start release
- Must be on release branch to finish release
- CHANGELOG.md file (will create if missing)

## CHANGELOG.md Format

GRM expects a CHANGELOG.md file following the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

### Added
- New feature X
- New feature Y

### Changed
- Updated feature Z

### Fixed
- Bug fix A

## 1.0.0 - 2023-12-01

### Added
- Initial release
```

## Workflow Example

1. **Start a release:**

```bash
$ grm r
Last version: 1.1.1
Choose bump type:
  [m]inor → 1.2.0
  [p]atch → 1.1.2
Enter m or p [M/p]: 
Create release 1.2.0? [Y/n]: y
✓ Created release branch 'release/1.2.0'
✓ Updated CHANGELOG.md
✓ Committed changes with message "Changelog"
```

2. **Review changes and finish:**

```bash
$ grm f
Current release branch: release/1.2.0
Target version: 1.2.0
Finish release 1.2.0? [Y/n]: y
✓ Merged to main branch
✓ Created tag v1.2.0
✓ Merged back to develop (if exists)
✓ Deleted release branch
Release 1.2.0 finished successfully!
```

## Branch Strategy

GRM works with the following branch strategy:

- **Integration Branch**: `main` (preferred) or `master`
- **Development Branch**: `develop` (optional)
- **Release Branches**: `release/<version>`

## Error Handling

GRM performs comprehensive validation:

- ✅ Clean working directory
- ✅ Correct branch for operation
- ✅ Valid CHANGELOG.md format
- ✅ Existing unreleased content
- ✅ Valid semantic versioning

Common error scenarios:

- Uncommitted changes → Commit or stash first
- Wrong branch (with changes) → Switch to correct branch manually
- Wrong branch (without changes) → Offers to switch automatically
- Missing changelog → Will prompt to create
- No unreleased content → Will warn but can continue

## Configuration

No configuration files needed. GRM works out of the box with sensible defaults.

## Testing

Run the full test suite:

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run with coverage
pytest --cov=grm --cov-report=html

# Run specific test file
pytest tests/test_cli.py -v
```

## Development

### Project Structure

```
grm/
├── grm/                   # Main package
│   ├── __init__.py       # Package initialization and metadata
│   ├── cli.py            # CLI interface and command handlers
│   ├── git_operations.py # Git operations wrapper
│   ├── version_manager.py # Semantic versioning logic
│   ├── changelog.py      # CHANGELOG.md manipulation
│   └── utils.py          # Utility functions
├── tests/                # Comprehensive test suite
│   ├── conftest.py       # Pytest fixtures
│   ├── test_cli.py       # CLI command tests
│   ├── test_changelog.py # Changelog tests
│   ├── test_git_operations.py # Git operations tests
│   └── test_version_manager.py # Version management tests
├── integration-test/     # Integration test project
├── setup.py             # Package setup and dependencies
├── requirements.txt     # Core dependencies
├── requirements-dev.txt # Development dependencies
└── CLAUDE.md           # AI assistant instructions
```

### Code Quality

The project uses:

- **Black** for code formatting
- **Flake8** for linting
- **MyPy** for type checking
- **Pytest** for testing

Run quality checks:

```bash
# Format code
black grm tests

# Lint code  
flake8 grm tests

# Type checking
mypy grm

# Run tests with coverage
pytest --cov=grm --cov-report=html

# Run all quality checks at once
black grm tests && flake8 grm tests && mypy grm
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and add tests
4. Run quality checks: `black grm tests && flake8 grm tests && mypy grm && pytest`
5. Commit changes: `git commit -m "Add feature"`
6. Push to branch: `git push origin feature-name`
7. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and changes.
