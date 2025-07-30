"""Pytest configuration and shared fixtures."""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Generator

import pytest
import git
from git import Repo

from grm.git_operations import GitManager
from grm.changelog import ChangelogManager


@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()

    try:
        os.chdir(temp_dir)
        yield temp_dir
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def git_repo(temp_dir: str) -> Generator[Repo, None, None]:
    """Create a temporary Git repository."""
    repo = Repo.init(temp_dir)

    # Configure user for commits
    with repo.config_writer() as config:
        config.set_value("user", "name", "Test User")
        config.set_value("user", "email", "test@example.com")

    # Create initial commit
    readme_path = os.path.join(temp_dir, "README.md")
    with open(readme_path, "w") as f:
        f.write("# Test Repository\n")

    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")

    yield repo


@pytest.fixture
def git_manager(git_repo: Repo) -> GitManager:
    """Create a GitManager instance with a test repository."""
    return GitManager(git_repo.working_dir)


@pytest.fixture
def changelog_manager(temp_dir: str) -> ChangelogManager:
    """Create a ChangelogManager instance."""
    return ChangelogManager(os.path.join(temp_dir, "CHANGELOG.md"))


@pytest.fixture
def sample_changelog_content() -> str:
    """Sample changelog content for testing."""
    return """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added
- New feature X
- New feature Y

### Fixed
- Bug fix Z

## 1.0.0 - 2023-12-01

### Added
- Initial release
"""


@pytest.fixture
def repo_with_tags(git_manager: GitManager) -> GitManager:
    """Create a repository with sample tags."""
    # Create some commits and tags
    repo = git_manager.repo

    # Create and tag version 1.0.0
    test_file = os.path.join(repo.working_dir, "test.txt")
    with open(test_file, "w") as f:
        f.write("Version 1.0.0\n")
    repo.index.add(["test.txt"])
    repo.index.commit("Add test file for 1.0.0")
    repo.create_tag("1.0.0")

    # Create and tag version 1.1.0
    with open(test_file, "a") as f:
        f.write("Version 1.1.0\n")
    repo.index.add(["test.txt"])
    repo.index.commit("Update for 1.1.0")
    repo.create_tag("1.1.0")

    # Create and tag version 1.1.1
    with open(test_file, "a") as f:
        f.write("Version 1.1.1\n")
    repo.index.add(["test.txt"])
    repo.index.commit("Update for 1.1.1")
    repo.create_tag("1.1.1")

    return git_manager


@pytest.fixture
def repo_with_develop_branch(git_manager: GitManager) -> GitManager:
    """Create a repository with main and develop branches."""
    repo = git_manager.repo

    # Create develop branch
    develop_branch = repo.create_head("develop")
    develop_branch.checkout()

    # Make a commit on develop
    test_file = os.path.join(repo.working_dir, "develop.txt")
    with open(test_file, "w") as f:
        f.write("Development work\n")
    repo.index.add(["develop.txt"])
    repo.index.commit("Development commit")

    # Switch back to main
    repo.heads.main.checkout()

    return git_manager
