"""Version management utilities for SemVer handling."""

import re
from typing import List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Version:
    """Represents a semantic version."""

    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def __lt__(self, other: "Version") -> bool:
        return (self.major, self.minor, self.patch) < (
            other.major,
            other.minor,
            other.patch,
        )

    def __eq__(self, other: "Version") -> bool:
        return (self.major, self.minor, self.patch) == (
            other.major,
            other.minor,
            other.patch,
        )

    def bump_major(self) -> "Version":
        """Return a new version with major version bumped and minor/patch reset to 0."""
        return Version(self.major + 1, 0, 0)

    def bump_minor(self) -> "Version":
        """Return a new version with minor version bumped and patch reset to 0."""
        return Version(self.major, self.minor + 1, 0)

    def bump_patch(self) -> "Version":
        """Return a new version with patch version bumped."""
        return Version(self.major, self.minor, self.patch + 1)


class VersionManager:
    """Manages semantic versioning for releases."""

    # Regex pattern for semantic versioning (MAJOR.MINOR.PATCH)
    SEMVER_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")

    def __init__(self, tags: List[str]):
        """Initialize VersionManager with existing tags.

        Args:
            tags: List of tag names from the repository
        """
        self.tags = tags
        self._versions = self._parse_versions()

    def _parse_versions(self) -> List[Version]:
        """Parse semantic versions from tags.

        Returns:
            List of Version objects sorted in ascending order
        """
        versions = []

        for tag in self.tags:
            # Remove common prefixes like 'v', 'version-', 'release-'
            # Sort by length to check longer prefixes first
            clean_tag = tag
            for prefix in sorted(["v", "version-", "release-"], key=len, reverse=True):
                if tag.startswith(prefix):
                    clean_tag = tag[len(prefix) :]
                    break

            match = self.SEMVER_PATTERN.match(clean_tag)
            if match:
                major, minor, patch = map(int, match.groups())
                versions.append(Version(major, minor, patch))

        return sorted(versions)

    def get_latest_version(self) -> Optional[Version]:
        """Get the latest semantic version.

        Returns:
            Latest Version object or None if no versions found
        """
        if not self._versions:
            return None
        return self._versions[-1]

    def get_next_minor_version(self) -> Version:
        """Get the next minor version.

        Returns:
            Next minor version (e.g., 1.2.3 -> 1.3.0)
        """
        latest = self.get_latest_version()
        if latest is None:
            return Version(0, 1, 0)
        return latest.bump_minor()

    def get_next_patch_version(self) -> Version:
        """Get the next patch version.

        Returns:
            Next patch version (e.g., 1.2.3 -> 1.2.4)
        """
        latest = self.get_latest_version()
        if latest is None:
            return Version(0, 0, 1)
        return latest.bump_patch()

    def get_next_major_version(self) -> Version:
        """Get the next major version.

        Returns:
            Next major version (e.g., 1.2.3 -> 2.0.0)
        """
        latest = self.get_latest_version()
        if latest is None:
            return Version(1, 0, 0)
        return latest.bump_major()

    def version_exists(self, version: Version) -> bool:
        """Check if a version already exists.

        Args:
            version: Version to check

        Returns:
            True if version exists, False otherwise
        """
        return version in self._versions

    def get_all_versions(self) -> List[Version]:
        """Get all parsed versions sorted in ascending order.

        Returns:
            List of Version objects
        """
        return self._versions.copy()

    def is_valid_semver(self, version_string: str) -> bool:
        """Check if a string is a valid semantic version.

        Args:
            version_string: String to validate

        Returns:
            True if valid semantic version, False otherwise
        """
        return bool(self.SEMVER_PATTERN.match(version_string))

    def parse_version_string(self, version_string: str) -> Optional[Version]:
        """Parse a version string into a Version object.

        Args:
            version_string: String to parse (e.g., "1.2.3")

        Returns:
            Version object or None if parsing fails
        """
        match = self.SEMVER_PATTERN.match(version_string)
        if match:
            major, minor, patch = map(int, match.groups())
            return Version(major, minor, patch)
        return None

    def suggest_version(self, bump_type: str) -> Version:
        """Suggest next version based on bump type.

        Args:
            bump_type: Type of version bump ('major', 'minor', 'patch')

        Returns:
            Suggested Version object

        Raises:
            ValueError: If bump_type is not valid
        """
        if bump_type == "major":
            return self.get_next_major_version()
        elif bump_type == "minor":
            return self.get_next_minor_version()
        elif bump_type == "patch":
            return self.get_next_patch_version()
        else:
            raise ValueError(
                f"Invalid bump type: {bump_type}. Must be 'major', 'minor', or 'patch'"
            )

    def get_version_summary(self) -> str:
        """Get a summary of version information.

        Returns:
            Human-readable version summary
        """
        latest = self.get_latest_version()
        if latest is None:
            return "No versions found. Starting from 0.1.0 or 0.0.1."

        total_versions = len(self._versions)
        next_minor = self.get_next_minor_version()
        next_patch = self.get_next_patch_version()

        return (
            f"Latest version: {latest}\n"
            f"Total versions: {total_versions}\n"
            f"Next minor: {next_minor}\n"
            f"Next patch: {next_patch}"
        )
