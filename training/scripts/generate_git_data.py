#!/usr/bin/env python3
"""
Generate training data for Git & Version Control domain.
Target: ~300 examples

Distribution:
- 70% tasks, 30% concepts
- 70% advanced, 30% beginner  
- 40% include error/recovery scenarios
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Any

DATA_DIR = Path(__file__).parent.parent / "data"

def save_jsonl(data: List[Dict], filename: str):
    """Save data as JSONL file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    filepath = DATA_DIR / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    print(f"Saved {len(data)} examples to {filepath}")


# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

TOOL_SYSTEM = """You are AJ, an AI assistant that selects the appropriate tool for tasks.

Available tools:
- scan_workspace: Scan and index files in workspace
- read_file: Read contents of a file (params: file_path)
- write_file: Write/create a file (params: file_path, content)
- execute_shell: Run shell command locally (params: cmd)
- remote_execute: Execute command on remote agent (params: agent_name, command)
- list_agents: Discover available FunnelCloud agents
- complete: Task is finished
- none: No action needed

Respond with a JSON object containing 'tool' and 'params'."""

PLANNING_SYSTEM = """You are AJ, an AI assistant that breaks down tasks into steps.

Given a user task, create a plan with 2-5 concrete steps. Each step should be:
- Specific and actionable
- Verifiable (you can check if it succeeded)
- Sequential (later steps may depend on earlier ones)

Respond with a JSON object containing 'steps' (array of strings) and 'reasoning'."""

CONCEPT_SYSTEM = """You are an expert in Git version control and collaborative development workflows. Answer questions accurately and thoroughly, providing practical examples where helpful."""

GUARDRAIL_SYSTEM = """You are AJ, an AI assistant with safety guardrails.

You must:
- Never execute commands without verifying preconditions
- Stop if you detect you're in a loop (same action 2+ times)
- Report errors gracefully instead of retrying indefinitely
- Never fabricate results - if something fails, say so

Analyze the situation and respond appropriately."""


# =============================================================================
# TASK EXAMPLES - Tool Selection (execute_shell with git commands)
# =============================================================================

BASIC_GIT_TASKS = [
    # Init and setup
    ("Initialize a new git repository in the current directory", 
     {"tool": "execute_shell", "params": {"cmd": "git init"}}),
    ("Initialize a bare git repository",
     {"tool": "execute_shell", "params": {"cmd": "git init --bare"}}),
    ("Set my git username globally",
     {"tool": "execute_shell", "params": {"cmd": "git config --global user.name 'Your Name'"}}),
    ("Set my git email globally",
     {"tool": "execute_shell", "params": {"cmd": "git config --global user.email 'you@example.com'"}}),
    ("Show my git configuration",
     {"tool": "execute_shell", "params": {"cmd": "git config --list"}}),
    ("Set the default branch name to main",
     {"tool": "execute_shell", "params": {"cmd": "git config --global init.defaultBranch main"}}),
    
    # Status and info
    ("Show the current git status",
     {"tool": "execute_shell", "params": {"cmd": "git status"}}),
    ("Show git status in short format",
     {"tool": "execute_shell", "params": {"cmd": "git status -s"}}),
    ("Show which remote repositories are configured",
     {"tool": "execute_shell", "params": {"cmd": "git remote -v"}}),
    ("Show the current branch name",
     {"tool": "execute_shell", "params": {"cmd": "git branch --show-current"}}),
    ("Show the HEAD commit hash",
     {"tool": "execute_shell", "params": {"cmd": "git rev-parse HEAD"}}),
    ("Count the total number of commits",
     {"tool": "execute_shell", "params": {"cmd": "git rev-list --count HEAD"}}),
    
    # Adding files
    ("Add all changed files to staging",
     {"tool": "execute_shell", "params": {"cmd": "git add ."}}),
    ("Add a specific file to staging",
     {"tool": "execute_shell", "params": {"cmd": "git add path/to/file.py"}}),
    ("Add all Python files to staging",
     {"tool": "execute_shell", "params": {"cmd": "git add '*.py'"}}),
    ("Interactively add changes",
     {"tool": "execute_shell", "params": {"cmd": "git add -p"}}),
    ("Add all changes including untracked files",
     {"tool": "execute_shell", "params": {"cmd": "git add -A"}}),
    ("Unstage a file",
     {"tool": "execute_shell", "params": {"cmd": "git reset HEAD path/to/file.py"}}),
    ("Unstage all staged files",
     {"tool": "execute_shell", "params": {"cmd": "git reset HEAD"}}),
    
    # Committing
    ("Commit the staged changes with message 'Initial commit'",
     {"tool": "execute_shell", "params": {"cmd": "git commit -m 'Initial commit'"}}),
    ("Commit with a multi-line message",
     {"tool": "execute_shell", "params": {"cmd": "git commit -m 'Title' -m 'Detailed description'"}}),
    ("Commit all tracked changes without staging first",
     {"tool": "execute_shell", "params": {"cmd": "git commit -am 'Quick commit'"}}),
    ("Create an empty commit",
     {"tool": "execute_shell", "params": {"cmd": "git commit --allow-empty -m 'Trigger CI build'"}}),
    ("Commit with a specific date",
     {"tool": "execute_shell", "params": {"cmd": "git commit -m 'Backdated commit' --date='2024-01-15 10:00:00'"}}),
    
    # Viewing history
    ("Show the git log",
     {"tool": "execute_shell", "params": {"cmd": "git log --oneline -10"}}),
    ("Show the last 5 commits with details",
     {"tool": "execute_shell", "params": {"cmd": "git log -5 --stat"}}),
    ("Show commits in a pretty one-line format",
     {"tool": "execute_shell", "params": {"cmd": "git log --pretty=format:'%h %s (%an, %ar)' -10"}}),
    ("Show commits with graph visualization",
     {"tool": "execute_shell", "params": {"cmd": "git log --oneline --graph --all"}}),
    ("Show commits from a specific author",
     {"tool": "execute_shell", "params": {"cmd": "git log --author='John' -10"}}),
    ("Show commits from the last week",
     {"tool": "execute_shell", "params": {"cmd": "git log --since='1 week ago' --oneline"}}),
    ("Show commits that modified a specific file",
     {"tool": "execute_shell", "params": {"cmd": "git log --follow -- path/to/file.py"}}),
    ("Search commits by message content",
     {"tool": "execute_shell", "params": {"cmd": "git log --grep='bug fix' --oneline"}}),
    
    # Branches
    ("Create a new branch called 'feature/login'",
     {"tool": "execute_shell", "params": {"cmd": "git checkout -b feature/login"}}),
    ("Create a new branch using git switch",
     {"tool": "execute_shell", "params": {"cmd": "git switch -c feature/new-feature"}}),
    ("Switch to the main branch",
     {"tool": "execute_shell", "params": {"cmd": "git checkout main"}}),
    ("Switch to main using git switch",
     {"tool": "execute_shell", "params": {"cmd": "git switch main"}}),
    ("List all branches",
     {"tool": "execute_shell", "params": {"cmd": "git branch -a"}}),
    ("List only local branches",
     {"tool": "execute_shell", "params": {"cmd": "git branch"}}),
    ("List only remote branches",
     {"tool": "execute_shell", "params": {"cmd": "git branch -r"}}),
    ("Delete a local branch",
     {"tool": "execute_shell", "params": {"cmd": "git branch -d feature/old-branch"}}),
    ("Force delete a local branch",
     {"tool": "execute_shell", "params": {"cmd": "git branch -D feature/abandoned"}}),
    ("Rename the current branch",
     {"tool": "execute_shell", "params": {"cmd": "git branch -m new-name"}}),
    ("List branches sorted by last commit date",
     {"tool": "execute_shell", "params": {"cmd": "git branch --sort=-committerdate"}}),
    
    # Push and pull
    ("Push the current branch to origin",
     {"tool": "execute_shell", "params": {"cmd": "git push origin HEAD"}}),
    ("Push and set upstream tracking",
     {"tool": "execute_shell", "params": {"cmd": "git push -u origin feature/my-feature"}}),
    ("Push all branches to origin",
     {"tool": "execute_shell", "params": {"cmd": "git push --all origin"}}),
    ("Push all tags to origin",
     {"tool": "execute_shell", "params": {"cmd": "git push --tags"}}),
    ("Pull the latest changes from origin",
     {"tool": "execute_shell", "params": {"cmd": "git pull origin main"}}),
    ("Pull with rebase instead of merge",
     {"tool": "execute_shell", "params": {"cmd": "git pull --rebase origin main"}}),
    ("Fetch without merging",
     {"tool": "execute_shell", "params": {"cmd": "git fetch origin"}}),
    ("Fetch all remotes",
     {"tool": "execute_shell", "params": {"cmd": "git fetch --all"}}),
    ("Delete a remote branch",
     {"tool": "execute_shell", "params": {"cmd": "git push origin --delete feature/old-branch"}}),
    
    # Clone
    ("Clone the repository at https://github.com/user/repo.git",
     {"tool": "execute_shell", "params": {"cmd": "git clone https://github.com/user/repo.git"}}),
    ("Clone into a specific directory",
     {"tool": "execute_shell", "params": {"cmd": "git clone https://github.com/user/repo.git my-project"}}),
    ("Clone only the latest commit (shallow clone)",
     {"tool": "execute_shell", "params": {"cmd": "git clone --depth 1 https://github.com/user/repo.git"}}),
    ("Clone a specific branch",
     {"tool": "execute_shell", "params": {"cmd": "git clone -b develop https://github.com/user/repo.git"}}),
    ("Clone with submodules",
     {"tool": "execute_shell", "params": {"cmd": "git clone --recurse-submodules https://github.com/user/repo.git"}}),
    
    # Diff
    ("Show the diff of unstaged changes",
     {"tool": "execute_shell", "params": {"cmd": "git diff"}}),
    ("Show the diff of staged changes",
     {"tool": "execute_shell", "params": {"cmd": "git diff --staged"}}),
    ("Show diff between two branches",
     {"tool": "execute_shell", "params": {"cmd": "git diff main..feature/branch"}}),
    ("Show diff of a specific file",
     {"tool": "execute_shell", "params": {"cmd": "git diff path/to/file.py"}}),
    ("Show diff with word-level highlighting",
     {"tool": "execute_shell", "params": {"cmd": "git diff --word-diff"}}),
    ("Show only names of changed files",
     {"tool": "execute_shell", "params": {"cmd": "git diff --name-only"}}),
    ("Show diff statistics",
     {"tool": "execute_shell", "params": {"cmd": "git diff --stat"}}),
    
    # Discarding changes
    ("Discard all local changes",
     {"tool": "execute_shell", "params": {"cmd": "git checkout -- ."}}),
    ("Discard changes to a specific file",
     {"tool": "execute_shell", "params": {"cmd": "git checkout -- path/to/file.py"}}),
    ("Restore a file using git restore",
     {"tool": "execute_shell", "params": {"cmd": "git restore path/to/file.py"}}),
    ("Discard all changes and untracked files",
     {"tool": "execute_shell", "params": {"cmd": "git checkout -- . && git clean -fd"}}),
    
    # Remotes
    ("Add a new remote repository",
     {"tool": "execute_shell", "params": {"cmd": "git remote add upstream https://github.com/original/repo.git"}}),
    ("Remove a remote",
     {"tool": "execute_shell", "params": {"cmd": "git remote remove origin"}}),
    ("Rename a remote",
     {"tool": "execute_shell", "params": {"cmd": "git remote rename origin old-origin"}}),
    ("Change remote URL",
     {"tool": "execute_shell", "params": {"cmd": "git remote set-url origin https://github.com/user/new-repo.git"}}),
    ("Show detailed remote info",
     {"tool": "execute_shell", "params": {"cmd": "git remote show origin"}}),
]

ADVANCED_GIT_TASKS = [
    # Rebasing
    ("Rebase the current branch onto main",
     {"tool": "execute_shell", "params": {"cmd": "git rebase main"}}),
    ("Interactive rebase the last 5 commits",
     {"tool": "execute_shell", "params": {"cmd": "git rebase -i HEAD~5"}}),
    ("Rebase onto a specific commit",
     {"tool": "execute_shell", "params": {"cmd": "git rebase --onto main feature-base feature"}}),
    ("Continue rebase after resolving conflicts",
     {"tool": "execute_shell", "params": {"cmd": "git rebase --continue"}}),
    ("Abort an in-progress rebase",
     {"tool": "execute_shell", "params": {"cmd": "git rebase --abort"}}),
    ("Skip the current commit during rebase",
     {"tool": "execute_shell", "params": {"cmd": "git rebase --skip"}}),
    ("Rebase and autosquash fixup commits",
     {"tool": "execute_shell", "params": {"cmd": "git rebase -i --autosquash main"}}),
    
    # Cherry-pick
    ("Cherry-pick commit abc1234 onto the current branch",
     {"tool": "execute_shell", "params": {"cmd": "git cherry-pick abc1234"}}),
    ("Cherry-pick multiple commits",
     {"tool": "execute_shell", "params": {"cmd": "git cherry-pick abc1234 def5678 ghi9012"}}),
    ("Cherry-pick a range of commits",
     {"tool": "execute_shell", "params": {"cmd": "git cherry-pick abc1234^..def5678"}}),
    ("Cherry-pick without committing",
     {"tool": "execute_shell", "params": {"cmd": "git cherry-pick -n abc1234"}}),
    ("Cherry-pick with original commit reference",
     {"tool": "execute_shell", "params": {"cmd": "git cherry-pick -x abc1234"}}),
    ("Abort cherry-pick in progress",
     {"tool": "execute_shell", "params": {"cmd": "git cherry-pick --abort"}}),
    ("Continue cherry-pick after conflict resolution",
     {"tool": "execute_shell", "params": {"cmd": "git cherry-pick --continue"}}),
    
    # Stashing
    ("Stash the current changes with a message",
     {"tool": "execute_shell", "params": {"cmd": "git stash push -m 'WIP: feature work'"}}),
    ("Stash including untracked files",
     {"tool": "execute_shell", "params": {"cmd": "git stash push -u -m 'Include untracked'"}}),
    ("Stash only staged changes",
     {"tool": "execute_shell", "params": {"cmd": "git stash push --staged"}}),
    ("Apply the most recent stash",
     {"tool": "execute_shell", "params": {"cmd": "git stash pop"}}),
    ("Apply stash without removing it",
     {"tool": "execute_shell", "params": {"cmd": "git stash apply"}}),
    ("Apply a specific stash",
     {"tool": "execute_shell", "params": {"cmd": "git stash apply stash@{2}"}}),
    ("List all stashes",
     {"tool": "execute_shell", "params": {"cmd": "git stash list"}}),
    ("Show contents of a stash",
     {"tool": "execute_shell", "params": {"cmd": "git stash show -p stash@{0}"}}),
    ("Drop a specific stash",
     {"tool": "execute_shell", "params": {"cmd": "git stash drop stash@{1}"}}),
    ("Clear all stashes",
     {"tool": "execute_shell", "params": {"cmd": "git stash clear"}}),
    ("Create a branch from a stash",
     {"tool": "execute_shell", "params": {"cmd": "git stash branch feature-from-stash stash@{0}"}}),
    
    # Reset
    ("Reset to a specific commit but keep changes staged",
     {"tool": "execute_shell", "params": {"cmd": "git reset --soft HEAD~1"}}),
    ("Reset and unstage changes",
     {"tool": "execute_shell", "params": {"cmd": "git reset --mixed HEAD~1"}}),
    ("Hard reset to origin/main (discard all local changes)",
     {"tool": "execute_shell", "params": {"cmd": "git reset --hard origin/main"}}),
    ("Reset to a specific commit hash",
     {"tool": "execute_shell", "params": {"cmd": "git reset --hard abc1234"}}),
    ("Reset a single file to HEAD",
     {"tool": "execute_shell", "params": {"cmd": "git reset HEAD path/to/file.py"}}),
    ("Reset to the state before last merge",
     {"tool": "execute_shell", "params": {"cmd": "git reset --hard ORIG_HEAD"}}),
    
    # Reflog
    ("Show the reflog to find lost commits",
     {"tool": "execute_shell", "params": {"cmd": "git reflog"}}),
    ("Show reflog with dates",
     {"tool": "execute_shell", "params": {"cmd": "git reflog --date=iso"}}),
    ("Show reflog for a specific branch",
     {"tool": "execute_shell", "params": {"cmd": "git reflog show feature/my-branch"}}),
    ("Recover a commit using reflog",
     {"tool": "execute_shell", "params": {"cmd": "git checkout HEAD@{5}"}}),
    
    # Bisect
    ("Use git bisect to find a bug-introducing commit",
     {"tool": "execute_shell", "params": {"cmd": "git bisect start"}}),
    ("Mark current commit as bad in bisect",
     {"tool": "execute_shell", "params": {"cmd": "git bisect bad"}}),
    ("Mark a commit as good in bisect",
     {"tool": "execute_shell", "params": {"cmd": "git bisect good abc1234"}}),
    ("Run bisect with a test script",
     {"tool": "execute_shell", "params": {"cmd": "git bisect run npm test"}}),
    ("End bisect session",
     {"tool": "execute_shell", "params": {"cmd": "git bisect reset"}}),
    ("View bisect log",
     {"tool": "execute_shell", "params": {"cmd": "git bisect log"}}),
    
    # Tags
    ("Create an annotated tag v1.0.0",
     {"tool": "execute_shell", "params": {"cmd": "git tag -a v1.0.0 -m 'Release version 1.0.0'"}}),
    ("Create a lightweight tag",
     {"tool": "execute_shell", "params": {"cmd": "git tag v1.0.0-rc1"}}),
    ("Tag a specific commit",
     {"tool": "execute_shell", "params": {"cmd": "git tag -a v0.9.0 abc1234 -m 'Retroactive tag'"}}),
    ("List all tags",
     {"tool": "execute_shell", "params": {"cmd": "git tag -l"}}),
    ("List tags matching a pattern",
     {"tool": "execute_shell", "params": {"cmd": "git tag -l 'v1.*'"}}),
    ("Show tag information",
     {"tool": "execute_shell", "params": {"cmd": "git show v1.0.0"}}),
    ("Delete a local tag",
     {"tool": "execute_shell", "params": {"cmd": "git tag -d v1.0.0"}}),
    ("Delete a remote tag",
     {"tool": "execute_shell", "params": {"cmd": "git push origin --delete v1.0.0"}}),
    ("Push a specific tag",
     {"tool": "execute_shell", "params": {"cmd": "git push origin v1.0.0"}}),
    
    # Blame and history
    ("Find who last modified each line in a file",
     {"tool": "execute_shell", "params": {"cmd": "git blame src/main.py"}}),
    ("Blame with line range",
     {"tool": "execute_shell", "params": {"cmd": "git blame -L 10,20 src/main.py"}}),
    ("Blame ignoring whitespace changes",
     {"tool": "execute_shell", "params": {"cmd": "git blame -w src/main.py"}}),
    ("Show commits that changed a specific file",
     {"tool": "execute_shell", "params": {"cmd": "git log --follow -p -- path/to/file.py"}}),
    ("Show the commit that introduced a specific line",
     {"tool": "execute_shell", "params": {"cmd": "git log -S 'search_string' --oneline"}}),
    ("Find commits that changed a regex pattern",
     {"tool": "execute_shell", "params": {"cmd": "git log -G 'def.*function' --oneline"}}),
    ("Show file at a specific commit",
     {"tool": "execute_shell", "params": {"cmd": "git show abc1234:path/to/file.py"}}),
    
    # Clean
    ("Clean up untracked files and directories",
     {"tool": "execute_shell", "params": {"cmd": "git clean -fd"}}),
    ("Dry run clean (show what would be removed)",
     {"tool": "execute_shell", "params": {"cmd": "git clean -nd"}}),
    ("Clean including ignored files",
     {"tool": "execute_shell", "params": {"cmd": "git clean -fdx"}}),
    ("Interactive clean",
     {"tool": "execute_shell", "params": {"cmd": "git clean -i"}}),
    
    # Fetch and prune
    ("Fetch all remotes and prune deleted branches",
     {"tool": "execute_shell", "params": {"cmd": "git fetch --all --prune"}}),
    ("Prune remote-tracking branches",
     {"tool": "execute_shell", "params": {"cmd": "git remote prune origin"}}),
    ("Fetch with tags",
     {"tool": "execute_shell", "params": {"cmd": "git fetch --tags"}}),
    
    # Log variations
    ("Show the commit graph with branches",
     {"tool": "execute_shell", "params": {"cmd": "git log --oneline --graph --all --decorate"}}),
    ("Show commits between two refs",
     {"tool": "execute_shell", "params": {"cmd": "git log main..feature/branch --oneline"}}),
    ("Show commits unique to each branch",
     {"tool": "execute_shell", "params": {"cmd": "git log main...feature/branch --oneline"}}),
    ("Show merge commits only",
     {"tool": "execute_shell", "params": {"cmd": "git log --merges --oneline"}}),
    ("Show commits excluding merges",
     {"tool": "execute_shell", "params": {"cmd": "git log --no-merges --oneline"}}),
    
    # Amend and modify
    ("Amend the last commit message",
     {"tool": "execute_shell", "params": {"cmd": "git commit --amend -m 'Updated commit message'"}}),
    ("Add a file to the last commit without changing the message",
     {"tool": "execute_shell", "params": {"cmd": "git add forgotten_file.py && git commit --amend --no-edit"}}),
    ("Change author of last commit",
     {"tool": "execute_shell", "params": {"cmd": "git commit --amend --author='New Author <new@email.com>'"}}),
    ("Create a fixup commit for later squashing",
     {"tool": "execute_shell", "params": {"cmd": "git commit --fixup abc1234"}}),
    
    # Revert
    ("Revert a specific commit (creates new commit)",
     {"tool": "execute_shell", "params": {"cmd": "git revert abc1234"}}),
    ("Revert without auto-committing",
     {"tool": "execute_shell", "params": {"cmd": "git revert -n abc1234"}}),
    ("Revert a merge commit",
     {"tool": "execute_shell", "params": {"cmd": "git revert -m 1 abc1234"}}),
    ("Revert multiple commits",
     {"tool": "execute_shell", "params": {"cmd": "git revert abc1234..def5678"}}),
    
    # Branch info
    ("Show which branches contain a specific commit",
     {"tool": "execute_shell", "params": {"cmd": "git branch --contains abc1234"}}),
    ("Show branches merged into main",
     {"tool": "execute_shell", "params": {"cmd": "git branch --merged main"}}),
    ("Show branches not merged into main",
     {"tool": "execute_shell", "params": {"cmd": "git branch --no-merged main"}}),
    ("Show upstream tracking info",
     {"tool": "execute_shell", "params": {"cmd": "git branch -vv"}}),
    
    # Patches
    ("Create a patch file from the last commit",
     {"tool": "execute_shell", "params": {"cmd": "git format-patch -1 HEAD"}}),
    ("Create patches for last 3 commits",
     {"tool": "execute_shell", "params": {"cmd": "git format-patch -3"}}),
    ("Apply a patch file",
     {"tool": "execute_shell", "params": {"cmd": "git apply fix.patch"}}),
    ("Apply patches with git am",
     {"tool": "execute_shell", "params": {"cmd": "git am *.patch"}}),
    ("Check if patch applies cleanly",
     {"tool": "execute_shell", "params": {"cmd": "git apply --check fix.patch"}}),
    
    # Merge
    ("Merge a branch into current",
     {"tool": "execute_shell", "params": {"cmd": "git merge feature/branch"}}),
    ("Merge with no fast-forward",
     {"tool": "execute_shell", "params": {"cmd": "git merge --no-ff feature/branch"}}),
    ("Merge with squash",
     {"tool": "execute_shell", "params": {"cmd": "git merge --squash feature/branch"}}),
    ("Abort a merge in progress",
     {"tool": "execute_shell", "params": {"cmd": "git merge --abort"}}),
    ("Continue merge after resolving conflicts",
     {"tool": "execute_shell", "params": {"cmd": "git merge --continue"}}),
    ("Merge with specific strategy",
     {"tool": "execute_shell", "params": {"cmd": "git merge -X theirs feature/branch"}}),
    
    # Submodules
    ("Add a submodule",
     {"tool": "execute_shell", "params": {"cmd": "git submodule add https://github.com/user/lib.git libs/lib"}}),
    ("Initialize submodules after clone",
     {"tool": "execute_shell", "params": {"cmd": "git submodule update --init --recursive"}}),
    ("Update all submodules to latest",
     {"tool": "execute_shell", "params": {"cmd": "git submodule update --remote"}}),
    ("Show submodule status",
     {"tool": "execute_shell", "params": {"cmd": "git submodule status"}}),
    ("Remove a submodule",
     {"tool": "execute_shell", "params": {"cmd": "git submodule deinit libs/lib && git rm libs/lib"}}),
    
    # Worktrees
    ("Create a new worktree for a branch",
     {"tool": "execute_shell", "params": {"cmd": "git worktree add ../feature-worktree feature/branch"}}),
    ("List all worktrees",
     {"tool": "execute_shell", "params": {"cmd": "git worktree list"}}),
    ("Remove a worktree",
     {"tool": "execute_shell", "params": {"cmd": "git worktree remove ../feature-worktree"}}),
    ("Prune worktree info",
     {"tool": "execute_shell", "params": {"cmd": "git worktree prune"}}),
    
    # Archive and bundle
    ("Create a zip archive of the repo",
     {"tool": "execute_shell", "params": {"cmd": "git archive --format=zip HEAD > repo.zip"}}),
    ("Create a tarball of a specific tag",
     {"tool": "execute_shell", "params": {"cmd": "git archive --format=tar.gz v1.0.0 > release.tar.gz"}}),
    ("Create a bundle for offline transfer",
     {"tool": "execute_shell", "params": {"cmd": "git bundle create repo.bundle --all"}}),
    ("Clone from a bundle",
     {"tool": "execute_shell", "params": {"cmd": "git clone repo.bundle my-repo"}}),
    
    # Misc advanced
    ("Show short stats for repo",
     {"tool": "execute_shell", "params": {"cmd": "git shortlog -sn"}}),
    ("List files tracked by git",
     {"tool": "execute_shell", "params": {"cmd": "git ls-files"}}),
    ("Verify integrity of git objects",
     {"tool": "execute_shell", "params": {"cmd": "git fsck"}}),
    ("Run garbage collection",
     {"tool": "execute_shell", "params": {"cmd": "git gc"}}),
    ("Aggressive garbage collection",
     {"tool": "execute_shell", "params": {"cmd": "git gc --aggressive"}}),
    ("Show object info",
     {"tool": "execute_shell", "params": {"cmd": "git cat-file -p abc1234"}}),
    ("Count objects in repo",
     {"tool": "execute_shell", "params": {"cmd": "git count-objects -v"}}),
]

REMOTE_GIT_TASKS = [
    # Remote execution on Windows/Linux agents
    ("Check git status on the remote development server",
     {"tool": "remote_execute", "params": {"command": "git status", "agent_name": "dev-server"}}),
    ("Pull the latest code on the production server",
     {"tool": "remote_execute", "params": {"command": "git pull origin main", "agent_name": "prod-server"}}),
    ("Show recent commits on my Windows workstation",
     {"tool": "remote_execute", "params": {"command": "git log --oneline -10", "agent_name": "workstation"}}),
    ("Check if there are uncommitted changes on the build server",
     {"tool": "remote_execute", "params": {"command": "git status --porcelain", "agent_name": "build-server"}}),
]


# =============================================================================
# MULTI-STEP PLANNING EXAMPLES
# =============================================================================

PLANNING_TASKS = [
    # Basic workflows
    (
        "Create a new feature branch, make some changes, and push it for review",
        {
            "steps": [
                "Ensure you're on the main branch and it's up to date with 'git checkout main && git pull'",
                "Create and switch to a new feature branch with 'git checkout -b feature/new-feature'",
                "Make your code changes and stage them with 'git add .'",
                "Commit the changes with a descriptive message",
                "Push the branch to origin with 'git push -u origin feature/new-feature'"
            ],
            "reasoning": "This follows the feature branch workflow, keeping main clean while developing in isolation."
        }
    ),
    (
        "Set up GitFlow branching strategy for a new project",
        {
            "steps": [
                "Initialize the repository with 'git init' if not already done",
                "Create the main branch for production releases",
                "Create a develop branch from main with 'git checkout -b develop'",
                "Document the branching strategy (feature/*, release/*, hotfix/* naming conventions)",
                "Configure branch protection rules if using GitHub/GitLab"
            ],
            "reasoning": "GitFlow provides structured branching for teams with scheduled releases."
        }
    ),
    (
        "Resolve a merge conflict between feature branch and main",
        {
            "steps": [
                "Fetch the latest changes with 'git fetch origin'",
                "Checkout your feature branch and merge main into it: 'git merge origin/main'",
                "Identify conflicting files from the merge output",
                "Open each conflicting file and manually resolve the conflicts (choose or combine changes)",
                "Stage the resolved files with 'git add <resolved-files>'",
                "Complete the merge with 'git commit'"
            ],
            "reasoning": "Merging main into feature first allows you to resolve conflicts locally before the PR merge."
        }
    ),
    (
        "Use git bisect to find the commit that introduced a bug",
        {
            "steps": [
                "Start bisect with 'git bisect start'",
                "Mark the current commit as bad: 'git bisect bad'",
                "Mark a known good commit: 'git bisect good <commit-hash>'",
                "Test each commit git checks out and mark as 'git bisect good' or 'git bisect bad'",
                "When bisect identifies the culprit commit, note its hash",
                "End bisect with 'git bisect reset' to return to your original branch"
            ],
            "reasoning": "Binary search through commits efficiently finds the bug-introducing change in O(log n) tests."
        }
    ),
    (
        "Recover a commit that was accidentally reset/deleted",
        {
            "steps": [
                "Run 'git reflog' to see the history of HEAD movements",
                "Find the commit hash of the lost commit in the reflog",
                "Create a branch pointing to that commit: 'git branch recovered-work <commit-hash>'",
                "Verify the recovered content with 'git log recovered-work'",
                "Cherry-pick or merge the recovered commits as needed"
            ],
            "reasoning": "Git reflog keeps all HEAD movements for ~90 days, making most 'lost' commits recoverable."
        }
    ),
    # Advanced workflows
    (
        "Squash multiple commits into one before merging a PR",
        {
            "steps": [
                "Ensure your branch is up to date with main",
                "Count how many commits to squash (e.g., 5 commits)",
                "Run 'git rebase -i HEAD~5' to start interactive rebase",
                "Change 'pick' to 'squash' (or 's') for all commits except the first",
                "Save and close the editor, then write a comprehensive commit message",
                "Force push with 'git push --force-with-lease' (safer than --force)"
            ],
            "reasoning": "Squashing creates a clean history and makes it easier to revert the entire feature if needed."
        }
    ),
    (
        "Set up a Git hook to run tests before each commit",
        {
            "steps": [
                "Navigate to .git/hooks/ directory",
                "Create a file named 'pre-commit' (no extension)",
                "Add shebang and test command: #!/bin/sh\\nnpm test",
                "Make it executable with 'chmod +x .git/hooks/pre-commit'",
                "Test by making a commit - it should run tests first"
            ],
            "reasoning": "Pre-commit hooks catch issues early, before they enter the repository history."
        }
    ),
    (
        "Migrate a repository from SVN to Git while preserving history",
        {
            "steps": [
                "Create an authors file mapping SVN usernames to Git format",
                "Clone the SVN repo with 'git svn clone --authors-file=authors.txt <svn-url>'",
                "Convert SVN branches/tags to Git format",
                "Add the new Git remote with 'git remote add origin <git-url>'",
                "Push all branches and tags to the new Git remote"
            ],
            "reasoning": "git-svn preserves commit history and author information during migration."
        }
    ),
    (
        "Release a hotfix using GitFlow methodology",
        {
            "steps": [
                "Create hotfix branch from main: 'git checkout -b hotfix/1.0.1 main'",
                "Make the fix and commit with clear message describing the bug",
                "Merge hotfix into main: 'git checkout main && git merge hotfix/1.0.1'",
                "Tag the release: 'git tag -a v1.0.1 -m \"Hotfix release\"'",
                "Merge hotfix into develop: 'git checkout develop && git merge hotfix/1.0.1'",
                "Delete the hotfix branch: 'git branch -d hotfix/1.0.1'",
                "Push main, develop, and tags to origin"
            ],
            "reasoning": "Hotfixes go to both main (for release) and develop (to include in future releases)."
        }
    ),
    (
        "Clean up a repository with large files accidentally committed",
        {
            "steps": [
                "Identify large files with 'git rev-list --objects --all | git cat-file --batch-check'",
                "Install git-filter-repo (preferred) or use BFG Repo-Cleaner",
                "Run 'git filter-repo --strip-blobs-bigger-than 10M' to remove large files from history",
                "Add patterns to .gitignore to prevent re-adding large files",
                "Force push all branches: 'git push origin --force --all'",
                "Notify all collaborators to re-clone the repository"
            ],
            "reasoning": "Rewriting history requires all collaborators to re-clone to avoid merge issues."
        }
    ),
    # Trunk-based development
    (
        "Set up trunk-based development workflow",
        {
            "steps": [
                "Ensure main branch is protected with required reviews",
                "Configure short-lived feature branches naming: 'feature/<ticket>-<description>'",
                "Set up CI to run on every push to main and feature branches",
                "Enable feature flags for incomplete features: implement flag checks in code",
                "Create a branch from main: 'git checkout -b feature/TICK-123-add-login main'",
                "Keep branches short-lived (1-2 days max) by breaking features into small increments",
                "Merge frequently with 'git merge main' to stay current"
            ],
            "reasoning": "Trunk-based development reduces merge conflicts and enables continuous delivery."
        }
    ),
    # Monorepo setup
    (
        "Set up a monorepo structure for multiple services",
        {
            "steps": [
                "Create root directory structure: packages/, services/, libs/, tools/",
                "Initialize git: 'git init' and create main .gitignore",
                "Set up sparse checkout for developers who only need parts: 'git sparse-checkout init --cone'",
                "Configure workspace tools (yarn workspaces, npm workspaces, or nx)",
                "Create CODEOWNERS file mapping directories to team ownership",
                "Set up CI to detect changes and only build/test affected packages",
                "Document the monorepo conventions in CONTRIBUTING.md"
            ],
            "reasoning": "Monorepos enable code sharing and atomic cross-package changes while maintaining team ownership."
        }
    ),
    # Code review workflow
    (
        "Implement a comprehensive code review workflow",
        {
            "steps": [
                "Create feature branch from main: 'git checkout -b feature/add-user-auth'",
                "Make atomic commits with clear messages following conventional commits",
                "Push branch: 'git push -u origin feature/add-user-auth'",
                "Create pull request with description template (what, why, testing)",
                "Request reviewers and link related issues",
                "Address review feedback with fixup commits: 'git commit --fixup <sha>'",
                "After approval, squash fixups: 'git rebase -i --autosquash main'",
                "Merge via GitHub/GitLab merge button (squash or merge commit per team policy)"
            ],
            "reasoning": "Structured code reviews catch bugs early and spread knowledge across the team."
        }
    ),
    # Release management
    (
        "Create a release with semantic versioning",
        {
            "steps": [
                "Ensure main branch is stable and all tests pass",
                "Determine version bump based on changes (major/minor/patch)",
                "Create release branch: 'git checkout -b release/v2.0.0 main'",
                "Update version in package.json/pyproject.toml and CHANGELOG.md",
                "Commit version bump: 'git commit -am \"chore: bump version to 2.0.0\"'",
                "Create annotated tag: 'git tag -a v2.0.0 -m \"Release v2.0.0\"'",
                "Merge to main: 'git checkout main && git merge release/v2.0.0'",
                "Push with tags: 'git push origin main --tags'",
                "Merge back to develop if using GitFlow: 'git checkout develop && git merge main'"
            ],
            "reasoning": "Semantic versioning communicates change impact; tags provide immutable release points."
        }
    ),
    # Disaster recovery
    (
        "Recover from an accidental force push to main",
        {
            "steps": [
                "Don't panic - reflog and remote backups likely exist",
                "Check if any team member has the original commits locally",
                "If available locally: 'git checkout main && git reset --hard origin/main@{1}'",
                "Or use reflog: 'git reflog show origin/main' to find the pre-force-push state",
                "Restore with: 'git push origin <correct-commit-sha>:main --force-with-lease'",
                "If lost, contact Git hosting provider - they often have backups",
                "Add branch protection rules to prevent future incidents",
                "Post-mortem: document what happened and prevention measures"
            ],
            "reasoning": "Force pushes are rarely unrecoverable; reflog and collaboration usually save the day."
        }
    ),
    # Cherry-pick workflow
    (
        "Backport a bug fix to a release branch",
        {
            "steps": [
                "Identify the commit hash(es) that contain the fix on main",
                "Checkout the release branch: 'git checkout release/v1.x'",
                "Cherry-pick the fix: 'git cherry-pick -x <commit-hash>'",
                "The -x flag adds 'cherry picked from' message for traceability",
                "If conflicts occur, resolve them and continue: 'git cherry-pick --continue'",
                "Test thoroughly - backports can have unexpected interactions",
                "Push and tag new patch release: 'git tag v1.2.3' and 'git push origin release/v1.x --tags'"
            ],
            "reasoning": "Cherry-pick with -x maintains traceability between main and release branch fixes."
        }
    ),
    # Splitting commits
    (
        "Split a large commit into smaller logical commits",
        {
            "steps": [
                "Start interactive rebase: 'git rebase -i HEAD~1' (or more commits back)",
                "Change 'pick' to 'edit' for the commit you want to split",
                "When rebase stops, reset the commit: 'git reset HEAD~'",
                "Now stage and commit changes in logical groups:",
                "  'git add -p' to interactively select hunks",
                "  'git commit -m \"Part 1: Database schema changes\"'",
                "  Repeat for each logical group",
                "Continue rebase: 'git rebase --continue'",
                "Force push if branch was already pushed: 'git push --force-with-lease'"
            ],
            "reasoning": "Small, focused commits make reviews easier and simplify bisecting/reverting."
        }
    ),
    # Git worktree workflow
    (
        "Use git worktrees for parallel development",
        {
            "steps": [
                "List existing worktrees: 'git worktree list'",
                "Create worktree for hotfix: 'git worktree add ../project-hotfix hotfix/urgent-fix'",
                "Create worktree for feature: 'git worktree add ../project-feature feature/new-ui'",
                "Now you can work in both directories simultaneously without stashing",
                "Each worktree has its own working directory but shares .git database",
                "When done, remove worktree: 'git worktree remove ../project-hotfix'",
                "Prune stale worktrees: 'git worktree prune'"
            ],
            "reasoning": "Worktrees enable context-switching without stashing or committing WIP code."
        }
    ),
    # Handling submodules
    (
        "Add and update submodules in a project",
        {
            "steps": [
                "Add submodule: 'git submodule add https://github.com/lib/cool-lib.git libs/cool-lib'",
                "This creates .gitmodules file and libs/cool-lib directory",
                "Commit the addition: 'git commit -m \"Add cool-lib submodule\"'",
                "For fresh clones: 'git clone --recursive <repo-url>' or",
                "  'git submodule init && git submodule update'",
                "Update to latest: 'cd libs/cool-lib && git pull && cd .. && git add libs/cool-lib'",
                "Update all submodules: 'git submodule update --remote --merge'"
            ],
            "reasoning": "Submodules pin external dependencies to specific commits for reproducibility."
        }
    ),
    # Pre-push validation
    (
        "Set up comprehensive pre-push validation",
        {
            "steps": [
                "Create .git/hooks/pre-push file",
                "Add tests: '#!/bin/sh\\nnpm test || exit 1'",
                "Add linting: 'npm run lint || exit 1'",
                "Add type checking: 'npm run typecheck || exit 1'",
                "Check for secrets: 'git secrets --scan || exit 1'",
                "Make executable: 'chmod +x .git/hooks/pre-push'",
                "For team sharing, use Husky or pre-commit framework in package.json",
                "Configure bypass for emergencies: 'git push --no-verify' (use sparingly)"
            ],
            "reasoning": "Pre-push hooks prevent broken code from reaching shared branches."
        }
    ),
    # Blame investigation
    (
        "Investigate code history with git blame and log",
        {
            "steps": [
                "Find who changed a line: 'git blame src/app.py'",
                "See blame with commit info: 'git blame -L 10,20 src/app.py'",
                "Ignore whitespace changes: 'git blame -w src/app.py'",
                "Ignore code movement: 'git blame -M src/app.py'",
                "Ignore code copied from other files: 'git blame -C src/app.py'",
                "See full commit for a blame result: 'git show <commit-hash>'",
                "Track line through renames: 'git log -p -S \"function_name\" -- \"*.py\"'"
            ],
            "reasoning": "Blame with -w, -M, -C options filters out noise from refactoring."
        }
    ),
    # Creating patches
    (
        "Create and apply Git patches for offline collaboration",
        {
            "steps": [
                "Create patch from commits: 'git format-patch -3 HEAD' (last 3 commits)",
                "Create patch from branch diff: 'git format-patch main..feature'",
                "Create single combined patch: 'git diff main > feature.patch'",
                "Apply patch preserving authorship: 'git am < feature.patch'",
                "Apply diff patch: 'git apply feature.patch'",
                "Check if patch applies cleanly: 'git apply --check feature.patch'",
                "Apply with 3-way merge for conflicts: 'git am -3 < feature.patch'"
            ],
            "reasoning": "Patches enable code sharing when direct repository access isn't available."
        }
    ),
    # Archive/export
    (
        "Create a clean archive of the repository for distribution",
        {
            "steps": [
                "Archive current HEAD: 'git archive --format=zip HEAD -o project.zip'",
                "Archive specific branch: 'git archive --format=tar.gz release/v1.0 -o release.tar.gz'",
                "Archive subdirectory only: 'git archive HEAD:src/ -o src-only.zip'",
                "Add prefix directory: 'git archive --prefix=project-v1.0/ HEAD -o release.zip'",
                "Exclude files with export-ignore in .gitattributes:",
                "  Add '*.md export-ignore' to exclude markdown files",
                "Verify archive doesn't include .git: 'unzip -l project.zip | grep .git'"
            ],
            "reasoning": "Git archive creates clean distributions without .git history or ignored files."
        }
    ),
    # Bisect automation
    (
        "Automate git bisect with a test script",
        {
            "steps": [
                "Create a test script that exits 0 for good, non-zero for bad:",
                "  'echo \"npm test -- --grep 'failing test'\" > test.sh && chmod +x test.sh'",
                "Start bisect: 'git bisect start'",
                "Mark endpoints: 'git bisect bad HEAD' and 'git bisect good v1.0.0'",
                "Run automated bisect: 'git bisect run ./test.sh'",
                "Git will automatically find the first bad commit",
                "Record the result and reset: 'git bisect reset'",
                "For skipped commits: script can exit 125 to skip"
            ],
            "reasoning": "Automated bisect finds bugs in large histories without manual testing each commit."
        }
    ),
    # Rewriting author info
    (
        "Fix incorrect author information in commit history",
        {
            "steps": [
                "For last commit: 'git commit --amend --author=\"New Name <new@email.com>\"'",
                "For multiple commits, use filter-repo (preferred):",
                "  'git filter-repo --commit-callback \"if commit.author_email == b\\\"old@email.com\\\": commit.author_email = b\\\"new@email.com\\\"\"'",
                "Or interactive rebase for recent commits:",
                "  'git rebase -i HEAD~5' then 'exec git commit --amend --author=\"...\" --no-edit'",
                "Verify changes: 'git log --format=\"%h %an <%ae>\"'",
                "Force push: 'git push --force-with-lease'",
                "Notify collaborators to re-clone or 'git fetch --all && git reset --hard origin/main'"
            ],
            "reasoning": "Correcting author info maintains accurate attribution but requires history rewrite."
        }
    ),
    # Shallow clone optimization
    (
        "Optimize CI/CD with shallow and partial clones",
        {
            "steps": [
                "Shallow clone (last N commits): 'git clone --depth=1 <repo-url>'",
                "Deepen if needed: 'git fetch --deepen=100'",
                "Partial clone (blobs on-demand): 'git clone --filter=blob:none <repo-url>'",
                "Fetch specific branch only: 'git clone --single-branch --branch=main <repo-url>'",
                "Combine options: 'git clone --depth=1 --single-branch --branch=main <url>'",
                "Treeless clone (no trees): 'git clone --filter=tree:0 <repo-url>'",
                "Unshallow if full history needed later: 'git fetch --unshallow'"
            ],
            "reasoning": "Shallow/partial clones dramatically reduce CI clone times for large repositories."
        }
    ),
    # Sparse checkout
    (
        "Set up sparse checkout for monorepo",
        {
            "steps": [
                "Clone without files: 'git clone --filter=blob:none --sparse <repo-url>'",
                "Enable sparse checkout: 'git sparse-checkout init --cone'",
                "Add directories to checkout: 'git sparse-checkout set services/my-service libs/shared'",
                "List currently checked out paths: 'git sparse-checkout list'",
                "Add more paths: 'git sparse-checkout add packages/new-package'",
                "Disable sparse checkout: 'git sparse-checkout disable'",
                "Combine with partial clone for best performance in large monorepos"
            ],
            "reasoning": "Sparse checkout reduces disk usage and improves performance for large monorepos."
        }
    ),
    # Signing commits
    (
        "Set up GPG commit signing for verified commits",
        {
            "steps": [
                "Generate GPG key if needed: 'gpg --gen-key'",
                "List keys: 'gpg --list-secret-keys --keyid-format=long'",
                "Configure Git with key: 'git config --global user.signingkey <KEY_ID>'",
                "Enable signing by default: 'git config --global commit.gpgsign true'",
                "Sign a commit: 'git commit -S -m \"Signed commit\"'",
                "Verify signatures: 'git log --show-signature'",
                "Add public key to GitHub/GitLab for Verified badge",
                "For SSH signing (Git 2.34+): 'git config --global gpg.format ssh'"
            ],
            "reasoning": "Signed commits prove authenticity and prevent commit impersonation."
        }
    ),
    # Handling large files
    (
        "Set up Git LFS for large file management",
        {
            "steps": [
                "Install Git LFS: 'git lfs install'",
                "Track large file types: 'git lfs track \"*.psd\" \"*.mp4\" \"*.zip\"'",
                "This creates/updates .gitattributes file",
                "Commit the .gitattributes: 'git add .gitattributes && git commit -m \"Track large files with LFS\"'",
                "Now add large files normally: 'git add assets/video.mp4'",
                "Verify LFS tracking: 'git lfs ls-files'",
                "Migrate existing large files: 'git lfs migrate import --include=\"*.mp4\"'"
            ],
            "reasoning": "Git LFS stores large files externally while keeping repository size manageable."
        }
    ),
    # Conventional commits setup
    (
        "Implement conventional commits with automated changelog",
        {
            "steps": [
                "Install commitlint: 'npm install -D @commitlint/cli @commitlint/config-conventional'",
                "Create commitlint.config.js: 'module.exports = {extends: [\"@commitlint/config-conventional\"]}'",
                "Set up husky pre-commit hook for validation",
                "Install standard-version: 'npm install -D standard-version'",
                "Use commit format: 'feat(scope): description', 'fix(scope): description'",
                "Run release: 'npx standard-version' - auto-bumps version and generates CHANGELOG",
                "Breaking changes: 'feat!: description' or 'BREAKING CHANGE:' in body"
            ],
            "reasoning": "Conventional commits enable automated versioning and changelog generation."
        }
    ),
    # Branch cleanup
    (
        "Clean up stale branches in repository",
        {
            "steps": [
                "Fetch and prune remote-tracking branches: 'git fetch --prune'",
                "List merged local branches: 'git branch --merged main'",
                "Delete merged branches: 'git branch -d $(git branch --merged main | grep -v main)'",
                "List remote merged branches: 'git branch -r --merged origin/main'",
                "Delete remote branches: 'git push origin --delete feature/old-branch'",
                "Interactive cleanup with: 'git branch -vv | grep \": gone]\"'",
                "Batch delete gone branches: 'git branch -vv | grep \": gone]\" | awk \"{print \\$1}\" | xargs git branch -d'"
            ],
            "reasoning": "Regular branch cleanup keeps repository navigable and reduces confusion."
        }
    ),
    # Multi-remote workflow
    (
        "Set up multiple remotes for fork-based development",
        {
            "steps": [
                "Clone your fork: 'git clone https://github.com/you/project.git'",
                "Add upstream remote: 'git remote add upstream https://github.com/original/project.git'",
                "Verify remotes: 'git remote -v'",
                "Fetch upstream: 'git fetch upstream'",
                "Sync your main with upstream: 'git checkout main && git merge upstream/main'",
                "Push to your fork: 'git push origin main'",
                "Create feature branches from upstream: 'git checkout -b feature upstream/main'"
            ],
            "reasoning": "Multiple remotes enable contributing to upstream while maintaining your fork."
        }
    ),
    # Rerere setup
    (
        "Enable and use git rerere for conflict resolution",
        {
            "steps": [
                "Enable rerere globally: 'git config --global rerere.enabled true'",
                "Git will now record how you resolve conflicts",
                "Next time same conflict occurs, Git auto-resolves it",
                "See recorded resolutions: 'git rerere status'",
                "Show diff of recorded resolutions: 'git rerere diff'",
                "Forget a bad resolution: 'git rerere forget <pathspec>'",
                "Manually train rerere: resolve conflict, 'git rerere', then abort merge"
            ],
            "reasoning": "Rerere dramatically speeds up repeated rebases and long-running branch merges."
        }
    ),
    # Interactive staging
    (
        "Use interactive staging for precise commits",
        {
            "steps": [
                "Start interactive add: 'git add -i'",
                "Choose option 5 (patch) to stage hunks",
                "For direct patch mode: 'git add -p'",
                "At each hunk, choose: y=stage, n=skip, s=split smaller, e=edit manually",
                "Stage entire files but select hunks: 'git add -p <file>'",
                "Unstage hunks: 'git reset -p'",
                "Stash partial changes: 'git stash -p'"
            ],
            "reasoning": "Interactive staging enables committing logical changes separately from work-in-progress."
        }
    ),
]


# =============================================================================
# CONCEPT Q&A EXAMPLES
# =============================================================================

BASIC_CONCEPTS = [
    (
        "What is Git?",
        "Git is a distributed version control system (DVCS) that tracks changes to files over time. Unlike centralized systems, every developer has a full copy of the repository history locally. Key features include:\n\n- **Snapshots, not diffs**: Git stores snapshots of your entire project at each commit\n- **Local operations**: Most operations are fast because they don't require network access\n- **Branching**: Lightweight branches make it easy to experiment\n- **Integrity**: Every file and commit is checksummed with SHA-1\n\nGit was created by Linus Torvalds in 2005 for Linux kernel development."
    ),
    (
        "What is a commit in Git?",
        "A commit is a snapshot of your project at a specific point in time. Each commit contains:\n\n- **Tree**: A snapshot of all tracked files\n- **Parent(s)**: Reference to the previous commit(s)\n- **Author**: Who made the changes and when\n- **Committer**: Who committed the changes (can differ in cherry-picks/rebases)\n- **Message**: Description of what changed\n- **SHA-1 hash**: A unique 40-character identifier\n\nCommits are immutable - once created, they cannot be changed (though you can create new commits that replace them)."
    ),
    (
        "What is the difference between git fetch and git pull?",
        "**git fetch** downloads changes from the remote repository but doesn't modify your working directory:\n- Updates remote-tracking branches (e.g., origin/main)\n- Safe - never changes your local branches or files\n- Use when you want to see what's changed before merging\n\n**git pull** is essentially git fetch + git merge:\n- Downloads changes AND merges them into your current branch\n- Can cause merge conflicts if you have local changes\n- More convenient but less control\n\nBest practice: Use `git fetch` followed by `git merge` or `git rebase` for more control over how changes are integrated."
    ),
    (
        "What is a branch in Git?",
        "A branch is simply a lightweight, movable pointer to a commit. When you create a branch, Git creates a new pointer - it doesn't copy any files.\n\n- **main/master**: The default branch, typically represents production\n- **HEAD**: A special pointer to your currently checked-out branch\n- **Creating branches is cheap**: Just creates a 41-byte file (the commit hash)\n\nBranches enable:\n- Parallel development (multiple features simultaneously)\n- Isolation (experiments don't affect stable code)\n- Code review workflows (feature branches → pull requests)"
    ),
    (
        "What is staging (the index) in Git?",
        "The staging area (also called the index) is an intermediate area between your working directory and the repository. It lets you control exactly what goes into your next commit.\n\n**Workflow:**\n1. **Working directory**: Where you edit files\n2. **Staging area**: Where you prepare commits (`git add`)\n3. **Repository**: Where commits are stored (`git commit`)\n\n**Benefits:**\n- Commit only part of your changes\n- Review what will be committed (`git diff --staged`)\n- Build commits incrementally\n\nUse `git add -p` to stage individual hunks within a file for fine-grained control."
    ),
    (
        "What is .gitignore?",
        "`.gitignore` is a file that tells Git which files or directories to ignore (not track). Common entries include:\n\n```\n# Dependencies\nnode_modules/\nvenv/\n\n# Build outputs\ndist/\n*.pyc\n\n# IDE files\n.vscode/\n.idea/\n\n# Secrets\n.env\n*.key\n```\n\n**Rules:**\n- Patterns are matched from the repository root\n- `*` matches anything, `**` matches directories\n- `!` negates a pattern (un-ignore)\n- Lines starting with `#` are comments\n\nAlready-tracked files aren't affected - use `git rm --cached <file>` to stop tracking."
    ),
    # NEW: Additional basic concepts
    (
        "What is HEAD in Git?",
        "HEAD is a special reference that points to the current commit you're working on. It's essentially 'where you are' in the repository.\n\n**Types of HEAD:**\n- **Attached HEAD**: Points to a branch name (e.g., HEAD → main → commit)\n- **Detached HEAD**: Points directly to a commit (no branch)\n\n**Common uses:**\n- `HEAD`: Current commit\n- `HEAD~1` or `HEAD^`: Parent of current commit\n- `HEAD~3`: Three commits before HEAD\n- `HEAD^2`: Second parent (for merge commits)\n\n**Commands that move HEAD:**\n- `git checkout`: Moves HEAD to a branch/commit\n- `git commit`: Moves HEAD forward with new commit\n- `git reset`: Moves HEAD backwards\n\nHEAD is stored in `.git/HEAD` - you can see it with `cat .git/HEAD`."
    ),
    (
        "What is a remote in Git?",
        "A remote is a reference to another copy of your repository, typically hosted on a server like GitHub, GitLab, or Bitbucket.\n\n**Default remote - origin:**\n- When you clone, Git creates 'origin' pointing to the source\n- `git remote -v` shows all configured remotes\n\n**Remote-tracking branches:**\n- `origin/main`: Your local copy of the remote's main branch\n- Updated by `git fetch`, not by local commits\n- Can't be checked out directly (read-only)\n\n**Common operations:**\n```bash\ngit remote add origin <url>     # Add a remote\ngit remote rename origin upstream  # Rename\ngit remote remove backup        # Delete\ngit remote set-url origin <new-url>  # Change URL\n```\n\nYou can have multiple remotes for forks, backups, or different deployment targets."
    ),
    (
        "What does 'git clone' do?",
        "`git clone` creates a complete copy of a repository, including all history, branches, and tags.\n\n**What clone does:**\n1. Creates a new directory (or uses specified name)\n2. Initializes a new Git repository\n3. Adds `origin` remote pointing to the source\n4. Fetches all branches and tags\n5. Checks out the default branch (usually main)\n\n**Variations:**\n```bash\ngit clone <url>                  # Full clone\ngit clone --depth 1 <url>        # Shallow (last commit only)\ngit clone --branch dev <url>     # Clone and checkout specific branch\ngit clone --bare <url>           # Clone without working directory\ngit clone <url> myproject        # Clone into 'myproject' folder\n```\n\n**After cloning**, you have all remote branches as remote-tracking branches (origin/*) and can create local branches from them."
    ),
    (
        "What is git diff and how do I use it?",
        "`git diff` shows the differences between various states in Git.\n\n**Common comparisons:**\n```bash\ngit diff                    # Working directory vs staging area\ngit diff --staged           # Staging area vs last commit (HEAD)\ngit diff HEAD               # Working directory vs last commit\ngit diff branch1..branch2   # Between two branches\ngit diff abc123 def456      # Between two commits\ngit diff HEAD~3             # Current vs 3 commits ago\n```\n\n**Filtering:**\n```bash\ngit diff -- path/to/file    # Only specific file\ngit diff --stat             # Summary only (files changed)\ngit diff --name-only        # Just filenames\n```\n\n**Output format:**\n- Lines starting with `-` are removed\n- Lines starting with `+` are added\n- `@@` markers show line numbers\n\nUse a visual diff tool with `git difftool` for complex changes."
    ),
    (
        "How do I undo changes in Git?",
        "Git offers several ways to undo changes, depending on where the changes are:\n\n**1. Undo unstaged changes (working directory):**\n```bash\ngit checkout -- <file>     # Discard file changes (old way)\ngit restore <file>         # Discard file changes (new way)\ngit restore .              # Discard all changes\n```\n\n**2. Undo staged changes:**\n```bash\ngit reset HEAD <file>      # Unstage file (old way)\ngit restore --staged <file> # Unstage file (new way)\n```\n\n**3. Undo last commit:**\n```bash\ngit reset --soft HEAD~1    # Undo commit, keep changes staged\ngit reset --mixed HEAD~1   # Undo commit, keep changes unstaged\ngit reset --hard HEAD~1    # Undo commit and discard changes\n```\n\n**4. Undo a published commit (safe):**\n```bash\ngit revert <commit>        # Creates new commit that undoes changes\n```\n\n**Rule of thumb**: Use `reset` for local changes, `revert` for shared history."
    ),
    (
        "What is git stash?",
        "`git stash` temporarily saves your uncommitted changes so you can work on something else.\n\n**Basic usage:**\n```bash\ngit stash                  # Save changes\ngit stash pop              # Restore and remove from stash\ngit stash apply            # Restore but keep in stash\ngit stash drop             # Delete top stash entry\n```\n\n**Managing multiple stashes:**\n```bash\ngit stash list             # View all stashes\ngit stash save \"message\"   # Stash with description\ngit stash pop stash@{2}    # Pop specific stash\ngit stash show             # View stash contents\ngit stash show -p          # View stash as diff\n```\n\n**Advanced:**\n```bash\ngit stash -u               # Include untracked files\ngit stash -a               # Include ignored files too\ngit stash branch <name>    # Create branch from stash\n```\n\n**When to use**: Quick context switches, pulling when you have local changes, experimenting safely."
    ),
    (
        "What is a tag in Git?",
        "Tags are named references to specific commits, typically used to mark release points.\n\n**Two types:**\n\n**1. Lightweight tags** (just a pointer):\n```bash\ngit tag v1.0               # Tag current commit\ngit tag v1.0 <commit>      # Tag specific commit\n```\n\n**2. Annotated tags** (full objects with metadata):\n```bash\ngit tag -a v1.0 -m \"Release v1.0\"  # With message\ngit tag -s v1.0 -m \"Signed release\" # GPG signed\n```\n\n**Working with tags:**\n```bash\ngit tag                    # List all tags\ngit show v1.0              # Show tag details\ngit checkout v1.0          # Checkout tag (detached HEAD)\ngit push origin v1.0       # Push specific tag\ngit push origin --tags     # Push all tags\ngit tag -d v1.0            # Delete local tag\ngit push origin :v1.0      # Delete remote tag\n```\n\n**Best practice**: Use annotated tags for releases (they store tagger info and timestamp)."
    ),
    (
        "What is a merge commit?",
        "A merge commit is a special commit with two or more parents, created when branches are merged.\n\n**How it works:**\n```bash\ngit checkout main\ngit merge feature-branch   # Creates merge commit if histories diverged\n```\n\n**Merge commit properties:**\n- Has multiple parent commits\n- Represents the point where branches rejoin\n- Message typically starts with \"Merge branch...\"\n\n**Fast-forward vs merge commit:**\n- **Fast-forward**: If main hasn't changed, Git just moves the pointer (no merge commit)\n- **Merge commit**: If both branches have new commits, Git creates a merge commit\n\n**Control the behavior:**\n```bash\ngit merge --ff-only feature    # Only fast-forward (fails if not possible)\ngit merge --no-ff feature      # Always create merge commit\ngit merge --squash feature     # Combine changes but don't commit yet\n```\n\nMerge commits preserve branch history but can make the history graph complex."
    ),
    (
        "What is a pull request / merge request?",
        "A pull request (GitHub/Bitbucket) or merge request (GitLab) is a feature of Git hosting platforms that facilitates code review before merging.\n\n**It's NOT a Git concept** - it's a platform feature built on top of Git.\n\n**Workflow:**\n1. Create a feature branch and push it\n2. Open a PR/MR on the platform\n3. Teammates review, comment, request changes\n4. Make updates, push more commits\n5. Once approved, merge (via platform or command line)\n\n**PR features:**\n- Code diff visualization\n- Inline comments and discussions\n- CI/CD integration (required checks)\n- Approval requirements\n- Merge options (merge, squash, rebase)\n\n**Under the hood**, a PR is just asking to merge your branch into another branch. You could do `git merge` directly, but PRs add collaboration features."
    ),
    (
        "What is git log and how do I read it?",
        "`git log` shows the commit history of your repository.\n\n**Basic usage:**\n```bash\ngit log                    # Full history\ngit log -5                 # Last 5 commits\ngit log --oneline          # Compact one-line format\ngit log --graph            # Show branch structure\ngit log --all              # All branches, not just current\n```\n\n**Filtering:**\n```bash\ngit log --author=\"John\"    # By author\ngit log --since=\"2024-01-01\"  # By date\ngit log --grep=\"bug fix\"   # By message content\ngit log -- path/to/file    # Commits affecting file\ngit log -S \"functionName\"  # Commits changing string (pickaxe)\n```\n\n**Formatting:**\n```bash\ngit log --format=\"%h %s (%an)\"  # Custom format\ngit log --stat             # Show files changed\ngit log -p                 # Show actual diffs\n```\n\n**Reading the output**: Each entry shows commit hash, author, date, and message. Use `--oneline --graph` for a visual overview."
    ),
]

ADVANCED_CONCEPTS = [
    (
        "How does Git store data internally?",
        "Git is fundamentally a content-addressable filesystem with a VCS built on top. It stores four types of objects:\n\n**1. Blob**: Raw file contents (no filename or metadata)\n**2. Tree**: Directory listings - maps filenames to blob/tree hashes\n**3. Commit**: Points to a tree + metadata (author, message, parent commits)\n**4. Tag**: Named pointer to a commit with optional signature\n\n**Storage:**\n- Objects are stored in `.git/objects/` by their SHA-1 hash\n- First 2 chars = directory, rest = filename (e.g., `ab/cdef1234...`)\n- Objects are compressed with zlib\n- Pack files (`.git/objects/pack/`) store deltas for efficiency\n\nThis content-addressed design means identical content is stored only once, and data integrity is guaranteed by the hash."
    ),
    (
        "Explain git rebase vs git merge",
        "Both integrate changes between branches, but with different history results:\n\n**Merge:**\n- Creates a new 'merge commit' with two parents\n- Preserves the exact history of both branches\n- Non-destructive - existing commits unchanged\n- Results in a non-linear history with merge bubbles\n\n**Rebase:**\n- Replays your commits on top of another branch\n- Creates NEW commits (different hashes) - rewrites history\n- Results in a linear, cleaner history\n- Dangerous on shared branches (others have the old commits)\n\n**When to use each:**\n- **Merge**: Public/shared branches, preserving feature branch history\n- **Rebase**: Local branches before pushing, cleaning up messy commits\n\n**Golden rule**: Never rebase commits that have been pushed to a shared repository."
    ),
    (
        "What is git reflog and how does it help recover lost work?",
        "Reflog (reference log) records every change to HEAD and branch tips in your local repository. It's your safety net for recovering 'lost' commits.\n\n**What it tracks:**\n- Every commit, merge, rebase, reset, checkout\n- Keeps entries for ~90 days by default\n- Local only - not pushed to remotes\n\n**Common recovery scenarios:**\n```bash\n# After accidental hard reset\ngit reflog\n# Shows: abc1234 HEAD@{2}: commit: Important work\ngit checkout abc1234\ngit branch recovered-work\n\n# After bad rebase\ngit reflog\ngit reset --hard HEAD@{5}  # Go back to before rebase\n```\n\n**Key insight**: In Git, commits are never truly deleted until garbage collection runs. If you can find the hash, you can recover it."
    ),
    (
        "How do Git hooks work?",
        "Git hooks are scripts that run automatically at certain points in the Git workflow. They live in `.git/hooks/` and must be executable.\n\n**Client-side hooks:**\n- `pre-commit`: Before commit is created (lint, test)\n- `prepare-commit-msg`: Modify default commit message\n- `commit-msg`: Validate commit message format\n- `pre-push`: Before push (run full test suite)\n- `post-checkout`: After checkout (rebuild dependencies)\n\n**Server-side hooks:**\n- `pre-receive`: Before accepting a push (enforce policies)\n- `update`: Like pre-receive but per-branch\n- `post-receive`: After push completes (deploy, notify)\n\n**Example pre-commit hook:**\n```bash\n#!/bin/sh\nnpm run lint || exit 1\nnpm test || exit 1\n```\n\n**Tools**: Husky, pre-commit framework, and Lefthook help manage hooks across teams."
    ),
    (
        "Explain the three-tree architecture in Git",
        "Git manages three 'trees' (collections of files) during normal operations:\n\n**1. HEAD (Last Commit)**\n- The snapshot from your last commit\n- What the repository looked like then\n- Immutable once committed\n\n**2. Index (Staging Area)**\n- Proposed next commit\n- `git add` copies from working directory to index\n- `git diff --staged` shows index vs HEAD\n\n**3. Working Directory**\n- Your actual files on disk\n- A 'sandbox' for editing\n- `git diff` shows working directory vs index\n\n**Reset modes operate on these trees:**\n- `git reset --soft HEAD~1`: Moves HEAD only (index and working unchanged)\n- `git reset --mixed HEAD~1`: Moves HEAD, resets index (working unchanged) [default]\n- `git reset --hard HEAD~1`: Resets all three trees\n\nUnderstanding this model clarifies how staging, committing, and resetting work."
    ),
    (
        "What is a detached HEAD state?",
        "Detached HEAD occurs when HEAD points directly to a commit instead of a branch reference. This happens when you:\n\n- `git checkout <commit-hash>`\n- `git checkout v1.0` (a tag)\n- During `git rebase` or `git bisect`\n\n**Implications:**\n- You can make commits, but they're 'orphaned'\n- If you switch branches, those commits become hard to find\n- No branch name updates automatically\n\n**Working in detached HEAD:**\n```bash\ngit checkout abc1234  # Now detached\n# Make changes and commit...\ngit checkout -b new-branch  # Save work to a branch\n```\n\n**Or to just look around:**\n```bash\ngit checkout abc1234  # Inspect old state\n# Look around, don't commit\ngit checkout main     # Return safely\n```\n\nAlways create a branch if you want to keep commits made in detached HEAD state."
    ),
    (
        "How does git cherry-pick work internally?",
        "Cherry-pick applies the changes introduced by an existing commit onto your current branch as a NEW commit.\n\n**Process:**\n1. Git computes the diff between the cherry-picked commit and its parent\n2. Applies that diff to your current HEAD\n3. Creates a new commit with:\n   - Same author and message (by default)\n   - Different committer and timestamp\n   - Different SHA-1 (because parent is different)\n\n**Use cases:**\n- Backporting a fix to a release branch\n- Pulling specific commits from a feature branch\n- Recovering commits from an abandoned branch\n\n**Flags:**\n- `-x`: Appends '(cherry picked from commit...)' to message\n- `-n`: Apply changes but don't commit (stage only)\n- `-m 1`: For merge commits, specify which parent to diff against\n\n**Caution**: Creates duplicate commits if the original is later merged. Consider `git rebase` for moving entire branches."
    ),
    (
        "Explain Git's garbage collection and object pruning",
        "Git's garbage collection (`git gc`) cleans up and optimizes the repository.\n\n**What it does:**\n- Compresses loose objects into pack files\n- Removes unreachable objects (orphaned commits, old blobs)\n- Prunes reflog entries older than the expiry (90 days default)\n- Removes empty directories in `.git/objects`\n\n**When objects become unreachable:**\n- Commits after `git reset --hard`\n- Old commits after `git rebase`\n- Blobs from files removed from history\n\n**Timeline:**\n1. Object becomes unreachable (no ref points to it)\n2. Reflog still references it (~90 days)\n3. Reflog entry expires\n4. Next `git gc` prunes the object\n\n**Commands:**\n```bash\ngit gc              # Normal garbage collection\ngit gc --aggressive # More thorough optimization\ngit gc --prune=now  # Immediately prune unreachable objects\ngit prune           # Just prune, no packing\n```\n\n**Safety**: Objects are recoverable via reflog until gc runs after reflog expiry."
    ),
    # NEW: Additional advanced concepts
    (
        "What are Git worktrees and when should I use them?",
        "Git worktrees allow multiple working directories sharing the same repository, perfect for parallel work without stashing.\n\n**How it works:**\n- Main worktree: Your normal clone\n- Linked worktrees: Additional checkouts in different directories\n- All share `.git` database (commits, branches, objects)\n\n**Use cases:**\n- Review a PR while working on something else\n- Run tests on one branch while coding on another\n- Build multiple versions simultaneously\n\n**Commands:**\n```bash\ngit worktree add ../review feature/pr-123   # New worktree for branch\ngit worktree add -b hotfix ../hotfix main   # Create branch and worktree\ngit worktree list                           # Show all worktrees\ngit worktree remove ../review               # Delete worktree\ngit worktree prune                          # Clean up stale entries\n```\n\n**Rules:**\n- Each branch can only be checked out in one worktree\n- Deleting a worktree doesn't delete the branch\n- More efficient than multiple clones (shared objects)"
    ),
    (
        "How does Git's pack file format work?",
        "Pack files efficiently store Git objects using delta compression.\n\n**Loose vs packed objects:**\n- **Loose**: Individual zlib-compressed files in `.git/objects/`\n- **Packed**: Multiple objects combined in `.git/objects/pack/`\n\n**Delta compression:**\n- Similar objects stored as base + delta (difference)\n- Git finds similar objects automatically\n- Can achieve 10-100x compression for code\n\n**Pack file structure:**\n- `.pack` file: Contains the actual object data\n- `.idx` file: Index for fast object lookup\n- Contains header, object entries, checksum\n\n**When packing occurs:**\n- `git gc` (automatic or manual)\n- `git repack`\n- `git push` (creates thin pack for transfer)\n\n**Inspection:**\n```bash\ngit verify-pack -v .git/objects/pack/*.idx  # List objects in pack\ngit count-objects -v                        # Show object statistics\n```\n\nThis design makes Git efficient for large repos with many similar files."
    ),
    (
        "Explain Git submodules vs subtrees",
        "Both manage external dependencies in a repository, but with different tradeoffs.\n\n**Submodules:**\n- Store a pointer to a specific commit in another repo\n- External repo remains separate\n- Requires explicit updates (`git submodule update`)\n- `.gitmodules` file tracks submodule URLs\n\n**Pros**: Clear separation, smaller repo size, version pinning\n**Cons**: Complex workflow, easy to get out of sync\n\n**Subtrees:**\n- Copy external project INTO your repo\n- History is merged into your history\n- No special commands needed for contributors\n\n**Pros**: Simpler workflow, works like regular directories\n**Cons**: Larger repo, harder to push changes upstream\n\n**When to use each:**\n- **Submodules**: Large dependencies, multiple repos using same lib\n- **Subtrees**: Smaller dependencies, want simpler contributor workflow\n\n**Commands:**\n```bash\n# Submodule\ngit submodule add <url> <path>\ngit submodule update --init --recursive\n\n# Subtree\ngit subtree add --prefix=libs/dep <url> main --squash\ngit subtree pull --prefix=libs/dep <url> main --squash\n```"
    ),
    (
        "What is git bisect and how does binary search help debugging?",
        "`git bisect` uses binary search to find the commit that introduced a bug in O(log n) tests.\n\n**How it works:**\n1. You specify a known good commit and known bad commit\n2. Git checks out the middle commit\n3. You test and mark it good or bad\n4. Git narrows the range by half\n5. Repeat until the culprit is found\n\n**Example: 1000 commits to search**\n- Linear search: Up to 1000 tests\n- Binary search: ~10 tests (log₂ 1000)\n\n**Manual bisect:**\n```bash\ngit bisect start\ngit bisect bad HEAD            # Current is broken\ngit bisect good v1.0.0         # This version worked\n# Git checks out middle commit\n# Test it...\ngit bisect good                # or git bisect bad\n# Repeat until found\ngit bisect reset               # Return to original state\n```\n\n**Automated bisect:**\n```bash\ngit bisect start HEAD v1.0.0\ngit bisect run ./test-script.sh  # Returns 0=good, 1=bad\n```\n\n**Skip problematic commits**: `git bisect skip` if a commit can't be tested."
    ),
    (
        "How does fast-forward merge differ from three-way merge?",
        "These are Git's two strategies for combining branches.\n\n**Fast-forward merge:**\n- Happens when target branch has no new commits\n- Git simply moves the branch pointer forward\n- No merge commit created\n- Linear history preserved\n\n```\nBefore:      main    feature\n               ↓        ↓\n            A--B--------C\n\nAfter ff:    main\n               ↓\n            A--B--C\n```\n\n**Three-way merge:**\n- Both branches have diverged with new commits\n- Git finds common ancestor and creates merge commit\n- Merge commit has two parents\n\n```\nBefore:      main    feature\n               ↓        ↓\n            A--B--D    C\n               └───┘\n\nAfter:       main\n               ↓\n            A--B--D--M (merge)\n               └──C──┘\n```\n\n**Control behavior:**\n```bash\ngit merge --ff-only    # Only fast-forward (fail if not possible)\ngit merge --no-ff      # Always create merge commit\n```\n\n**Best practice**: Use `--no-ff` for feature branches to preserve branch history."
    ),
    (
        "What are Git attributes and how do they affect behavior?",
        "`.gitattributes` configures path-specific settings for Git behavior.\n\n**Common uses:**\n\n**1. Line ending normalization:**\n```\n* text=auto                # Auto-detect text files\n*.sh text eol=lf           # Force LF for shell scripts\n*.bat text eol=crlf        # Force CRLF for Windows batch\n```\n\n**2. Diff behavior:**\n```\n*.png binary               # Treat as binary\n*.min.js -diff             # Don't show diffs\n*.py diff=python           # Use Python-aware diff\n```\n\n**3. Merge strategies:**\n```\n*.lock merge=ours          # Always keep our version\npackage-lock.json -merge   # Require manual merge\n```\n\n**4. Export control:**\n```\n.gitattributes export-ignore\ntests/ export-ignore       # Exclude from archives\n```\n\n**5. LFS tracking:**\n```\n*.psd filter=lfs diff=lfs merge=lfs -text\n```\n\nAttributes are processed hierarchically from repo root through subdirectories."
    ),
    (
        "Explain the difference between author and committer in Git",
        "Git tracks two identities for each commit: author and committer.\n\n**Author:**\n- Who originally wrote the changes\n- Set when commit is first created\n- Preserved through cherry-pick, rebase\n\n**Committer:**\n- Who last applied the commit\n- Updated on cherry-pick, rebase, amend\n- Usually same as author for regular commits\n\n**When they differ:**\n- `git cherry-pick`: Author = original, Committer = you\n- `git rebase`: Author preserved, Committer = rebaser\n- `git commit --amend`: Committer updated, Author unchanged\n- Patches via email: Author = patch writer, Committer = applier\n\n**View both:**\n```bash\ngit log --format=\"%H%n  Author: %an <%ae> %ad%n  Commit: %cn <%ce> %cd\"\n```\n\n**Override author:**\n```bash\ngit commit --author=\"Name <email@example.com>\"\n```\n\nThis distinction maintains accurate attribution in collaborative workflows."
    ),
    (
        "What is the difference between git reset and git revert?",
        "Both undo changes but in fundamentally different ways.\n\n**git reset:**\n- Moves branch pointer backward\n- Rewrites history (commits disappear)\n- Affects local state only (until pushed)\n- Three modes: --soft, --mixed, --hard\n\n```bash\ngit reset --soft HEAD~3   # Undo 3 commits, keep changes staged\ngit reset --mixed HEAD~3  # Undo 3 commits, keep changes unstaged\ngit reset --hard HEAD~3   # Undo 3 commits, discard changes\n```\n\n**git revert:**\n- Creates NEW commit that undoes changes\n- Preserves history (original commit remains)\n- Safe for shared branches\n- Can revert any commit, not just recent ones\n\n```bash\ngit revert HEAD           # Revert last commit\ngit revert abc123         # Revert specific commit\ngit revert abc123..def456 # Revert range\ngit revert -n abc123      # Stage revert without committing\n```\n\n**When to use:**\n- **reset**: Local changes, unpushed commits, cleaning up before push\n- **revert**: Published commits, shared branches, maintaining accurate history"
    ),
    (
        "How does Git handle binary files?",
        "Git can store binary files but with limitations compared to text files.\n\n**What Git does:**\n- Stores complete snapshots (no diff optimization)\n- Compresses with zlib (works better for some formats)\n- Cannot show meaningful diffs\n- Cannot merge binary files automatically\n\n**Challenges:**\n- Large binaries bloat repository permanently\n- Each version stored in full (unlike text deltas)\n- History rewriting required to truly remove\n\n**Solutions:**\n\n**1. Git LFS (Large File Storage):**\n```bash\ngit lfs track \"*.psd\"\n# Stores pointer in Git, actual file on LFS server\n```\n\n**2. .gitattributes:**\n```\n*.png binary              # Explicit binary marking\n*.doc diff=word           # Custom diff driver\n```\n\n**3. Custom diff/merge:**\n```bash\ngit config diff.exif.textconv exiftool  # For images\ngit config merge.unity.driver \"...\"     # For Unity files\n```\n\n**Best practices:**\n- Use LFS for large binaries (>1MB)\n- Store source files, not generated binaries\n- Consider artifact storage (Artifactory, S3) for builds"
    ),
    (
        "What is a bare repository in Git?",
        "A bare repository has no working directory - only the `.git` contents.\n\n**Structure:**\n```\nregular-repo/           bare-repo.git/\n├── .git/               ├── HEAD\n│   ├── HEAD            ├── config\n│   ├── objects/        ├── objects/\n│   └── refs/           └── refs/\n└── (working files)\n```\n\n**Use cases:**\n- Central/server repositories (GitHub, GitLab)\n- Shared team repositories\n- Backup/mirror repositories\n\n**Why bare for servers:**\n- No working directory to get out of sync\n- Push operations are always safe\n- Can't accidentally edit files\n\n**Commands:**\n```bash\ngit init --bare repo.git      # Create bare repo\ngit clone --bare <url>        # Clone as bare\ngit config --bool core.bare true  # Convert to bare\n```\n\n**Conventions:**\n- Bare repos use `.git` suffix (myproject.git)\n- Typically stored in shared locations\n- Never checkout or edit directly\n\nBare repos are the backbone of Git hosting services."
    ),
]


# =============================================================================
# ERROR HANDLING / GUARDRAIL EXAMPLES
# =============================================================================

ERROR_SCENARIOS = [
    # Merge conflicts
    (
        "Context: You ran 'git merge feature-branch' and got CONFLICT in 3 files.\nTask: Help me resolve these merge conflicts",
        {
            "action": "guide",
            "response": "You have merge conflicts that need manual resolution. Here's how to proceed:\n\n1. **See conflicting files**: `git status` shows files with conflicts\n\n2. **Open each file** and look for conflict markers:\n```\n<<<<<<< HEAD\nyour changes\n=======\ntheir changes\n>>>>>>> feature-branch\n```\n\n3. **Resolve each conflict** by:\n   - Keeping your version\n   - Keeping their version\n   - Combining both\n   - Writing something new\n\n4. **Remove the conflict markers** entirely\n\n5. **Stage resolved files**: `git add <filename>`\n\n6. **Complete the merge**: `git commit`\n\nTip: Use `git mergetool` if you have a visual merge tool configured.",
            "guardrail": "manual_intervention_required"
        }
    ),
    # Push rejected
    (
        "Context: 'git push' failed with 'rejected - non-fast-forward'\nTask: Push my changes to the remote",
        {
            "action": "guide",
            "response": "Your push was rejected because the remote has commits you don't have locally. This is a safety feature to prevent overwriting others' work.\n\n**Safe solution (recommended):**\n```bash\ngit pull --rebase origin main\n# Resolve any conflicts if they occur\ngit push\n```\n\n**Alternative (merge instead of rebase):**\n```bash\ngit pull origin main\n# This creates a merge commit\ngit push\n```\n\n**Force push (DANGEROUS - only for your own branches):**\n```bash\ngit push --force-with-lease\n# Only use on feature branches you alone work on\n```\n\nNever force push to shared branches like main/master.",
            "guardrail": "prevent_data_loss"
        }
    ),
    # Detached HEAD
    (
        "Context: Git says 'You are in detached HEAD state'\nTask: I made commits here and don't want to lose them",
        {
            "action": "guide",
            "response": "You're in detached HEAD state with commits that aren't on any branch. To save your work:\n\n**Create a branch from your current position:**\n```bash\ngit branch my-saved-work\n# or create and switch in one command:\ngit checkout -b my-saved-work\n```\n\nYour commits are now safely on a branch. You can:\n- Merge it into main: `git checkout main && git merge my-saved-work`\n- Rebase it: `git rebase main`\n- Push it: `git push -u origin my-saved-work`\n\n**How you got here**: Detached HEAD happens when you checkout a commit hash, tag, or during rebase/bisect. Always create a branch if you plan to make commits.",
            "guardrail": "prevent_data_loss"
        }
    ),
    # Accidental commit
    (
        "Context: I accidentally committed sensitive data (API key) to the repository\nTask: Remove the sensitive data from Git history",
        {
            "action": "guide",
            "response": "⚠️ **URGENT**: If pushed, assume the key is compromised. Rotate it immediately.\n\n**Remove from history (unpushed commits):**\n```bash\ngit reset --soft HEAD~1  # Undo commit, keep changes staged\n# Remove the sensitive file\ngit add .\ngit commit -m 'Remove sensitive data'\n```\n\n**Remove from entire history (if pushed):**\n```bash\n# Using git-filter-repo (recommended)\npip install git-filter-repo\ngit filter-repo --path secrets.txt --invert-paths\n\n# Force push ALL branches\ngit push origin --force --all\n```\n\n**After cleanup:**\n1. Add the file to .gitignore\n2. Use environment variables instead\n3. Notify collaborators to re-clone\n4. Rotate any exposed credentials\n\n**Prevention**: Use pre-commit hooks to scan for secrets (git-secrets, detect-secrets).",
            "guardrail": "security_incident"
        }
    ),
    # Rebase conflict loop
    (
        "Context: During 'git rebase main', I've been resolving the same conflict repeatedly for 5 commits\nTask: Finish this rebase",
        {
            "action": "guide",
            "response": "Repeated conflicts during rebase often indicate structural issues. Options:\n\n**Continue if almost done:**\n```bash\n# After resolving current conflict\ngit add .\ngit rebase --continue\n```\n\n**Abort and try different approach:**\n```bash\ngit rebase --abort  # Return to pre-rebase state\n\n# Try merge instead (preserves history as-is)\ngit merge main\n```\n\n**Enable rerere (REuse REcorded REsolution):**\n```bash\ngit config --global rerere.enabled true\n# Git will remember how you resolved conflicts\n```\n\n**If conflicts are in generated files:**\n- Accept theirs: `git checkout --theirs <file>`\n- Accept yours: `git checkout --ours <file>`\n- Regenerate after rebase completes\n\nFor heavily diverged branches, merge is often simpler than rebase.",
            "guardrail": "loop_detection"
        }
    ),
    # Lost commits after reset
    (
        "Context: I ran 'git reset --hard HEAD~5' and lost important commits\nTask: Recover those lost commits",
        {
            "action": "guide",
            "response": "Don't panic! The commits aren't deleted yet - they're just unreachable. Use reflog to recover them:\n\n**Find the lost commits:**\n```bash\ngit reflog\n# Look for entries like:\n# abc1234 HEAD@{1}: commit: My important work\n# def5678 HEAD@{2}: commit: Also important\n```\n\n**Recover to a branch:**\n```bash\n# Create a branch pointing to before the reset\ngit branch recovered HEAD@{6}\n# Or directly checkout\ngit checkout HEAD@{6}\ngit checkout -b recovered\n```\n\n**Verify recovery:**\n```bash\ngit log recovered  # Should show your lost commits\n```\n\n**Merge recovered work:**\n```bash\ngit checkout main\ngit merge recovered\n# or cherry-pick specific commits\ngit cherry-pick abc1234 def5678\n```\n\nReflog entries expire after ~90 days, so recover promptly.",
            "guardrail": "prevent_data_loss"
        }
    ),
    # Submodule issues
    (
        "Context: 'git pull' says 'fatal: reference is not a tree' in a submodule\nTask: Fix this submodule error",
        {
            "action": "guide",
            "response": "This error means the parent repo references a submodule commit that doesn't exist. Common causes:\n- Someone pushed parent repo but not submodule\n- Submodule repo was force-pushed\n\n**Fix 1: Update submodule to latest:**\n```bash\ncd path/to/submodule\ngit fetch\ngit checkout main\ngit pull\ncd ..\ngit add path/to/submodule\ngit commit -m 'Update submodule to latest'\n```\n\n**Fix 2: If you need the specific commit:**\n```bash\n# Get the expected commit hash\ngit ls-tree HEAD path/to/submodule\n# Contact submodule maintainer to push that commit\n```\n\n**Fix 3: Re-clone submodule:**\n```bash\ngit submodule deinit path/to/submodule\nrm -rf .git/modules/path/to/submodule\ngit submodule update --init path/to/submodule\n```\n\nPrevention: Always push submodule changes before pushing parent repo changes.",
            "guardrail": "dependency_issue"
        }
    ),
    # No agent for remote operations
    (
        "Context: User asked to check git status on their remote server but list_agents returned no agents\nTask: Check git status on the production server",
        {
            "action": "stop",
            "response": "I cannot check the git status on the production server because no FunnelCloud agents are currently available. The list_agents command found no connected agents.\n\nTo proceed, please:\n1. Start the FunnelCloud agent on the production server\n2. Ensure the agent is network-accessible from this environment\n3. Verify the agent registered successfully with the orchestrator\n\nOnce an agent is available, I can execute git commands on the remote server.",
            "guardrail": "no_agent_available"
        }
    ),
    # NEW: Additional error scenarios
    # Corrupt repository
    (
        "Context: Git says 'fatal: bad object HEAD' or 'error: object file is empty'\nTask: Recover from repository corruption",
        {
            "action": "guide",
            "response": "Your repository has corrupted objects. Recovery approach depends on severity:\n\n**Step 1: Check extent of damage:**\n```bash\ngit fsck --full\n```\n\n**Step 2: If only HEAD is bad:**\n```bash\ngit symbolic-ref HEAD refs/heads/main  # Point HEAD to main\n# Or find last good commit from reflog\ngit reflog\ngit reset --hard <last-good-commit>\n```\n\n**Step 3: If objects are corrupted:**\n```bash\n# Fetch missing objects from remote\ngit fetch origin\n# Re-sync local to remote\ngit reset --hard origin/main\n```\n\n**Step 4: If no remote exists (nuclear option):**\n```bash\n# Save any recoverable files\ncp -r . ../backup\n# Re-clone from backup if possible\nrm -rf .git\ngit init\n# Re-add remote and fetch\n```\n\n**Prevention**: Avoid killing Git processes, use reliable storage, enable git gc.",
            "guardrail": "data_corruption"
        }
    ),
    # Permission denied
    (
        "Context: 'git push' fails with 'Permission denied (publickey)'\nTask: Push my changes to GitHub",
        {
            "action": "guide",
            "response": "SSH authentication is failing. Let's diagnose and fix:\n\n**Step 1: Check if SSH key exists:**\n```bash\nls -la ~/.ssh/id_ed25519.pub  # or id_rsa.pub\n```\n\n**Step 2: If no key, generate one:**\n```bash\nssh-keygen -t ed25519 -C \"your@email.com\"\neval \"$(ssh-agent -s)\"\nssh-add ~/.ssh/id_ed25519\n```\n\n**Step 3: Add key to GitHub:**\n- Copy: `cat ~/.ssh/id_ed25519.pub`\n- GitHub → Settings → SSH Keys → New SSH Key\n\n**Step 4: Test connection:**\n```bash\nssh -T git@github.com\n# Should say: 'Hi username! You've successfully authenticated'\n```\n\n**Alternative: Use HTTPS instead:**\n```bash\ngit remote set-url origin https://github.com/user/repo.git\n# Will prompt for credentials or use credential manager\n```\n\n**For organizations**: May need SSO authorization for the SSH key.",
            "guardrail": "authentication_failure"
        }
    ),
    # LFS errors
    (
        "Context: 'git clone' fails with 'Smudge error' or 'LFS: Client error'\nTask: Clone repository that uses Git LFS",
        {
            "action": "guide",
            "response": "Git LFS isn't properly set up or there's an access issue.\n\n**Step 1: Install Git LFS:**\n```bash\n# macOS\nbrew install git-lfs\n# Ubuntu\nsudo apt install git-lfs\n# Windows: download from git-lfs.github.com\ngit lfs install\n```\n\n**Step 2: Clone without LFS initially:**\n```bash\nGIT_LFS_SKIP_SMUDGE=1 git clone <repo-url>\ncd repo\ngit lfs pull  # Fetch LFS files separately\n```\n\n**Step 3: If storage quota exceeded:**\n- Check LFS usage in repository settings\n- Purchase additional LFS storage or clean old files\n\n**Step 4: If authentication issue:**\n```bash\ngit lfs env  # Check LFS endpoint\ngit config --global credential.helper store  # Cache credentials\n```\n\n**Selective download:**\n```bash\ngit lfs pull --include=\"*.psd\"  # Only specific patterns\ngit lfs pull --exclude=\"*.mp4\"  # Skip large videos\n```",
            "guardrail": "external_dependency"
        }
    ),
    # Diverged branches
    (
        "Context: 'git status' shows 'Your branch and origin/main have diverged'\nTask: Sync my branch with the remote",
        {
            "action": "guide",
            "response": "Your local and remote branches have both moved forward with different commits.\n\n**Option 1: Rebase (clean history):**\n```bash\ngit fetch origin\ngit rebase origin/main\n# Resolve any conflicts if they occur\ngit push --force-with-lease\n```\n\n**Option 2: Merge (preserve all history):**\n```bash\ngit fetch origin\ngit merge origin/main\n# Creates a merge commit\ngit push\n```\n\n**Option 3: Reset to remote (discard local):**\n```bash\n# WARNING: Loses local commits\ngit fetch origin\ngit reset --hard origin/main\n```\n\n**Before deciding, see the difference:**\n```bash\ngit log --oneline main..origin/main  # Remote's new commits\ngit log --oneline origin/main..main  # Your local commits\n```\n\n**Recommendation**: If working alone on branch, rebase. If shared branch, merge.",
            "guardrail": "divergence_warning"
        }
    ),
    # Index lock
    (
        "Context: 'fatal: Unable to create .git/index.lock: File exists'\nTask: Run git command (git keeps failing with lock error)",
        {
            "action": "guide",
            "response": "A previous Git operation was interrupted, leaving a lock file.\n\n**Step 1: Check for running Git processes:**\n```bash\nps aux | grep git  # Linux/Mac\ntasklist | findstr git  # Windows\n```\n\n**Step 2: If no Git processes, remove the lock:**\n```bash\nrm -f .git/index.lock  # Linux/Mac\ndel .git\\index.lock    # Windows\n```\n\n**Step 3: If lock keeps reappearing:**\n- Check for IDE with Git integration (VS Code, IntelliJ)\n- Check for file sync tools (Dropbox, OneDrive) - don't sync .git folders!\n- Check for antivirus scanning .git folder\n\n**Prevention:**\n- Don't Ctrl+C during Git operations\n- Exclude .git from cloud sync\n- Consider `core.fsmonitor` for large repos\n\n**Related locks:**\n- `.git/refs/heads/<branch>.lock` - branch update lock\n- `.git/config.lock` - config update lock",
            "guardrail": "lock_file"
        }
    ),
    # Untracked files blocking operation
    (
        "Context: 'git checkout' says 'error: The following untracked files would be overwritten'\nTask: Switch to another branch",
        {
            "action": "guide",
            "response": "Untracked files in your working directory conflict with files in the target branch.\n\n**Option 1: Stash untracked files:**\n```bash\ngit stash --include-untracked\ngit checkout <branch>\ngit stash pop  # Restore after switching\n```\n\n**Option 2: Move files temporarily:**\n```bash\nmkdir ../temp-untracked\nmv conflicting-file.txt ../temp-untracked/\ngit checkout <branch>\n# Decide what to do with saved files\n```\n\n**Option 3: Delete untracked files (if not needed):**\n```bash\ngit clean -fd  # DANGEROUS: Deletes untracked files and directories\ngit clean -fdn # Dry run first (shows what would be deleted)\ngit checkout <branch>\n```\n\n**Option 4: Add to .gitignore (if they should always be ignored):**\n```bash\necho \"conflicting-file.txt\" >> .gitignore\ngit checkout <branch>\n```\n\n**Investigation:**\n```bash\ngit ls-tree <branch> -- conflicting-file.txt  # See if file exists on target\n```",
            "guardrail": "untracked_conflict"
        }
    ),
    # Too large to push
    (
        "Context: 'git push' fails with 'this exceeds file size limit of 100.00 MB'\nTask: Push my repository to GitHub",
        {
            "action": "guide",
            "response": "GitHub rejects files larger than 100MB. You need to remove the file from Git history.\n\n**If file is in the last commit:**\n```bash\ngit reset --soft HEAD~1  # Undo commit\n# Add file to .gitignore\necho \"large-file.zip\" >> .gitignore\n# Re-commit without the file\ngit add .\ngit commit -m \"Your message\"\n```\n\n**If file is deeper in history:**\n```bash\n# Using git-filter-repo (recommended)\npip install git-filter-repo\ngit filter-repo --path large-file.zip --invert-paths\n\n# Force push\ngit push --force-with-lease\n```\n\n**For future large files, use Git LFS:**\n```bash\ngit lfs install\ngit lfs track \"*.zip\"\ngit add .gitattributes\ngit add large-file.zip\ngit commit -m \"Add large file via LFS\"\n```\n\n**Alternative: Store elsewhere:**\n- Use cloud storage (S3, GCS) with URLs in repo\n- Use GitHub Releases for binary attachments\n- Use package registries for artifacts",
            "guardrail": "file_size_limit"
        }
    ),
    # CRLF warnings
    (
        "Context: Git shows 'warning: LF will be replaced by CRLF' on every commit\nTask: Stop these line ending warnings",
        {
            "action": "guide",
            "response": "Git is automatically converting line endings. Configure your preference:\n\n**Option 1: Normalize to LF (recommended for cross-platform):**\n```bash\n# Configure globally\ngit config --global core.autocrlf input  # Linux/Mac\ngit config --global core.autocrlf true   # Windows\n\n# Normalize existing files\ngit add --renormalize .\ngit commit -m \"Normalize line endings\"\n```\n\n**Option 2: Use .gitattributes (best for teams):**\n```\n# .gitattributes\n* text=auto\n*.sh text eol=lf\n*.bat text eol=crlf\n*.png binary\n```\n\n**Option 3: Disable conversion (not recommended):**\n```bash\ngit config --global core.autocrlf false\n```\n\n**Refresh files after changing settings:**\n```bash\ngit rm --cached -r .\ngit reset --hard\n```\n\n**Note**: .gitattributes in the repo ensures consistent behavior for all contributors.",
            "guardrail": "line_ending_config"
        }
    ),
    # Shallow clone limitations
    (
        "Context: 'git log' only shows one commit, or 'git merge-base' fails with shallow clone\nTask: Get full repository history",
        {
            "action": "guide",
            "response": "You have a shallow clone with limited history. Let's fix it:\n\n**Check if shallow:**\n```bash\ngit rev-parse --is-shallow-repository\n# Returns 'true' if shallow\n```\n\n**Option 1: Fetch full history (unshallow):**\n```bash\ngit fetch --unshallow\n# Downloads complete history\n```\n\n**Option 2: Deepen incrementally:**\n```bash\ngit fetch --deepen=100  # Fetch 100 more commits\ngit fetch --shallow-since=\"2024-01-01\"  # Fetch since date\n```\n\n**Option 3: Fresh full clone:**\n```bash\ncd ..\nmv myrepo myrepo-shallow\ngit clone <url> myrepo  # Full clone\n# Copy any local branches/stashes if needed\n```\n\n**Why shallow clones exist:**\n- CI/CD: Faster builds when only latest code needed\n- `git clone --depth 1`: Only last commit\n- Saves time and bandwidth for large repos\n\n**Operations that need full history:**\n- `git log` (full), `git blame`, `git bisect`, `merge-base`",
            "guardrail": "shallow_limitation"
        }
    ),
    # Uncommitted changes blocking merge
    (
        "Context: 'git merge' says 'Please commit your changes or stash them before you merge'\nTask: Merge feature branch into main",
        {
            "action": "guide",
            "response": "Git won't merge with uncommitted changes to protect your work. Options:\n\n**Option 1: Commit your changes first:**\n```bash\ngit add .\ngit commit -m \"WIP: Save progress before merge\"\ngit merge feature-branch\n```\n\n**Option 2: Stash changes temporarily:**\n```bash\ngit stash\ngit merge feature-branch\ngit stash pop\n# Resolve any conflicts between stash and merged changes\n```\n\n**Option 3: Clean merge (changes can be regenerated):**\n```bash\ngit stash\ngit merge feature-branch\ngit stash drop  # Discard stashed changes\n```\n\n**Why Git requires this:**\n- Merge might need to modify files you've changed\n- Prevents confusion between merge changes and local changes\n- Allows clean abort if merge fails\n\n**If changes are in unrelated files:**\n```bash\ngit stash push -m \"unrelated work\" -- specific/file.txt\ngit merge feature-branch\ngit stash pop\n```",
            "guardrail": "uncommitted_changes"
        }
    ),
    # Refusing to merge unrelated histories
    (
        "Context: 'git pull' fails with 'refusing to merge unrelated histories'\nTask: Pull from remote repository",
        {
            "action": "guide",
            "response": "Git detected that local and remote repositories have no common ancestor. This often happens when:\n- Initialized repo locally AND separately on GitHub with README\n- Combining two separate repositories\n\n**If you want to combine them:**\n```bash\ngit pull origin main --allow-unrelated-histories\n# Resolve any conflicts\ngit push\n```\n\n**If you want remote to override local:**\n```bash\ngit fetch origin\ngit reset --hard origin/main\n```\n\n**If you want local to override remote:**\n```bash\ngit push --force origin main\n# WARNING: Destroys remote history\n```\n\n**Prevention for new repos:**\n- Either create on GitHub without README, then push\n- Or clone the GitHub repo, then add code\n\n**Never both:**\n- `git init` locally AND\n- Create repo on GitHub with initial commit",
            "guardrail": "unrelated_histories"
        }
    ),
    # Git credential issues
    (
        "Context: Git keeps asking for username/password on every push\nTask: Store credentials so I don't have to re-enter them",
        {
            "action": "guide",
            "response": "Configure Git credential storage:\n\n**Option 1: Use SSH instead of HTTPS (recommended):**\n```bash\n# Generate SSH key\nssh-keygen -t ed25519\n# Add to GitHub/GitLab\ncat ~/.ssh/id_ed25519.pub\n# Change remote URL\ngit remote set-url origin git@github.com:user/repo.git\n```\n\n**Option 2: Credential helper (HTTPS):**\n```bash\n# macOS: Use Keychain\ngit config --global credential.helper osxkeychain\n\n# Windows: Use Credential Manager\ngit config --global credential.helper manager-core\n\n# Linux: Cache for 1 hour\ngit config --global credential.helper 'cache --timeout=3600'\n\n# Linux: Store permanently (less secure)\ngit config --global credential.helper store\n```\n\n**Option 3: Personal Access Token (for HTTPS):**\n- Generate token in GitHub Settings → Developer settings → Personal access tokens\n- Use token as password when prompted\n- Token stored by credential helper\n\n**For organizations with SSO:**\n```bash\ngit config --global credential.https://github.com.provider generic\n```",
            "guardrail": "credential_config"
        }
    ),
]


# =============================================================================
# GENERATE ALL EXAMPLES
# =============================================================================

def generate_tool_examples() -> List[Dict]:
    """Generate tool selection examples."""
    examples = []
    
    # Basic tasks (30%)
    for instruction, response in BASIC_GIT_TASKS:
        examples.append({
            "system": TOOL_SYSTEM,
            "instruction": instruction,
            "response": json.dumps(response)
        })
    
    # Advanced tasks (70%)
    for instruction, response in ADVANCED_GIT_TASKS:
        examples.append({
            "system": TOOL_SYSTEM,
            "instruction": instruction,
            "response": json.dumps(response)
        })
    
    # Remote tasks
    for instruction, response in REMOTE_GIT_TASKS:
        examples.append({
            "system": TOOL_SYSTEM,
            "instruction": instruction,
            "response": json.dumps(response)
        })
    
    return examples


def generate_planning_examples() -> List[Dict]:
    """Generate multi-step planning examples."""
    examples = []
    
    for instruction, response in PLANNING_TASKS:
        examples.append({
            "system": PLANNING_SYSTEM,
            "instruction": instruction,
            "response": json.dumps(response)
        })
    
    return examples


def generate_concept_examples() -> List[Dict]:
    """Generate concept Q&A examples."""
    examples = []
    
    # Basic concepts (50%)
    for question, answer in BASIC_CONCEPTS:
        examples.append({
            "system": CONCEPT_SYSTEM,
            "instruction": question,
            "response": answer
        })
    
    # Advanced concepts (50%)
    for question, answer in ADVANCED_CONCEPTS:
        examples.append({
            "system": CONCEPT_SYSTEM,
            "instruction": question,
            "response": answer
        })
    
    return examples


def generate_error_examples() -> List[Dict]:
    """Generate error handling/guardrail examples."""
    examples = []
    
    for situation, response in ERROR_SCENARIOS:
        examples.append({
            "system": GUARDRAIL_SYSTEM,
            "instruction": situation,
            "response": json.dumps(response)
        })
    
    return examples


def generate_variations() -> List[Dict]:
    """Generate variations of common tasks for diversity."""
    examples = []
    
    # Variations of commit messages
    commit_variations = [
        "Commit with message 'Fix bug in login'",
        "Save my changes with the message 'Add unit tests'",
        "Commit the staged files with message 'Refactor database layer'",
        "Make a commit saying 'Update dependencies'",
        "Commit these changes: 'Implement user profile feature'",
    ]
    
    for instruction in commit_variations:
        msg = instruction.split("'")[1]
        examples.append({
            "system": TOOL_SYSTEM,
            "instruction": instruction,
            "response": json.dumps({
                "tool": "execute_shell",
                "params": {"cmd": f"git commit -m '{msg}'"}
            })
        })
    
    # Variations of branch operations
    branch_names = ["feature/auth", "bugfix/issue-42", "release/v2.0", "hotfix/security-patch", "experiment/new-ui"]
    for branch in branch_names:
        examples.append({
            "system": TOOL_SYSTEM,
            "instruction": f"Create a new branch called {branch}",
            "response": json.dumps({
                "tool": "execute_shell",
                "params": {"cmd": f"git checkout -b {branch}"}
            })
        })
        examples.append({
            "system": TOOL_SYSTEM,
            "instruction": f"Switch to the {branch} branch",
            "response": json.dumps({
                "tool": "execute_shell",
                "params": {"cmd": f"git checkout {branch}"}
            })
        })
        examples.append({
            "system": TOOL_SYSTEM,
            "instruction": f"Delete the {branch} branch",
            "response": json.dumps({
                "tool": "execute_shell",
                "params": {"cmd": f"git branch -d {branch}"}
            })
        })
    
    # Log variations
    log_variations = [
        ("Show me the last 20 commits", "git log --oneline -20"),
        ("Display commit history with file changes", "git log --stat"),
        ("Show commits by author john@example.com", "git log --author='john@example.com'"),
        ("Show commits from the last week", "git log --since='1 week ago'"),
        ("Display commits that modified src/app.py", "git log --follow -p -- src/app.py"),
    ]
    
    for instruction, cmd in log_variations:
        examples.append({
            "system": TOOL_SYSTEM,
            "instruction": instruction,
            "response": json.dumps({
                "tool": "execute_shell",
                "params": {"cmd": cmd}
            })
        })
    
    return examples


def main():
    """Generate all Git training data."""
    print("=" * 60)
    print("Generating Git & Version Control Training Data")
    print("=" * 60)
    
    all_examples = []
    
    print("\n1. Generating tool selection examples...")
    tool_examples = generate_tool_examples()
    all_examples.extend(tool_examples)
    print(f"   Generated {len(tool_examples)} examples")
    
    print("\n2. Generating planning examples...")
    planning_examples = generate_planning_examples()
    all_examples.extend(planning_examples)
    print(f"   Generated {len(planning_examples)} examples")
    
    print("\n3. Generating concept Q&A...")
    concept_examples = generate_concept_examples()
    all_examples.extend(concept_examples)
    print(f"   Generated {len(concept_examples)} examples")
    
    print("\n4. Generating error/guardrail scenarios...")
    error_examples = generate_error_examples()
    all_examples.extend(error_examples)
    print(f"   Generated {len(error_examples)} examples")
    
    print("\n5. Generating variations...")
    variation_examples = generate_variations()
    all_examples.extend(variation_examples)
    print(f"   Generated {len(variation_examples)} examples")
    
    # Shuffle for training
    random.seed(42)
    random.shuffle(all_examples)
    
    # Save
    save_jsonl(all_examples, "git_version_control.jsonl")
    
    # Stats
    print("\n" + "=" * 60)
    print("Git Training Data Generation Complete!")
    print("=" * 60)
    print(f"Total examples: {len(all_examples)}")
    
    # Count by type
    tool_count = len([e for e in all_examples if '"tool"' in e.get('response', '')])
    plan_count = len([e for e in all_examples if '"steps"' in e.get('response', '')])
    error_count = len([e for e in all_examples if '"guardrail"' in e.get('response', '')])
    concept_count = len(all_examples) - tool_count - plan_count - error_count
    
    print(f"  Tool selection: {tool_count}")
    print(f"  Planning: {plan_count}")
    print(f"  Concepts: {concept_count}")
    print(f"  Error handling: {error_count}")


if __name__ == "__main__":
    main()
