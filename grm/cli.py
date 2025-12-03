"""Main CLI interface for GRM (Git Release Manager)."""

from typing import Optional

import click

from .git_operations import GitManager, GitOperationError
from .version_manager import VersionManager
from .changelog import ChangelogManager, ChangelogError
from .utils import (
    error_exit,
    success_message,
    warning_message,
    info_message,
    confirm_action,
)


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """GRM - Git Release Manager

    A CLI tool for managing Git releases with strict commit messages and changelog updates.
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command("r")
@click.option(
    "-m",
    "--minor",
    "bump_type",
    flag_value="minor",
    help="Create a minor version bump (X.Y+1.0)",
)
@click.option(
    "-p",
    "--patch",
    "bump_type",
    flag_value="patch",
    help="Create a patch version bump (X.Y.Z+1)",
)
@click.option(
    "-M",
    "--major",
    "bump_type",
    flag_value="major",
    help="Create a major version bump (X+1.0.0)",
)
def release(bump_type: Optional[str]):
    """Create a new release branch."""

    try:
        # Initialize managers
        git_manager = GitManager()
        changelog_manager = ChangelogManager()

        # Validate preconditions
        _validate_release_preconditions(git_manager, changelog_manager)

        # Get version information
        tags = git_manager.get_all_tags()
        version_manager = VersionManager(tags)

        # Check for mismatch between changelog and tags
        try:
            changelog_versions = changelog_manager.get_version_sections()
            if changelog_versions and len(changelog_versions) > 0:
                latest_changelog_version = changelog_versions[0][0]
                latest_tag_version = version_manager.get_latest_version()
                if latest_tag_version and str(latest_tag_version) != latest_changelog_version:
                    error_exit(
                        f"Version mismatch: CHANGELOG.md has {latest_changelog_version}, "
                        f"but latest git tag is {latest_tag_version}"
                    )
        except (TypeError, IndexError):
            pass

        # Determine version bump
        if bump_type is None:
            bump_type = _prompt_for_bump_type(version_manager)

        new_version = version_manager.suggest_version(bump_type)

        # Confirm version
        if not confirm_action(f"Create release {new_version}?", default=True):
            info_message("Release creation cancelled.")
            return

        # Create release branch
        release_branch_name = f"release/{new_version}"
        info_message(f"Creating release branch: {release_branch_name}")
        git_manager.create_branch(release_branch_name, checkout=True)

        # Update changelog
        info_message("Updating CHANGELOG.md...")
        changelog_manager.move_unreleased_to_version(str(new_version))

        # Stage and commit changelog
        info_message("Committing changelog changes...")
        git_manager.commit_changes("Changelog", files=["CHANGELOG.md"])

        # Push release branch to remote if remote exists
        if git_manager.has_remote():
            info_message("Pushing release branch to remote...")
            try:
                git_manager.push_branch(release_branch_name, set_upstream=True)
                info_message(f"✓ Pushed {release_branch_name} to remote")
            except GitOperationError as e:
                warning_message(f"Failed to push release branch: {e}")
                warning_message("You may need to push manually")

        success_message(
            f"✓ Release branch '{release_branch_name}' created successfully!"
        )
        info_message("Next steps:")
        info_message("  1. Review the changes in CHANGELOG.md")
        info_message("  2. When ready, run: grm f")

    except (GitOperationError, ChangelogError, ValueError) as e:
        error_exit(str(e))
    except KeyboardInterrupt:
        error_exit("Operation cancelled by user")


@cli.command("f")
def finish():
    """Finish the current release."""

    try:
        # Initialize managers
        git_manager = GitManager()

        # Validate preconditions
        _validate_finish_preconditions(git_manager)

        # Get current branch and extract version
        current_branch = git_manager.get_current_branch_name()
        if not current_branch.startswith("release/"):
            error_exit(f"Current branch '{current_branch}' is not a release branch")

        version = current_branch.replace("release/", "")
        integration_branch = git_manager.get_integration_branch()

        info_message(f"Finishing release {version}...")

        # Confirm the action
        if not confirm_action(f"Finish release {version}?", default=True):
            info_message("Release finish cancelled.")
            return

        commit_message = f"Finish {version}"

        # Merge to integration branch (main/master)
        info_message(f"Merging to {integration_branch}...")
        git_manager.checkout_branch(integration_branch)
        
        # Pull latest changes from remote before merging
        if git_manager.has_remote():
            info_message(f"Pulling latest changes from {integration_branch}...")
            try:
                git_manager.pull_branch(integration_branch)
                success_message(f"✓ Pulled latest changes from {integration_branch}")
            except GitOperationError as e:
                warning_message(f"Failed to pull latest changes: {e}")
                if not confirm_action("Continue with merge anyway?", default=False):
                    error_exit("Release finish cancelled.")
        
        git_manager.merge_branch(current_branch, commit_message, no_ff=True)

        # Create tag
        info_message(f"Creating tag {version}...")
        git_manager.create_tag(version)

        # Merge back to develop if it exists
        if git_manager.branch_exists("develop"):
            info_message("Merging back to develop...")
            git_manager.checkout_branch("develop")
            
            # Pull latest changes from remote before merging
            if git_manager.has_remote():
                info_message(f"Pulling latest changes from develop...")
                try:
                    git_manager.pull_branch("develop")
                    success_message(f"✓ Pulled latest changes from develop")
                except GitOperationError as e:
                    warning_message(f"Failed to pull latest changes from develop: {e}")
                    if not confirm_action("Continue with merge anyway?", default=False):
                        error_exit("Release finish cancelled.")
            
            git_manager.merge_branch(integration_branch, commit_message, no_ff=True)
        else:
            warning_message("No 'develop' branch found, skipping merge back")

        # Delete release branch (local and remote)
        info_message(f"Deleting release branch {current_branch}...")
        try:
            has_remote = git_manager.has_remote()
            git_manager.delete_branch(
                current_branch, force=False, delete_remote=has_remote
            )
            if has_remote:
                info_message("✓ Deleted both local and remote release branch")
            else:
                info_message("✓ Deleted local release branch (no remote configured)")
        except GitOperationError as e:
            if "Local branch deleted but failed to delete remote branch" in str(e):
                warning_message(
                    "Local branch deleted but remote branch deletion failed"
                )
                warning_message("You may need to delete the remote branch manually")
            else:
                raise

        success_message(f"✓ Release {version} finished successfully!")
        info_message("Summary:")
        info_message(f"  • Merged release/{version} to {integration_branch}")
        info_message(f"  • Created tag {version}")
        if git_manager.branch_exists("develop"):
            info_message(f"  • Merged {integration_branch} back to develop")
        info_message("  • Deleted release branch")

        # Push changes to remote if remote exists
        has_remote = git_manager.has_remote()
        if has_remote:
            info_message("Pushing changes to remote...")
            try:
                # Push integration branch
                git_manager.push_branch(integration_branch)
                info_message(f"✓ Pushed {integration_branch}")

                # Push tag
                git_manager.repo.git.push("origin", "--tags")
                info_message(f"✓ Pushed tag {version}")

                # Push develop if it exists
                if git_manager.branch_exists("develop"):
                    git_manager.push_branch("develop")
                    info_message("✓ Pushed develop")

            except GitOperationError as e:
                warning_message(f"Failed to push some changes: {e}")
                warning_message("You may need to push manually")

        # Switch to develop branch if it exists, otherwise stay on integration branch
        if git_manager.branch_exists("develop"):
            git_manager.checkout_branch("develop")
            info_message("✓ Switched to develop branch")
        else:
            git_manager.checkout_branch(integration_branch)
            info_message(f"✓ Switched to {integration_branch} branch")

    except (GitOperationError, ValueError) as e:
        error_exit(str(e))
    except KeyboardInterrupt:
        error_exit("Operation cancelled by user")


def _validate_release_preconditions(
    git_manager: GitManager, changelog_manager: ChangelogManager
):
    """Validate preconditions for creating a release."""

    # Check for uncommitted changes
    if not git_manager.is_working_directory_clean():
        error_exit(
            "Working directory has uncommitted changes. Please commit or stash them first."
        )

    # Ensure we're on the correct branch for creating releases
    release_source_branch = git_manager.get_release_source_branch()
    current_branch = git_manager.get_current_branch_name()

    if current_branch != release_source_branch:
        # Check if develop branch exists and we're not on it
        if release_source_branch == "develop" and git_manager.branch_exists("develop"):
            # Offer to checkout to develop and continue
            warning_message(
                f"Currently on '{current_branch}' branch, but releases must be created from '{release_source_branch}'."
            )
            if confirm_action(f"Switch to '{release_source_branch}' branch and continue?", default=True):
                info_message(f"Checking out '{release_source_branch}' branch...")
                git_manager.checkout_branch(release_source_branch)
                success_message(f"✓ Switched to '{release_source_branch}' branch")
                
                # Pull latest changes if remote exists
                if git_manager.has_remote():
                    info_message(f"Pulling latest changes from remote...")
                    try:
                        git_manager.pull_branch(release_source_branch)
                        success_message(f"✓ Pulled latest changes")
                    except GitOperationError as e:
                        warning_message(f"Failed to pull latest changes: {e}")
                        warning_message("Continuing with local version")
            else:
                error_exit("Release creation cancelled.")
        else:
            error_exit(
                f"Must be on '{release_source_branch}' branch to create a release. "
                f"Currently on '{current_branch}'."
            )

    # Create changelog if it doesn't exist
    if not changelog_manager.changelog_exists():
        if confirm_action("CHANGELOG.md not found. Create it?", default=True):
            changelog_manager.create_initial_changelog()
            info_message("Created CHANGELOG.md with initial structure")
        else:
            error_exit("CHANGELOG.md is required for release management")

    # Validate changelog format
    issues = changelog_manager.validate_changelog_format()
    if issues:
        error_exit("CHANGELOG.md format issues:\n  • " + "\n  • ".join(issues))

    # Check if there's content to release
    if not changelog_manager.has_unreleased_content():
        warning_message("No unreleased content found in CHANGELOG.md")
        if not confirm_action("Continue anyway?", default=False):
            error_exit("Release cancelled - no content to release")


def _validate_finish_preconditions(git_manager: GitManager):
    """Validate preconditions for finishing a release."""

    # Check for uncommitted changes
    if not git_manager.is_working_directory_clean():
        error_exit(
            "Working directory has uncommitted changes. Please commit or stash them first."
        )

    # Ensure we're on a release branch
    current_branch = git_manager.get_current_branch_name()
    if not current_branch.startswith("release/"):
        error_exit(
            f"Must be on a release branch to finish. Currently on '{current_branch}'."
        )


def _prompt_for_bump_type(version_manager: VersionManager) -> str:
    """Prompt user for version bump type."""

    latest_version = version_manager.get_latest_version()

    if latest_version:
        click.echo(f"Last version is {latest_version}.")
    else:
        click.echo("No previous versions found.")

    click.echo("Choose bump type:")

    next_minor = version_manager.get_next_minor_version()
    next_patch = version_manager.get_next_patch_version()
    next_major = version_manager.get_next_major_version()

    click.echo(f"  [m]inor → {next_minor}")
    click.echo(f"  [p]atch → {next_patch}")
    click.echo(f"  [M]ajor → {next_major}")

    while True:
        choice = click.prompt("(minor default)", type=str, default="m", show_default=False).strip()
        if choice in ["M"] or choice.lower() == "major":
            return "major"
        elif choice.lower() in ["p", "patch"]:
            return "patch"
        elif choice.lower() in ["m", "minor", ""]:
            return "minor"
        else:
            click.echo("Please enter 'm' for minor, 'p' for patch, or 'M' for major.")


def main():
    """Entry point for the GRM CLI."""
    try:
        cli()
    except Exception as e:
        error_exit(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
