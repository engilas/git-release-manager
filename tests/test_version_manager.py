"""Tests for version_manager module."""

import pytest

from grm.version_manager import Version, VersionManager


class TestVersion:
    """Test cases for Version class."""

    def test_version_creation(self):
        """Test creating a Version instance."""
        version = Version(1, 2, 3)
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3

    def test_version_string_representation(self):
        """Test string representation of Version."""
        version = Version(1, 2, 3)
        assert str(version) == "1.2.3"

    def test_version_comparison_less_than(self):
        """Test version comparison (less than)."""
        v1 = Version(1, 0, 0)
        v2 = Version(1, 1, 0)
        v3 = Version(1, 1, 1)
        v4 = Version(2, 0, 0)

        assert v1 < v2
        assert v2 < v3
        assert v3 < v4
        assert v1 < v4

    def test_version_comparison_equal(self):
        """Test version comparison (equality)."""
        v1 = Version(1, 2, 3)
        v2 = Version(1, 2, 3)
        v3 = Version(1, 2, 4)

        assert v1 == v2
        assert not (v1 == v3)

    def test_bump_major(self):
        """Test major version bump."""
        version = Version(1, 2, 3)
        bumped = version.bump_major()

        assert bumped.major == 2
        assert bumped.minor == 0
        assert bumped.patch == 0

        # Original should be unchanged
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3

    def test_bump_minor(self):
        """Test minor version bump."""
        version = Version(1, 2, 3)
        bumped = version.bump_minor()

        assert bumped.major == 1
        assert bumped.minor == 3
        assert bumped.patch == 0

        # Original should be unchanged
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3

    def test_bump_patch(self):
        """Test patch version bump."""
        version = Version(1, 2, 3)
        bumped = version.bump_patch()

        assert bumped.major == 1
        assert bumped.minor == 2
        assert bumped.patch == 4

        # Original should be unchanged
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3


class TestVersionManager:
    """Test cases for VersionManager class."""

    def test_init_with_empty_tags(self):
        """Test VersionManager initialization with no tags."""
        manager = VersionManager([])
        assert manager.get_all_versions() == []
        assert manager.get_latest_version() is None

    def test_init_with_semver_tags(self):
        """Test VersionManager initialization with semantic version tags."""
        tags = ["1.0.0", "1.1.0", "1.1.1", "2.0.0"]
        manager = VersionManager(tags)

        versions = manager.get_all_versions()
        assert len(versions) == 4
        assert versions[0] == Version(1, 0, 0)
        assert versions[-1] == Version(2, 0, 0)

    def test_init_with_prefixed_tags(self):
        """Test VersionManager initialization with prefixed tags."""
        tags = ["v1.0.0", "version-1.1.0", "release-1.1.1"]
        manager = VersionManager(tags)

        versions = manager.get_all_versions()
        assert len(versions) == 3
        assert versions[0] == Version(1, 0, 0)
        assert versions[1] == Version(1, 1, 0)
        assert versions[2] == Version(1, 1, 1)

    def test_init_with_mixed_tags(self):
        """Test VersionManager initialization with mixed valid/invalid tags."""
        tags = ["1.0.0", "invalid-tag", "v1.1.0", "not-a-version", "1.2.0"]
        manager = VersionManager(tags)

        versions = manager.get_all_versions()
        assert len(versions) == 3
        assert versions[0] == Version(1, 0, 0)
        assert versions[1] == Version(1, 1, 0)
        assert versions[2] == Version(1, 2, 0)

    def test_get_latest_version_with_versions(self):
        """Test getting latest version when versions exist."""
        tags = ["1.0.0", "1.1.0", "2.0.0", "1.1.1"]
        manager = VersionManager(tags)

        latest = manager.get_latest_version()
        assert latest == Version(2, 0, 0)

    def test_get_latest_version_no_versions(self):
        """Test getting latest version when no versions exist."""
        manager = VersionManager([])
        assert manager.get_latest_version() is None

    def test_get_next_minor_version_with_existing(self):
        """Test getting next minor version with existing versions."""
        tags = ["1.0.0", "1.1.0", "1.1.1"]
        manager = VersionManager(tags)

        next_minor = manager.get_next_minor_version()
        assert next_minor == Version(1, 2, 0)

    def test_get_next_minor_version_no_existing(self):
        """Test getting next minor version with no existing versions."""
        manager = VersionManager([])

        next_minor = manager.get_next_minor_version()
        assert next_minor == Version(0, 1, 0)

    def test_get_next_patch_version_with_existing(self):
        """Test getting next patch version with existing versions."""
        tags = ["1.0.0", "1.1.0", "1.1.1"]
        manager = VersionManager(tags)

        next_patch = manager.get_next_patch_version()
        assert next_patch == Version(1, 1, 2)

    def test_get_next_patch_version_no_existing(self):
        """Test getting next patch version with no existing versions."""
        manager = VersionManager([])

        next_patch = manager.get_next_patch_version()
        assert next_patch == Version(0, 0, 1)

    def test_get_next_major_version_with_existing(self):
        """Test getting next major version with existing versions."""
        tags = ["1.0.0", "1.1.0", "1.1.1"]
        manager = VersionManager(tags)

        next_major = manager.get_next_major_version()
        assert next_major == Version(2, 0, 0)

    def test_get_next_major_version_no_existing(self):
        """Test getting next major version with no existing versions."""
        manager = VersionManager([])

        next_major = manager.get_next_major_version()
        assert next_major == Version(1, 0, 0)

    def test_version_exists(self):
        """Test checking if a version exists."""
        tags = ["1.0.0", "1.1.0"]
        manager = VersionManager(tags)

        assert manager.version_exists(Version(1, 0, 0)) is True
        assert manager.version_exists(Version(1, 1, 0)) is True
        assert manager.version_exists(Version(1, 2, 0)) is False
        assert manager.version_exists(Version(2, 0, 0)) is False

    def test_is_valid_semver(self):
        """Test semantic version validation."""
        manager = VersionManager([])

        assert manager.is_valid_semver("1.0.0") is True
        assert manager.is_valid_semver("0.0.1") is True
        assert manager.is_valid_semver("10.20.30") is True

        assert manager.is_valid_semver("1.0") is False
        assert manager.is_valid_semver("1.0.0.0") is False
        assert manager.is_valid_semver("v1.0.0") is False
        assert manager.is_valid_semver("1.0.0-alpha") is False
        assert manager.is_valid_semver("invalid") is False

    def test_parse_version_string(self):
        """Test parsing version string."""
        manager = VersionManager([])

        version = manager.parse_version_string("1.2.3")
        assert version == Version(1, 2, 3)

        invalid = manager.parse_version_string("invalid")
        assert invalid is None

    def test_suggest_version_minor(self):
        """Test version suggestion for minor bump."""
        tags = ["1.0.0", "1.1.0"]
        manager = VersionManager(tags)

        suggested = manager.suggest_version("minor")
        assert suggested == Version(1, 2, 0)

    def test_suggest_version_patch(self):
        """Test version suggestion for patch bump."""
        tags = ["1.0.0", "1.1.0"]
        manager = VersionManager(tags)

        suggested = manager.suggest_version("patch")
        assert suggested == Version(1, 1, 1)

    def test_suggest_version_major(self):
        """Test version suggestion for major bump."""
        tags = ["1.0.0", "1.1.0"]
        manager = VersionManager(tags)

        suggested = manager.suggest_version("major")
        assert suggested == Version(2, 0, 0)

    def test_suggest_version_invalid(self):
        """Test version suggestion with invalid bump type."""
        manager = VersionManager([])

        with pytest.raises(ValueError, match="Invalid bump type"):
            manager.suggest_version("invalid")

    def test_get_version_summary(self):
        """Test getting version summary."""
        tags = ["1.0.0", "1.1.0", "1.1.1"]
        manager = VersionManager(tags)

        summary = manager.get_version_summary()
        assert "Latest version: 1.1.1" in summary
        assert "Total versions: 3" in summary
        assert "Next minor: 1.2.0" in summary
        assert "Next patch: 1.1.2" in summary

    def test_get_version_summary_no_versions(self):
        """Test getting version summary with no versions."""
        manager = VersionManager([])

        summary = manager.get_version_summary()
        assert "No versions found" in summary
