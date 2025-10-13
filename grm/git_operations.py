"""Git operations wrapper for GRM."""

import os
from typing import List, Optional, Tuple
import git
from git import Repo, InvalidGitRepositoryError


class GitOperationError(Exception):
    """Exception raised for Git operation errors."""

    pass


class GitManager:
    """Manages Git operations for release management."""

    def __init__(self, repo_path: str = "."):
        """Initialize GitManager with repository path.

        Args:
            repo_path: Path to the Git repository

        Raises:
            GitOperationError: If the path is not a valid Git repository
        """
        try:
            self.repo = Repo(repo_path)
        except InvalidGitRepositoryError:
            raise GitOperationError(f"'{repo_path}' is not a valid Git repository")

    def is_working_directory_clean(self) -> bool:
        """Check if working directory has no uncommitted changes.

        Returns:
            True if working directory is clean, False otherwise
        """
        return not self.repo.is_dirty(untracked_files=True)

    def get_integration_branch(self) -> str:
        """Detect the integration branch (main or master).

        Returns:
            'main' if it exists, otherwise 'master'

        Raises:
            GitOperationError: If neither main nor master branch exists
        """
        branches = [branch.name for branch in self.repo.branches]

        if "main" in branches:
            return "main"
        elif "master" in branches:
            return "master"
        else:
            raise GitOperationError("Neither 'main' nor 'master' branch found")

    def get_release_source_branch(self) -> str:
        """Detect the branch from which releases should be created.

        Returns:
            'develop' if it exists, otherwise the integration branch (main or master)

        Raises:
            GitOperationError: If neither main nor master branch exists
        """
        branches = [branch.name for branch in self.repo.branches]

        if "develop" in branches:
            return "develop"
        else:
            return self.get_integration_branch()

    def get_all_tags(self) -> List[str]:
        """Get all tags from the repository.

        Returns:
            List of tag names
        """
        return [tag.name for tag in self.repo.tags]

    def get_current_branch_name(self) -> str:
        """Get the name of the current branch.

        Returns:
            Current branch name

        Raises:
            GitOperationError: If unable to determine current branch
        """
        try:
            return self.repo.active_branch.name
        except TypeError:
            raise GitOperationError(
                "Unable to determine current branch (detached HEAD?)"
            )

    def create_branch(self, branch_name: str, checkout: bool = True) -> None:
        """Create a new branch.

        Args:
            branch_name: Name of the branch to create
            checkout: Whether to checkout the new branch immediately

        Raises:
            GitOperationError: If branch creation fails
        """
        try:
            new_branch = self.repo.create_head(branch_name)
            if checkout:
                new_branch.checkout()
        except Exception as e:
            raise GitOperationError(f"Failed to create branch '{branch_name}': {e}")

    def checkout_branch(self, branch_name: str) -> None:
        """Checkout an existing branch.

        Args:
            branch_name: Name of the branch to checkout

        Raises:
            GitOperationError: If checkout fails
        """
        try:
            self.repo.heads[branch_name].checkout()
        except Exception as e:
            raise GitOperationError(f"Failed to checkout branch '{branch_name}': {e}")

    def commit_changes(self, message: str, files: Optional[List[str]] = None) -> None:
        """Commit changes to the repository.

        Args:
            message: Commit message
            files: List of files to stage. If None, stages all changes

        Raises:
            GitOperationError: If commit fails
        """
        try:
            if files:
                self.repo.index.add(files)
            else:
                self.repo.git.add(A=True)

            self.repo.index.commit(message)
        except Exception as e:
            raise GitOperationError(f"Failed to commit changes: {e}")

    def merge_branch(
        self, branch_name: str, commit_message: str, no_ff: bool = True
    ) -> None:
        """Merge a branch into the current branch.

        Args:
            branch_name: Name of the branch to merge
            commit_message: Message for the merge commit
            no_ff: Force creation of merge commit (no fast-forward)

        Raises:
            GitOperationError: If merge fails
        """
        try:
            if no_ff:
                self.repo.git.merge(branch_name, no_ff=True, m=commit_message)
            else:
                self.repo.git.merge(branch_name, m=commit_message)
        except Exception as e:
            raise GitOperationError(f"Failed to merge branch '{branch_name}': {e}")

    def create_tag(self, tag_name: str, message: Optional[str] = None) -> None:
        """Create a tag at the current commit.

        Args:
            tag_name: Name of the tag
            message: Optional tag message for annotated tag

        Raises:
            GitOperationError: If tag creation fails
        """
        try:
            if message:
                self.repo.create_tag(tag_name, message=message)
            else:
                self.repo.create_tag(tag_name)
        except Exception as e:
            raise GitOperationError(f"Failed to create tag '{tag_name}': {e}")

    def delete_branch(
        self, branch_name: str, force: bool = False, delete_remote: bool = False
    ) -> None:
        """Delete a local branch and optionally the remote branch.

        Args:
            branch_name: Name of the branch to delete
            force: Force deletion even if not fully merged
            delete_remote: Also delete the remote branch if it exists

        Raises:
            GitOperationError: If branch deletion fails
        """
        try:
            # Delete local branch
            if force:
                self.repo.git.branch(branch_name, D=True)
            else:
                self.repo.git.branch(branch_name, d=True)

            # Delete remote branch if requested
            if delete_remote:
                try:
                    # Check if remote branch exists
                    remote_branches = [ref.name for ref in self.repo.remote().refs]
                    remote_branch_name = f"origin/{branch_name}"

                    if remote_branch_name in remote_branches:
                        self.repo.git.push("origin", "--delete", branch_name)
                except Exception as remote_error:
                    # Don't fail if remote deletion fails, just warn
                    raise GitOperationError(
                        f"Local branch deleted but failed to delete remote branch: {remote_error}"
                    )

        except Exception as e:
            raise GitOperationError(f"Failed to delete branch '{branch_name}': {e}")

    def branch_exists(self, branch_name: str) -> bool:
        """Check if a branch exists.

        Args:
            branch_name: Name of the branch to check

        Returns:
            True if branch exists, False otherwise
        """
        return branch_name in [branch.name for branch in self.repo.branches]

    def get_branch_commit_count(self, branch_name: str, base_branch: str) -> int:
        """Get number of commits in branch_name that are not in base_branch.

        Args:
            branch_name: Name of the feature branch
            base_branch: Name of the base branch

        Returns:
            Number of commits ahead
        """
        try:
            commits = list(self.repo.iter_commits(f"{base_branch}..{branch_name}"))
            return len(commits)
        except Exception:
            return 0

    def push_branch(
        self, branch_name: Optional[str] = None, set_upstream: bool = False
    ) -> None:
        """Push a branch to remote.

        Args:
            branch_name: Name of the branch to push. If None, pushes current branch
            set_upstream: Set upstream tracking for the branch

        Raises:
            GitOperationError: If push fails
        """
        try:
            if branch_name is None:
                branch_name = self.get_current_branch_name()

            if set_upstream:
                self.repo.git.push("--set-upstream", "origin", branch_name)
            else:
                self.repo.git.push("origin", branch_name)
        except Exception as e:
            raise GitOperationError(f"Failed to push branch '{branch_name}': {e}")

    def pull_branch(self, branch_name: Optional[str] = None) -> None:
        """Pull latest changes from remote for a branch.

        Args:
            branch_name: Name of the branch to pull. If None, pulls current branch

        Raises:
            GitOperationError: If pull fails
        """
        try:
            if branch_name is None:
                branch_name = self.get_current_branch_name()

            self.repo.git.pull("origin", branch_name)
        except Exception as e:
            raise GitOperationError(f"Failed to pull branch '{branch_name}': {e}")

    def has_remote(self) -> bool:
        """Check if repository has a remote configured.

        Returns:
            True if remote exists, False otherwise
        """
        try:
            return len(self.repo.remotes) > 0
        except Exception:
            return False
