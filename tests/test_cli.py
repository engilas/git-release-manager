"""Tests for cli module."""

import os
from unittest.mock import patch, Mock

import pytest
from click.testing import CliRunner

from grm.cli import cli, release, finish
from grm.git_operations import GitOperationError
from grm.changelog import ChangelogError


class TestCLI:
    """Test cases for CLI commands."""

    def test_cli_no_command(self):
        """Test CLI with no command shows help."""
        runner = CliRunner()
        result = runner.invoke(cli)

        assert result.exit_code == 0
        assert "Git Release Manager" in result.output

    @patch("grm.cli.GitManager")
    @patch("grm.cli.ChangelogManager")
    @patch("grm.cli.VersionManager")
    def test_release_command_success(
        self, mock_version_manager, mock_changelog_manager, mock_git_manager
    ):
        """Test successful release command execution."""
        # Setup mocks
        git_mock = Mock()
        git_mock.is_working_directory_clean.return_value = True
        git_mock.get_release_source_branch.return_value = "main"
        git_mock.get_current_branch_name.return_value = "main"
        git_mock.get_all_tags.return_value = ["1.0.0", "1.1.0"]
        mock_git_manager.return_value = git_mock

        changelog_mock = Mock()
        changelog_mock.changelog_exists.return_value = True
        changelog_mock.validate_changelog_format.return_value = []
        changelog_mock.has_unreleased_content.return_value = True
        mock_changelog_manager.return_value = changelog_mock

        version_mock = Mock()
        version_mock.suggest_version.return_value = Mock(__str__=lambda x: "1.2.0")
        mock_version_manager.return_value = version_mock

        runner = CliRunner()
        result = runner.invoke(release, ["--minor"], input="y\n")

        assert result.exit_code == 0
        assert "Release branch 'release/1.2.0' created successfully" in result.output

        # Verify method calls
        git_mock.create_branch.assert_called_once_with("release/1.2.0", checkout=True)
        changelog_mock.move_unreleased_to_version.assert_called_once()
        git_mock.commit_changes.assert_called_once_with(
            "Changelog", files=["CHANGELOG.md"]
        )

    @patch("grm.cli.GitManager")
    @patch("grm.cli.ChangelogManager")
    @patch("grm.cli.VersionManager")
    def test_release_command_patch_flag(
        self, mock_version_manager, mock_changelog_manager, mock_git_manager
    ):
        """Test release command with patch flag."""
        # Setup mocks
        git_mock = Mock()
        git_mock.is_working_directory_clean.return_value = True
        git_mock.get_release_source_branch.return_value = "main"
        git_mock.get_current_branch_name.return_value = "main"
        git_mock.get_all_tags.return_value = ["1.0.0"]
        mock_git_manager.return_value = git_mock

        changelog_mock = Mock()
        changelog_mock.changelog_exists.return_value = True
        changelog_mock.validate_changelog_format.return_value = []
        changelog_mock.has_unreleased_content.return_value = True
        mock_changelog_manager.return_value = changelog_mock

        version_mock = Mock()
        version_mock.suggest_version.return_value = Mock(__str__=lambda x: "1.0.1")
        mock_version_manager.return_value = version_mock

        runner = CliRunner()
        result = runner.invoke(release, ["--patch"], input="y\n")

        assert result.exit_code == 0
        version_mock.suggest_version.assert_called_with("patch")

    @patch("grm.cli.GitManager")
    @patch("grm.cli.ChangelogManager")
    def test_release_command_dirty_working_directory(
        self, mock_changelog_manager, mock_git_manager
    ):
        """Test release command with dirty working directory."""
        git_mock = Mock()
        git_mock.is_working_directory_clean.return_value = False
        mock_git_manager.return_value = git_mock

        runner = CliRunner()
        result = runner.invoke(release, ["--minor"])

        assert result.exit_code == 1
        assert "uncommitted changes" in result.output

    @patch("grm.cli.GitManager")
    @patch("grm.cli.ChangelogManager")
    def test_release_command_wrong_branch(
        self, mock_changelog_manager, mock_git_manager
    ):
        """Test release command on wrong branch."""
        git_mock = Mock()
        git_mock.is_working_directory_clean.return_value = True
        git_mock.get_release_source_branch.return_value = "main"
        git_mock.get_current_branch_name.return_value = "feature-branch"
        mock_git_manager.return_value = git_mock

        runner = CliRunner()
        result = runner.invoke(release, ["--minor"])

        assert result.exit_code == 1
        assert "Must be on 'main' branch" in result.output

    @patch("grm.cli.GitManager")
    @patch("grm.cli.ChangelogManager")
    @patch("grm.cli.VersionManager")
    def test_release_command_from_develop_branch(
        self, mock_version_manager, mock_changelog_manager, mock_git_manager
    ):
        """Test successful release command from develop branch."""
        # Setup mocks
        git_mock = Mock()
        git_mock.is_working_directory_clean.return_value = True
        git_mock.get_release_source_branch.return_value = (
            "develop"  # Should return develop when it exists
        )
        git_mock.get_current_branch_name.return_value = "develop"
        git_mock.get_all_tags.return_value = ["1.0.0", "1.1.0"]
        mock_git_manager.return_value = git_mock

        changelog_mock = Mock()
        changelog_mock.changelog_exists.return_value = True
        changelog_mock.validate_changelog_format.return_value = []
        changelog_mock.has_unreleased_content.return_value = True
        mock_changelog_manager.return_value = changelog_mock

        version_mock = Mock()
        version_mock.suggest_version.return_value = Mock(__str__=lambda x: "1.2.0")
        mock_version_manager.return_value = version_mock

        runner = CliRunner()
        result = runner.invoke(release, ["--minor"], input="y\n")

        assert result.exit_code == 0
        assert "Release branch 'release/1.2.0' created successfully" in result.output

        # Verify method calls
        git_mock.create_branch.assert_called_once_with("release/1.2.0", checkout=True)
        changelog_mock.move_unreleased_to_version.assert_called_once()
        git_mock.commit_changes.assert_called_once_with(
            "Changelog", files=["CHANGELOG.md"]
        )

    @patch("grm.cli.GitManager")
    @patch("grm.cli.ChangelogManager")
    def test_release_command_wrong_branch_with_develop(
        self, mock_changelog_manager, mock_git_manager
    ):
        """Test release command on wrong branch when develop exists - prompt to switch."""
        git_mock = Mock()
        git_mock.is_working_directory_clean.return_value = True
        git_mock.get_release_source_branch.return_value = "develop"
        git_mock.get_current_branch_name.return_value = "feature-branch"
        git_mock.branch_exists.return_value = True
        mock_git_manager.return_value = git_mock

        runner = CliRunner()
        # Decline the prompt to switch branches
        result = runner.invoke(release, ["--minor"], input="n\n")

        assert result.exit_code == 1
        assert "Currently on 'feature-branch' branch" in result.output
        assert "Switch to 'develop' branch and continue?" in result.output
        assert "Release creation cancelled." in result.output

    @patch("grm.cli.GitManager")
    @patch("grm.cli.ChangelogManager")
    def test_release_command_wrong_branch_with_develop_accept_switch(
        self, mock_changelog_manager, mock_git_manager
    ):
        """Test release command on wrong branch when develop exists - accept switch."""
        git_mock = Mock()
        git_mock.is_working_directory_clean.return_value = True
        git_mock.get_release_source_branch.return_value = "develop"
        git_mock.get_current_branch_name.return_value = "feature-branch"
        git_mock.branch_exists.return_value = True
        git_mock.get_all_tags.return_value = ["0.1.0"]
        git_mock.has_remote.return_value = True
        mock_git_manager.return_value = git_mock

        changelog_mock = Mock()
        changelog_mock.changelog_exists.return_value = True
        changelog_mock.validate_changelog_format.return_value = []
        changelog_mock.has_unreleased_content.return_value = True
        mock_changelog_manager.return_value = changelog_mock

        runner = CliRunner()
        # Accept the prompt to switch branches, then confirm the release creation
        result = runner.invoke(release, ["--minor"], input="y\ny\n")

        assert result.exit_code == 0
        git_mock.checkout_branch.assert_called_with("develop")
        git_mock.pull_branch.assert_called_once_with("develop")
        assert "Switched to 'develop' branch" in result.output
        assert "Pulled latest changes" in result.output
        assert "Release branch 'release/0.2.0' created successfully!" in result.output

    @patch("grm.cli.GitManager")
    @patch("grm.cli.ChangelogManager")
    def test_release_command_wrong_branch_accept_switch_no_remote(
        self, mock_changelog_manager, mock_git_manager
    ):
        """Test release command on wrong branch - accept switch without remote."""
        git_mock = Mock()
        git_mock.is_working_directory_clean.return_value = True
        git_mock.get_release_source_branch.return_value = "develop"
        git_mock.get_current_branch_name.return_value = "feature-branch"
        git_mock.branch_exists.return_value = True
        git_mock.get_all_tags.return_value = ["0.1.0"]
        git_mock.has_remote.return_value = False
        mock_git_manager.return_value = git_mock

        changelog_mock = Mock()
        changelog_mock.changelog_exists.return_value = True
        changelog_mock.validate_changelog_format.return_value = []
        changelog_mock.has_unreleased_content.return_value = True
        mock_changelog_manager.return_value = changelog_mock

        runner = CliRunner()
        result = runner.invoke(release, ["--minor"], input="y\ny\n")

        assert result.exit_code == 0
        git_mock.checkout_branch.assert_called_with("develop")
        git_mock.pull_branch.assert_not_called()
        assert "Switched to 'develop' branch" in result.output
        assert "Release branch 'release/0.2.0' created successfully!" in result.output

    @patch("grm.cli.GitManager")
    @patch("grm.cli.ChangelogManager")
    def test_release_command_wrong_branch_accept_switch_pull_fails(
        self, mock_changelog_manager, mock_git_manager
    ):
        """Test release command on wrong branch - accept switch but pull fails."""
        git_mock = Mock()
        git_mock.is_working_directory_clean.return_value = True
        git_mock.get_release_source_branch.return_value = "develop"
        git_mock.get_current_branch_name.return_value = "feature-branch"
        git_mock.branch_exists.return_value = True
        git_mock.get_all_tags.return_value = ["0.1.0"]
        git_mock.has_remote.return_value = True
        git_mock.pull_branch.side_effect = GitOperationError("Network error")
        mock_git_manager.return_value = git_mock

        changelog_mock = Mock()
        changelog_mock.changelog_exists.return_value = True
        changelog_mock.validate_changelog_format.return_value = []
        changelog_mock.has_unreleased_content.return_value = True
        mock_changelog_manager.return_value = changelog_mock

        runner = CliRunner()
        result = runner.invoke(release, ["--minor"], input="y\ny\n")

        assert result.exit_code == 0
        git_mock.checkout_branch.assert_called_with("develop")
        git_mock.pull_branch.assert_called_once_with("develop")
        assert "Switched to 'develop' branch" in result.output
        assert "Failed to pull latest changes" in result.output
        assert "Continuing with local version" in result.output
        assert "Release branch 'release/0.2.0' created successfully!" in result.output

    @patch("grm.cli.GitManager")
    @patch("grm.cli.ChangelogManager")
    def test_release_command_no_changelog(
        self, mock_changelog_manager, mock_git_manager
    ):
        """Test release command with no changelog."""
        git_mock = Mock()
        git_mock.is_working_directory_clean.return_value = True
        git_mock.get_release_source_branch.return_value = "main"
        git_mock.get_current_branch_name.return_value = "main"
        mock_git_manager.return_value = git_mock

        changelog_mock = Mock()
        changelog_mock.changelog_exists.return_value = False
        mock_changelog_manager.return_value = changelog_mock

        runner = CliRunner()
        result = runner.invoke(release, ["--minor"], input="n\n")

        assert result.exit_code == 1
        assert "CHANGELOG.md is required" in result.output

    @patch("grm.cli.GitManager")
    @patch("grm.cli.ChangelogManager")
    @patch("grm.cli.VersionManager")
    def test_release_command_no_unreleased_content(
        self, mock_version_manager, mock_changelog_manager, mock_git_manager
    ):
        """Test release command with no unreleased content."""
        git_mock = Mock()
        git_mock.is_working_directory_clean.return_value = True
        git_mock.get_release_source_branch.return_value = "main"
        git_mock.get_current_branch_name.return_value = "main"
        git_mock.get_all_tags.return_value = []
        mock_git_manager.return_value = git_mock

        changelog_mock = Mock()
        changelog_mock.changelog_exists.return_value = True
        changelog_mock.validate_changelog_format.return_value = []
        changelog_mock.has_unreleased_content.return_value = False
        mock_changelog_manager.return_value = changelog_mock

        runner = CliRunner()
        result = runner.invoke(release, ["--minor"], input="n\n")

        assert result.exit_code == 1
        assert "no content to release" in result.output

    @patch("grm.cli.GitManager")
    @patch("grm.cli.ChangelogManager")
    @patch("grm.cli.VersionManager")
    @patch("grm.cli._prompt_for_bump_type")
    def test_release_command_prompt_for_bump_type(
        self,
        mock_prompt,
        mock_version_manager,
        mock_changelog_manager,
        mock_git_manager,
    ):
        """Test release command prompting for bump type."""
        # Setup mocks
        git_mock = Mock()
        git_mock.is_working_directory_clean.return_value = True
        git_mock.get_release_source_branch.return_value = "main"
        git_mock.get_current_branch_name.return_value = "main"
        git_mock.get_all_tags.return_value = []
        mock_git_manager.return_value = git_mock

        changelog_mock = Mock()
        changelog_mock.changelog_exists.return_value = True
        changelog_mock.validate_changelog_format.return_value = []
        changelog_mock.has_unreleased_content.return_value = True
        mock_changelog_manager.return_value = changelog_mock

        version_mock = Mock()
        version_mock.suggest_version.return_value = Mock(__str__=lambda x: "0.1.0")
        mock_version_manager.return_value = version_mock

        mock_prompt.return_value = "minor"

        runner = CliRunner()
        result = runner.invoke(release, input="y\n")

        assert result.exit_code == 0
        mock_prompt.assert_called_once()
        version_mock.suggest_version.assert_called_with("minor")

    @patch("grm.cli.GitManager")
    @patch("grm.cli.ChangelogManager")
    @patch("grm.cli.VersionManager")
    def test_release_command_push_with_remote(
        self, mock_version_manager, mock_changelog_manager, mock_git_manager
    ):
        """Test release command pushes branch when remote exists."""
        # Setup mocks
        git_mock = Mock()
        git_mock.is_working_directory_clean.return_value = True
        git_mock.get_release_source_branch.return_value = "main"
        git_mock.get_current_branch_name.return_value = "main"
        git_mock.get_all_tags.return_value = ["1.0.0"]
        git_mock.has_remote.return_value = True
        mock_git_manager.return_value = git_mock

        changelog_mock = Mock()
        changelog_mock.changelog_exists.return_value = True
        changelog_mock.validate_changelog_format.return_value = []
        changelog_mock.has_unreleased_content.return_value = True
        mock_changelog_manager.return_value = changelog_mock

        version_mock = Mock()
        version_mock.suggest_version.return_value = Mock(__str__=lambda x: "1.1.0")
        mock_version_manager.return_value = version_mock

        runner = CliRunner()
        result = runner.invoke(release, ["--minor"], input="y\n")

        assert result.exit_code == 0
        assert "✓ Pushed release/1.1.0 to remote" in result.output

        # Verify push was called with upstream tracking
        git_mock.push_branch.assert_called_once_with("release/1.1.0", set_upstream=True)

    @patch("grm.cli.GitManager")
    @patch("grm.cli.ChangelogManager")
    @patch("grm.cli.VersionManager")
    def test_release_command_no_push_without_remote(
        self, mock_version_manager, mock_changelog_manager, mock_git_manager
    ):
        """Test release command skips push when no remote exists."""
        # Setup mocks
        git_mock = Mock()
        git_mock.is_working_directory_clean.return_value = True
        git_mock.get_release_source_branch.return_value = "main"
        git_mock.get_current_branch_name.return_value = "main"
        git_mock.get_all_tags.return_value = ["1.0.0"]
        git_mock.has_remote.return_value = False
        mock_git_manager.return_value = git_mock

        changelog_mock = Mock()
        changelog_mock.changelog_exists.return_value = True
        changelog_mock.validate_changelog_format.return_value = []
        changelog_mock.has_unreleased_content.return_value = True
        mock_changelog_manager.return_value = changelog_mock

        version_mock = Mock()
        version_mock.suggest_version.return_value = Mock(__str__=lambda x: "1.1.0")
        mock_version_manager.return_value = version_mock

        runner = CliRunner()
        result = runner.invoke(release, ["--minor"], input="y\n")

        assert result.exit_code == 0
        assert "Pushing release branch to remote" not in result.output

        # Verify push was not called
        git_mock.push_branch.assert_not_called()

    @patch("grm.cli.GitManager")
    @patch("grm.cli.ChangelogManager")
    @patch("grm.cli.VersionManager")
    def test_release_command_push_failure_handling(
        self, mock_version_manager, mock_changelog_manager, mock_git_manager
    ):
        """Test release command handles push failures gracefully."""
        # Setup mocks
        git_mock = Mock()
        git_mock.is_working_directory_clean.return_value = True
        git_mock.get_release_source_branch.return_value = "main"
        git_mock.get_current_branch_name.return_value = "main"
        git_mock.get_all_tags.return_value = ["1.0.0"]
        git_mock.has_remote.return_value = True
        git_mock.push_branch.side_effect = GitOperationError("Push failed")
        mock_git_manager.return_value = git_mock

        changelog_mock = Mock()
        changelog_mock.changelog_exists.return_value = True
        changelog_mock.validate_changelog_format.return_value = []
        changelog_mock.has_unreleased_content.return_value = True
        mock_changelog_manager.return_value = changelog_mock

        version_mock = Mock()
        version_mock.suggest_version.return_value = Mock(__str__=lambda x: "1.1.0")
        mock_version_manager.return_value = version_mock

        runner = CliRunner()
        result = runner.invoke(release, ["--minor"], input="y\n")

        assert result.exit_code == 0  # Should not fail despite push error
        assert "Failed to push release branch: Push failed" in result.output
        assert "You may need to push manually" in result.output

        # Verify push was attempted
        git_mock.push_branch.assert_called_once_with("release/1.1.0", set_upstream=True)

    @patch("grm.cli.GitManager")
    def test_finish_command_success(self, mock_git_manager):
        """Test successful finish command execution."""
        git_mock = Mock()
        git_mock.is_working_directory_clean.return_value = True
        git_mock.get_current_branch_name.return_value = "release/1.2.0"
        git_mock.get_integration_branch.return_value = "main"
        git_mock.branch_exists.return_value = True
        git_mock.has_remote.return_value = False
        mock_git_manager.return_value = git_mock

        runner = CliRunner()
        result = runner.invoke(finish, input="y\n")

        assert result.exit_code == 0
        assert "Release 1.2.0 finished successfully" in result.output

        # Verify method calls
        git_mock.checkout_branch.assert_any_call("main")
        git_mock.merge_branch.assert_called()
        git_mock.create_tag.assert_called_once_with("1.2.0")
        git_mock.delete_branch.assert_called_once()

    @patch("grm.cli.GitManager")
    def test_finish_command_not_release_branch(self, mock_git_manager):
        """Test finish command not on release branch."""
        git_mock = Mock()
        git_mock.is_working_directory_clean.return_value = True
        git_mock.get_current_branch_name.return_value = "main"
        mock_git_manager.return_value = git_mock

        runner = CliRunner()
        result = runner.invoke(finish)

        assert result.exit_code == 1
        assert "release branch" in result.output

    @patch("grm.cli.GitManager")
    def test_finish_command_dirty_working_directory(self, mock_git_manager):
        """Test finish command with dirty working directory."""
        git_mock = Mock()
        git_mock.is_working_directory_clean.return_value = False
        mock_git_manager.return_value = git_mock

        runner = CliRunner()
        result = runner.invoke(finish)

        assert result.exit_code == 1
        assert "uncommitted changes" in result.output

    @patch("grm.cli.GitManager")
    def test_finish_command_with_develop_branch(self, mock_git_manager):
        """Test finish command with develop branch present."""
        git_mock = Mock()
        git_mock.is_working_directory_clean.return_value = True
        git_mock.get_current_branch_name.return_value = "release/1.2.0"
        git_mock.get_release_source_branch.return_value = "main"
        git_mock.branch_exists.return_value = True  # develop branch exists
        git_mock.has_remote.return_value = False
        mock_git_manager.return_value = git_mock

        runner = CliRunner()
        result = runner.invoke(finish, input="y\n")

        assert result.exit_code == 0
        assert "Merging back to develop" in result.output

        # Should checkout develop and merge
        git_mock.checkout_branch.assert_any_call("develop")

    @patch("grm.cli.GitManager")
    def test_finish_command_no_develop_branch(self, mock_git_manager):
        """Test finish command without develop branch."""
        git_mock = Mock()
        git_mock.is_working_directory_clean.return_value = True
        git_mock.get_current_branch_name.return_value = "release/1.2.0"
        git_mock.get_release_source_branch.return_value = "main"

        def branch_exists_side_effect(branch_name):
            return branch_name != "develop"

        git_mock.branch_exists.side_effect = branch_exists_side_effect
        git_mock.has_remote.return_value = False
        mock_git_manager.return_value = git_mock

        runner = CliRunner()
        result = runner.invoke(finish, input="y\n")

        assert result.exit_code == 0
        assert "No 'develop' branch found" in result.output

    @patch("grm.cli.GitManager")
    def test_finish_command_cancel(self, mock_git_manager):
        """Test finish command cancellation."""
        git_mock = Mock()
        git_mock.is_working_directory_clean.return_value = True
        git_mock.get_current_branch_name.return_value = "release/1.2.0"
        mock_git_manager.return_value = git_mock

        runner = CliRunner()
        result = runner.invoke(finish, input="n\n")

        assert result.exit_code == 0
        assert "Release finish cancelled" in result.output

        # Should not perform any git operations
        git_mock.merge_branch.assert_not_called()
        git_mock.create_tag.assert_not_called()

    @patch("grm.cli.GitManager")
    def test_finish_command_git_error(self, mock_git_manager):
        """Test finish command with Git operation error."""
        git_mock = Mock()
        git_mock.is_working_directory_clean.return_value = True
        git_mock.get_current_branch_name.return_value = "release/1.2.0"
        git_mock.get_release_source_branch.return_value = "main"
        git_mock.checkout_branch.side_effect = GitOperationError("Test error")
        mock_git_manager.return_value = git_mock

        runner = CliRunner()
        result = runner.invoke(finish, input="y\n")

        assert result.exit_code == 1
        assert "Test error" in result.output

    @patch("grm.cli.GitManager")
    def test_finish_command_checkout_to_develop_after_completion(
        self, mock_git_manager
    ):
        """Test that finish command checks out to develop branch after completion."""
        git_mock = Mock()
        git_mock.is_working_directory_clean.return_value = True
        git_mock.get_current_branch_name.return_value = "release/1.2.0"
        git_mock.get_integration_branch.return_value = "main"
        git_mock.branch_exists.return_value = True  # develop branch exists
        git_mock.has_remote.return_value = False
        mock_git_manager.return_value = git_mock

        runner = CliRunner()
        result = runner.invoke(finish, input="y\n")

        assert result.exit_code == 0

        # Verify checkout calls - should checkout develop at the end
        checkout_calls = git_mock.checkout_branch.call_args_list
        assert ("main",) in [
            call[0] for call in checkout_calls
        ]  # Checkout main for merge
        assert ("develop",) in [
            call[0] for call in checkout_calls
        ]  # Merge back to develop
        assert checkout_calls[-1][0] == ("develop",)  # Final checkout should be develop
        assert "✓ Switched to develop branch" in result.output

    @patch("grm.cli.GitManager")
    def test_finish_command_checkout_to_integration_when_no_develop(
        self, mock_git_manager
    ):
        """Test that finish command checks out to integration branch when no develop exists."""
        git_mock = Mock()
        git_mock.is_working_directory_clean.return_value = True
        git_mock.get_current_branch_name.return_value = "release/1.2.0"
        git_mock.get_integration_branch.return_value = "main"

        def branch_exists_side_effect(branch_name):
            return branch_name != "develop"  # develop doesn't exist

        git_mock.branch_exists.side_effect = branch_exists_side_effect
        git_mock.has_remote.return_value = False
        mock_git_manager.return_value = git_mock

        runner = CliRunner()
        result = runner.invoke(finish, input="y\n")

        assert result.exit_code == 0

        # Verify final checkout is to main (integration branch)
        checkout_calls = git_mock.checkout_branch.call_args_list
        assert checkout_calls[-1][0] == ("main",)  # Final checkout should be main
        assert "✓ Switched to main branch" in result.output

    @patch("grm.cli.GitManager")
    def test_finish_command_push_prompt_with_remote_accept(self, mock_git_manager):
        """Test finish command push prompt when remote exists and user accepts."""
        git_mock = Mock()
        git_mock.is_working_directory_clean.return_value = True
        git_mock.get_current_branch_name.return_value = "release/1.2.0"
        git_mock.get_integration_branch.return_value = "main"
        git_mock.branch_exists.return_value = True  # develop exists
        git_mock.has_remote.return_value = True
        mock_git_manager.return_value = git_mock

        runner = CliRunner()
        result = runner.invoke(finish, input="y\ny\n")  # Yes to finish, Yes to push

        assert result.exit_code == 0
        assert "Push all changes to remote?" in result.output
        assert "Pushing changes to remote..." in result.output
        assert "✓ Pushed main" in result.output
        assert "✓ Pushed tag 1.2.0" in result.output
        assert "✓ Pushed develop" in result.output

        # Verify push operations
        git_mock.push_branch.assert_any_call("main")
        git_mock.push_branch.assert_any_call("develop")
        git_mock.repo.git.push.assert_called_with("origin", "--tags")

    @patch("grm.cli.GitManager")
    def test_finish_command_push_prompt_with_remote_decline(self, mock_git_manager):
        """Test finish command push prompt when remote exists and user declines."""
        git_mock = Mock()
        git_mock.is_working_directory_clean.return_value = True
        git_mock.get_current_branch_name.return_value = "release/1.2.0"
        git_mock.get_integration_branch.return_value = "main"
        git_mock.branch_exists.return_value = False  # no develop
        git_mock.has_remote.return_value = True
        mock_git_manager.return_value = git_mock

        runner = CliRunner()
        result = runner.invoke(finish, input="y\nn\n")  # Yes to finish, No to push

        assert result.exit_code == 0
        assert "Push all changes to remote?" in result.output
        assert "Skipped pushing to remote" in result.output

        # Verify no push operations occurred
        git_mock.push_branch.assert_not_called()
        git_mock.repo.git.push.assert_not_called()

    @patch("grm.cli.GitManager")
    def test_finish_command_no_push_prompt_without_remote(self, mock_git_manager):
        """Test finish command doesn't prompt for push when no remote exists."""
        git_mock = Mock()
        git_mock.is_working_directory_clean.return_value = True
        git_mock.get_current_branch_name.return_value = "release/1.2.0"
        git_mock.get_integration_branch.return_value = "main"
        git_mock.branch_exists.return_value = False
        git_mock.has_remote.return_value = False  # No remote
        mock_git_manager.return_value = git_mock

        runner = CliRunner()
        result = runner.invoke(finish, input="y\n")  # Only yes to finish

        assert result.exit_code == 0
        assert "Push all changes to remote?" not in result.output
        assert "Pushing changes to remote..." not in result.output

        # Verify no push operations occurred
        git_mock.push_branch.assert_not_called()

    @patch("grm.cli.GitManager")
    def test_finish_command_push_failure_handling(self, mock_git_manager):
        """Test finish command handles push failures gracefully."""
        git_mock = Mock()
        git_mock.is_working_directory_clean.return_value = True
        git_mock.get_current_branch_name.return_value = "release/1.2.0"
        git_mock.get_integration_branch.return_value = "main"
        git_mock.branch_exists.return_value = False
        git_mock.has_remote.return_value = True
        git_mock.push_branch.side_effect = GitOperationError("Push failed")
        mock_git_manager.return_value = git_mock

        runner = CliRunner()
        result = runner.invoke(finish, input="y\ny\n")  # Yes to finish, Yes to push

        assert result.exit_code == 0  # Should not fail despite push error
        assert "Failed to push some changes: Push failed" in result.output
        assert "You may need to push manually" in result.output

    @patch("grm.cli.GitManager")
    def test_finish_command_push_only_existing_branches(self, mock_git_manager):
        """Test finish command only pushes branches that exist."""
        git_mock = Mock()
        git_mock.is_working_directory_clean.return_value = True
        git_mock.get_current_branch_name.return_value = "release/1.2.0"
        git_mock.get_integration_branch.return_value = "main"

        def branch_exists_side_effect(branch_name):
            return branch_name != "develop"  # Only main exists, no develop

        git_mock.branch_exists.side_effect = branch_exists_side_effect
        git_mock.has_remote.return_value = True
        mock_git_manager.return_value = git_mock

        runner = CliRunner()
        result = runner.invoke(finish, input="y\ny\n")  # Yes to finish, Yes to push

        assert result.exit_code == 0
        assert "✓ Pushed main" in result.output
        assert "✓ Pushed develop" not in result.output  # develop doesn't exist

        # Verify only main was pushed, not develop
        git_mock.push_branch.assert_called_once_with("main")

    def test_prompt_for_bump_type_minor(self):
        """Test prompting for bump type - minor selected."""
        from grm.cli import _prompt_for_bump_type
        from grm.version_manager import VersionManager

        version_manager = VersionManager(["1.0.0"])

        with patch("click.prompt", return_value="m"):
            result = _prompt_for_bump_type(version_manager)
            assert result == "minor"

    def test_prompt_for_bump_type_default(self):
        """Test prompting for bump type - default (Enter) selects minor."""
        from grm.cli import _prompt_for_bump_type
        from grm.version_manager import VersionManager

        version_manager = VersionManager(["1.0.0"])

        # Empty string simulates pressing Enter with default value
        with patch("click.prompt", return_value=""):
            result = _prompt_for_bump_type(version_manager)
            assert result == "minor"

    def test_prompt_for_bump_type_patch(self):
        """Test prompting for bump type - patch selected."""
        from grm.cli import _prompt_for_bump_type
        from grm.version_manager import VersionManager

        version_manager = VersionManager(["1.0.0"])

        with patch("click.prompt", return_value="p"):
            result = _prompt_for_bump_type(version_manager)
            assert result == "patch"

    def test_prompt_for_bump_type_invalid_then_valid(self):
        """Test prompting for bump type with invalid then valid input."""
        from grm.cli import _prompt_for_bump_type
        from grm.version_manager import VersionManager

        version_manager = VersionManager(["1.0.0"])

        with patch("click.prompt", side_effect=["invalid", "x", "m"]):
            result = _prompt_for_bump_type(version_manager)
            assert result == "minor"
