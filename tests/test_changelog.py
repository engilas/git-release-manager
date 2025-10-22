"""Tests for changelog module."""

import os
import pytest
from datetime import datetime

from grm.changelog import ChangelogManager, ChangelogError


class TestChangelogManager:
    """Test cases for ChangelogManager class."""

    def test_changelog_exists_false(self, changelog_manager: ChangelogManager):
        """Test changelog_exists when file doesn't exist."""
        assert changelog_manager.changelog_exists() is False

    def test_changelog_exists_true(
        self, changelog_manager: ChangelogManager, temp_dir: str
    ):
        """Test changelog_exists when file exists."""
        # Create changelog file
        with open(changelog_manager.changelog_path, "w") as f:
            f.write("# Changelog\n")

        assert changelog_manager.changelog_exists() is True

    def test_create_initial_changelog(self, changelog_manager: ChangelogManager):
        """Test creating initial changelog file."""
        changelog_manager.create_initial_changelog()

        assert changelog_manager.changelog_exists() is True
        content = changelog_manager.read_changelog()
        assert "# Changelog" in content
        assert "## Unreleased" in content
        assert "Keep a Changelog" in content

    def test_read_changelog_success(
        self, changelog_manager: ChangelogManager, sample_changelog_content: str
    ):
        """Test reading changelog file successfully."""
        # Create changelog file
        with open(changelog_manager.changelog_path, "w") as f:
            f.write(sample_changelog_content)

        content = changelog_manager.read_changelog()
        assert content == sample_changelog_content

    def test_read_changelog_not_found(self, changelog_manager: ChangelogManager):
        """Test reading non-existent changelog file."""
        with pytest.raises(ChangelogError, match="not found"):
            changelog_manager.read_changelog()

    def test_write_changelog(self, changelog_manager: ChangelogManager):
        """Test writing changelog file."""
        content = "# Test Changelog\n"
        changelog_manager.write_changelog(content)

        assert changelog_manager.changelog_exists() is True
        read_content = changelog_manager.read_changelog()
        assert read_content == content

    def test_extract_unreleased_content(
        self, changelog_manager: ChangelogManager, sample_changelog_content: str
    ):
        """Test extracting unreleased content."""
        changelog_manager.write_changelog(sample_changelog_content)

        unreleased = changelog_manager.extract_unreleased_content()

        assert "### Added" in unreleased
        assert "- New feature X" in unreleased
        assert "- New feature Y" in unreleased
        assert "### Fixed" in unreleased
        assert "- Bug fix Z" in unreleased

        # Should not contain version sections
        assert "## 1.0.0" not in unreleased
        assert "Initial release" not in unreleased

    def test_extract_unreleased_content_empty(
        self, changelog_manager: ChangelogManager
    ):
        """Test extracting unreleased content when empty."""
        content = """# Changelog

## Unreleased

## 1.0.0 - 2023-12-01

### Added
- Initial release
"""
        changelog_manager.write_changelog(content)

        unreleased = changelog_manager.extract_unreleased_content()
        assert unreleased == []

    def test_extract_unreleased_content_no_section(
        self, changelog_manager: ChangelogManager
    ):
        """Test extracting unreleased content when section doesn't exist."""
        content = """# Changelog

## 1.0.0 - 2023-12-01

### Added
- Initial release
"""
        changelog_manager.write_changelog(content)

        with pytest.raises(ChangelogError, match="Unreleased.*not found"):
            changelog_manager.extract_unreleased_content()

    def test_move_unreleased_to_version(
        self, changelog_manager: ChangelogManager, sample_changelog_content: str
    ):
        """Test moving unreleased content to version section."""
        changelog_manager.write_changelog(sample_changelog_content)

        changelog_manager.move_unreleased_to_version("1.2.0", "2024-01-15")

        updated_content = changelog_manager.read_changelog()

        # Check that new version section was created
        assert "## 1.2.0 - 2024-01-15" in updated_content

        # Check that unreleased content was moved
        lines = updated_content.split("\n")
        unreleased_idx = next(
            i for i, line in enumerate(lines) if line.strip() == "## Unreleased"
        )
        version_idx = next(
            i for i, line in enumerate(lines) if "## 1.2.0 - 2024-01-15" in line
        )

        # Unreleased section should now be empty (or minimal)
        unreleased_section = lines[unreleased_idx:version_idx]
        content_lines = [line for line in unreleased_section[1:] if line.strip()]
        assert len(content_lines) == 0  # Should be empty now

        # Version section should contain the moved content
        next_version_idx = next(
            (
                i
                for i, line in enumerate(lines[version_idx + 1 :], version_idx + 1)
                if line.strip().startswith("## ")
            ),
            len(lines),
        )
        version_section = lines[version_idx:next_version_idx]
        version_content = "\n".join(version_section)

        assert "### Added" in version_content
        assert "- New feature X" in version_content
        assert "- New feature Y" in version_content
        assert "### Fixed" in version_content
        assert "- Bug fix Z" in version_content

    def test_move_unreleased_to_version_default_date(
        self, changelog_manager: ChangelogManager, sample_changelog_content: str
    ):
        """Test moving unreleased content with default date (today)."""
        changelog_manager.write_changelog(sample_changelog_content)

        today = datetime.now().strftime("%Y-%m-%d")
        changelog_manager.move_unreleased_to_version("1.2.0")

        updated_content = changelog_manager.read_changelog()
        assert f"## 1.2.0 - {today}" in updated_content

    def test_move_unreleased_to_version_invalid_date(
        self, changelog_manager: ChangelogManager, sample_changelog_content: str
    ):
        """Test moving unreleased content with invalid date format."""
        changelog_manager.write_changelog(sample_changelog_content)

        with pytest.raises(ChangelogError, match="Invalid date format"):
            changelog_manager.move_unreleased_to_version("1.2.0", "invalid-date")

    def test_move_unreleased_to_version_empty_content(
        self, changelog_manager: ChangelogManager
    ):
        """Test moving empty unreleased content."""
        content = """# Changelog

## Unreleased

## 1.0.0 - 2023-12-01

### Added
- Initial release
"""
        changelog_manager.write_changelog(content)

        changelog_manager.move_unreleased_to_version("1.1.0", "2024-01-15")

        updated_content = changelog_manager.read_changelog()

        # Should not create version section for empty content
        assert "## 1.1.0 - 2024-01-15" not in updated_content

        # Unreleased section should still exist and be empty
        assert "## Unreleased" in updated_content

    def test_has_unreleased_content_true(
        self, changelog_manager: ChangelogManager, sample_changelog_content: str
    ):
        """Test has_unreleased_content when content exists."""
        changelog_manager.write_changelog(sample_changelog_content)
        assert changelog_manager.has_unreleased_content() is True

    def test_has_unreleased_content_false(self, changelog_manager: ChangelogManager):
        """Test has_unreleased_content when no content exists."""
        content = """# Changelog

## Unreleased

## 1.0.0 - 2023-12-01

### Added
- Initial release
"""
        changelog_manager.write_changelog(content)
        assert changelog_manager.has_unreleased_content() is False

    def test_has_unreleased_content_no_file(self, changelog_manager: ChangelogManager):
        """Test has_unreleased_content when file doesn't exist."""
        assert changelog_manager.has_unreleased_content() is False

    def test_get_version_sections(
        self, changelog_manager: ChangelogManager, sample_changelog_content: str
    ):
        """Test getting version sections from changelog."""
        changelog_manager.write_changelog(sample_changelog_content)

        versions = changelog_manager.get_version_sections()
        assert len(versions) == 1
        assert versions[0] == ("1.0.0", "2023-12-01")

    def test_get_version_sections_multiple(self, changelog_manager: ChangelogManager):
        """Test getting multiple version sections."""
        content = """# Changelog

## Unreleased

## 2.0.0 - 2024-01-15

### Added
- Major feature

## 1.1.0 - 2023-12-15

### Added
- Minor feature

## 1.0.0 - 2023-12-01

### Added
- Initial release
"""
        changelog_manager.write_changelog(content)

        versions = changelog_manager.get_version_sections()
        assert len(versions) == 3
        assert versions[0] == ("2.0.0", "2024-01-15")
        assert versions[1] == ("1.1.0", "2023-12-15")
        assert versions[2] == ("1.0.0", "2023-12-01")

    def test_validate_changelog_format_valid(
        self, changelog_manager: ChangelogManager, sample_changelog_content: str
    ):
        """Test validating valid changelog format."""
        changelog_manager.write_changelog(sample_changelog_content)

        issues = changelog_manager.validate_changelog_format()
        assert issues == []

    def test_validate_changelog_format_no_file(
        self, changelog_manager: ChangelogManager
    ):
        """Test validating when changelog doesn't exist."""
        issues = changelog_manager.validate_changelog_format()
        assert "does not exist" in issues[0]

    def test_validate_changelog_format_no_unreleased(
        self, changelog_manager: ChangelogManager
    ):
        """Test validating when no unreleased section exists."""
        content = """# Changelog

## 1.0.0 - 2023-12-01

### Added
- Initial release
"""
        changelog_manager.write_changelog(content)

        issues = changelog_manager.validate_changelog_format()
        assert any("Missing '## Unreleased' section" in issue for issue in issues)

