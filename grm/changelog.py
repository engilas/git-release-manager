"""Changelog management utilities for CHANGELOG.md manipulation."""

import os
import re
from datetime import datetime
from typing import List, Optional, Tuple


class ChangelogError(Exception):
    """Exception raised for changelog operation errors."""

    pass


class ChangelogManager:
    """Manages CHANGELOG.md file operations."""

    # Pattern to match version headers (## 1.2.3 - 2023-12-25)
    VERSION_HEADER_PATTERN = re.compile(r"^## (\d+\.\d+\.\d+) - (\d{4}-\d{2}-\d{2})$")

    # Pattern to match unreleased header
    UNRELEASED_PATTERN = re.compile(r"^## Unreleased$", re.IGNORECASE)

    def __init__(self, changelog_path: str = "CHANGELOG.md"):
        """Initialize ChangelogManager.

        Args:
            changelog_path: Path to the CHANGELOG.md file
        """
        self.changelog_path = changelog_path

    def changelog_exists(self) -> bool:
        """Check if CHANGELOG.md exists.

        Returns:
            True if changelog exists, False otherwise
        """
        return os.path.exists(self.changelog_path)

    def create_initial_changelog(self) -> None:
        """Create an initial CHANGELOG.md file with basic structure."""
        initial_content = """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

"""

        with open(self.changelog_path, "w", encoding="utf-8") as f:
            f.write(initial_content)

    def read_changelog(self) -> str:
        """Read the entire changelog content.

        Returns:
            Changelog content as string

        Raises:
            ChangelogError: If changelog cannot be read
        """
        try:
            with open(self.changelog_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            raise ChangelogError(f"Changelog file '{self.changelog_path}' not found")
        except Exception as e:
            raise ChangelogError(f"Failed to read changelog: {e}")

    def write_changelog(self, content: str) -> None:
        """Write content to changelog file.

        Args:
            content: Content to write

        Raises:
            ChangelogError: If changelog cannot be written
        """
        try:
            with open(self.changelog_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            raise ChangelogError(f"Failed to write changelog: {e}")

    def _find_unreleased_section(self, lines: List[str]) -> Tuple[int, int]:
        """Find the start and end of the Unreleased section.

        Args:
            lines: List of changelog lines

        Returns:
            Tuple of (start_index, end_index) for unreleased content

        Raises:
            ChangelogError: If unreleased section is not found or malformed
        """
        unreleased_start = -1
        content_start = -1
        content_end = -1

        for i, line in enumerate(lines):
            if self.UNRELEASED_PATTERN.match(line.strip()):
                unreleased_start = i
                # Look for content start (first non-empty line after header)
                for j in range(i + 1, len(lines)):
                    if lines[j].strip():
                        if lines[j].strip().startswith("##"):
                            # Next section found, unreleased is empty
                            content_start = j
                            content_end = j
                            break
                        else:
                            content_start = j
                            break
                else:
                    # No content found, unreleased section goes to end
                    content_start = len(lines)
                    content_end = len(lines)
                break

        if unreleased_start == -1:
            raise ChangelogError("'## Unreleased' section not found in changelog")

        # Find end of unreleased content (next ## header or end of file)
        if content_start < len(lines):
            for i in range(content_start, len(lines)):
                if lines[i].strip().startswith(
                    "## "
                ) and not self.UNRELEASED_PATTERN.match(lines[i].strip()):
                    content_end = i
                    break
            else:
                content_end = len(lines)

        return content_start, content_end

    def extract_unreleased_content(self) -> List[str]:
        """Extract content from the Unreleased section.

        Returns:
            List of lines from the unreleased section

        Raises:
            ChangelogError: If extraction fails
        """
        content = self.read_changelog()
        lines = content.split("\n")

        content_start, content_end = self._find_unreleased_section(lines)

        # Extract content between start and end
        unreleased_content = []
        for i in range(content_start, content_end):
            line = lines[i].rstrip()
            if line.strip():  # Skip empty lines at the boundaries
                unreleased_content.append(line)

        return unreleased_content

    def move_unreleased_to_version(
        self, version: str, date: Optional[str] = None
    ) -> None:
        """Move unreleased content to a new version section.

        Args:
            version: Version string (e.g., "1.2.3")
            date: Release date in YYYY-MM-DD format. If None, uses today's date

        Raises:
            ChangelogError: If operation fails
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        # Validate date format
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise ChangelogError(f"Invalid date format: {date}. Expected YYYY-MM-DD")

        content = self.read_changelog()
        lines = content.split("\n")

        # Find unreleased section
        unreleased_start = -1
        for i, line in enumerate(lines):
            if self.UNRELEASED_PATTERN.match(line.strip()):
                unreleased_start = i
                break

        if unreleased_start == -1:
            raise ChangelogError("'## Unreleased' section not found in changelog")

        # Extract unreleased content
        content_start, content_end = self._find_unreleased_section(lines)
        unreleased_content = lines[content_start:content_end]

        # Remove empty lines from unreleased content
        while unreleased_content and not unreleased_content[0].strip():
            unreleased_content.pop(0)
        while unreleased_content and not unreleased_content[-1].strip():
            unreleased_content.pop()

        # Build new changelog content
        new_lines = []

        # Add everything up to and including the Unreleased header
        new_lines.extend(lines[: unreleased_start + 1])

        # Add empty line after Unreleased header
        new_lines.append("")

        # Add new version section
        if unreleased_content:
            new_lines.append(f"## {version} - {date}")
            new_lines.append("")
            new_lines.extend(unreleased_content)
            new_lines.append("")

        # Add everything after the unreleased content
        new_lines.extend(lines[content_end:])

        # Write updated changelog
        self.write_changelog("\n".join(new_lines))

    def has_unreleased_content(self) -> bool:
        """Check if there is content in the Unreleased section.

        Returns:
            True if unreleased section has content, False otherwise
        """
        try:
            unreleased_content = self.extract_unreleased_content()
            return len(unreleased_content) > 0
        except ChangelogError:
            return False

    def get_version_sections(self) -> List[Tuple[str, str]]:
        """Get all version sections from the changelog.

        Returns:
            List of tuples (version, date) for each version section
        """
        content = self.read_changelog()
        lines = content.split("\n")

        versions = []
        for line in lines:
            match = self.VERSION_HEADER_PATTERN.match(line.strip())
            if match:
                version, date = match.groups()
                versions.append((version, date))

        return versions

    def validate_changelog_format(self) -> List[str]:
        """Validate changelog format and return list of issues.

        Returns:
            List of validation issues (empty if valid)
        """
        issues = []

        if not self.changelog_exists():
            issues.append("CHANGELOG.md does not exist")
            return issues

        try:
            content = self.read_changelog()
            lines = content.split("\n")
        except Exception as e:
            issues.append(f"Cannot read changelog: {e}")
            return issues

        # Check for Unreleased section
        has_unreleased = False
        for line in lines:
            if self.UNRELEASED_PATTERN.match(line.strip()):
                has_unreleased = True
                break

        if not has_unreleased:
            issues.append("Missing '## Unreleased' section")

        # Check version header format
        for i, line in enumerate(lines, 1):
            if line.strip().startswith("## ") and not self.UNRELEASED_PATTERN.match(
                line.strip()
            ):
                if not self.VERSION_HEADER_PATTERN.match(line.strip()):
                    issues.append(
                        f"Line {i}: Invalid version header format: '{line.strip()}'"
                    )

        return issues
