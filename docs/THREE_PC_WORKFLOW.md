# Three-PC GitHub workflow

Use the same workflow on PC1 (primary), PC2 (secondary), and PC3 (third).
Each computer has its own clone and its own GitHub login. There is no remote
access assumption and no credential sharing. Commands below run in either
PowerShell or Bash unless a block is explicitly labeled otherwise. Run each
command deliberately and stop when one fails; these blocks are not automation.

## Rules for all three computers

1. One independent task, one distinct `feature/<task-name>` branch. Assign branch
   ownership before concurrent work. Do not have two computers independently
   author the same task branch. Use a separate clone for a second concurrent
   task on the same computer.
2. `main` is the shared integration branch. The initial Step 0 infrastructure
   commit is the only bootstrap exception. Do subsequent work on task branches.
3. Start branch switches, pulls, and merges with `git status --short --branch`.
   If there are staged, unstaged, or untracked changes, stop and preserve them.
   Commit reviewed work on its existing task branch, or make a private backup
   and explicitly choose how to save it. Never automatically discard work.
4. Stage named files, inspect `git diff --cached`, and commit one task at a time.
   Avoid `git add .` and `git add -A` when unrelated work might be present.
5. Use pull requests for review. A human explicitly approves and triggers each
   merge. Do not enable auto-merge or automatically combine competing tasks.
6. Never force-push `main`. Do not rewrite published task history in this
   workflow. No hard resets, cleaning commands, or automatic commits.
7. Review staged content for credentials, internal ATLAS material, and datasets.
   `.gitignore` cannot remove a secret or dataset that is already tracked.

When giving a task to a Codex instance, state its branch and allowed files:

```text
Work only on feature/<task-name> for this task. Check the current branch and
working tree before editing. Do not work directly on main. Stop if unrelated
changes or an in-progress Git operation are present. Keep changes within the
assigned scope. Do not commit, push, or merge without explicit instructions.
```

Example allocation only: PC1 `feature/root-io`, PC2
`feature/physics-selection`, PC3 `feature/statistical-validation`.
These are future examples, not Step 0 implementations or authorizations.

## A. First-time clone on PC2 or PC3 (also valid on a new PC1)

Complete authentication in B independently on the new computer. The public
repository must already be published with `main`; an intended URL is not proof
that publication succeeded. Choose a local parent folder of your own. Do not
clone over an existing project folder. From that parent folder:

```text
git clone https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1.git
cd ATLAS_HH_BBGG_PUBLIC_V1
git status --short --branch
git remote -v
git branch -vv
```

Confirm `main` tracks `origin/main`. Open this cloned folder as a project in
Codex on that computer. Local folder names need not match across computers.
No project file relies on a user's absolute filesystem path.

Set the commit identity **locally in each clone**, using that person's chosen
name and GitHub-verified or GitHub-provided private email. Replace these two
values before running the commands; do not commit the placeholders:

```text
git config --local user.name "YOUR_CHOSEN_COMMIT_NAME"
git config --local user.email "YOUR_GITHUB_VERIFIED_OR_NOREPLY_EMAIL"
git config --local pull.ff only
git config --local push.default simple
git config --get user.name
git config --get user.email
```

Git author identity is not authentication. If using different GitHub accounts,
the repository owner must grant each account write access and each person must
accept the invitation. Without write access, public cloning works but pushing
does not. Do not distribute the owner's token as a workaround.

Run the environment check in the appropriate shell:

```powershell
powershell -NoProfile -File ./scripts/check_environment.ps1
```

```bash
bash ./scripts/check_environment.sh
```

If local PowerShell policy blocks an unsigned script, review it first. A
one-process invocation is available without changing permanent system policy:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ./scripts/check_environment.ps1
```

On Windows, use Git Bash for the Bash script; a Windows `bash.exe` command may
instead be a WSL launcher. No ROOT or CMake installation is needed for Step 0.

## B. Authenticate each computer independently

Check installed tools:

```text
git --version
gh --version
```

If `gh` is missing, stop remote creation/push work and install GitHub CLI
manually using its [official installation instructions](https://github.com/cli/cli#installation).
For Windows with WinGet, the explicit installation command is:

```powershell
winget install --id GitHub.cli --exact --source winget
```

Reopen the terminal after installation. No check script installs packages.
Authenticate on this computer, complete the browser prompt, and verify:

```text
gh auth login --hostname github.com --git-protocol https --web
gh auth status --active --hostname github.com
gh api user --jq .login
gh auth setup-git --hostname github.com
```

Stop if login or status fails. Confirm the active account has write access to
the repository. Browser or Codex GitHub-connector login alone does not establish
local Git/CLI authentication. Store credentials in the operating system's
credential store; never copy credentials between computers or commit them.

References: [gh auth login](https://cli.github.com/manual/gh_auth_login),
[gh auth status](https://cli.github.com/manual/gh_auth_status).

## C. Update local main

From a clean working tree with no merge or rebase in progress:

```text
git status --short --branch
git fetch origin
git switch main
git pull --ff-only origin main
git status --short --branch
```

If `--ff-only` fails, stop and inspect the history. Do not replace it with a
forced update. Use H or I to preserve and reconcile local work.

## D. Create a task branch

Complete C first. Replace `task-name` with a unique, descriptive lowercase name
for the assigned task; do not use the same branch for independent work:

```text
git switch -c feature/task-name
git branch --show-current
git status --short --branch
```

Confirm the current branch is `feature/task-name` before letting Codex edit.
If the branch already exists, inspect it rather than replacing it.

## E. Commit and push the task branch

Inspect the actual changes. The `README.md` path below is an example: replace
it with the specific files belonging to this task. Do not include unrelated
files or secrets:

```text
git branch --show-current
git status --short --branch
git diff
git add -- README.md
git diff --cached --stat
git diff --cached
git commit -m "Describe the single task change"
git push --set-upstream origin feature/task-name
```

Create a pull request against `main`, then fill in a concise description and
the actual checks performed in the browser:

```text
gh pr create --base main --head feature/task-name --web
```

Later pushes on the same task branch update that PR. If the remote branch has
unexpected changes, stop and inspect them; never force-push over another task.

## F. Review and merge an approved pull request

Replace `123` with the actual PR number. Review scope, base branch, changed
files, security, and any available checks:

```text
gh pr view 123 --web
gh pr diff 123
gh pr checks 123
```

Step 0 defines no CI jobs, so "no checks" is not proof of successful testing.
Record the relevant manual validation. If another authorized account performs
the review, it may submit approval explicitly:

```text
gh pr review 123 --approve
```

GitHub does not allow an author to approve their own PR. When one person owns
all three computers, have another reviewer approve or document the owner's
explicit manual review according to the chosen repository policy.

After approval, use the PR's GitHub page to merge manually. Recheck the latest
head and diff if new commits appeared after review. Do not enable automatic
merging, bypass review, or merge competing changes without resolving their
scope. Keep task branches until all affected computers have synchronized.

For enforceable protection after publication, the owner can configure a GitHub
branch rule/ruleset for `main`: require pull requests, block force pushes and
deletion, and use reviewer requirements appropriate to the available reviewers.
These repository settings must be configured and verified separately; the
documentation and local settings do not enforce server-side branch protection.

## G. Synchronize after merging

On **each** computer, save any in-progress task work first and require a clean
working tree. Then:

```text
git status --short --branch
git fetch origin
git switch main
git pull --ff-only origin main
git branch -vv
git log -1 --oneline
git status --short --branch
```

Verify that the merged change is present. Create a fresh branch with D for the
next independent task. Do not silently switch another active task onto `main`.

## H. Handle conflicts safely on a task branch

Never resolve independent task conflicts directly on `main`. Confirm the task
branch, a clean tree, and no operation already in progress. Make a private
backup before attempting unfamiliar recovery; include untracked files as well
as tracked modifications. Fetch and deliberately merge `main` into the task:

```text
git status --short --branch
git branch --show-current
git fetch origin
git merge --no-commit --no-ff origin/main
```

This deliberate command leaves a required merge commit for manual inspection;
it is not an automatic task integration. If Git says "Already up to date",
there is no merge to commit. Otherwise inspect conflicts:

```text
git status
git diff --name-only --diff-filter=U
git diff
```

Edit each conflicted file deliberately, retain the intended changes from both
sides, and remove conflict markers. Use actual resolved paths when staging:

```text
git add -- README.md
git diff --cached
git diff --check
git diff --cached --check
git status
```

Proceed only when there are no unmerged paths and relevant checks pass:

```text
git commit -m "Merge current main into task branch after conflict review"
git push origin feature/task-name
```

If the resolution is uncertain, copy any valuable new resolution work to a
private backup, then explicitly abort the merge:

```text
git merge --abort
git status
```

Do not automatically choose "ours"/"theirs" for every file or delete work to
make the conflict disappear. Coordinate overlapping file changes before retry.

## I. Recover from an interrupted push or pull

Start with inspection; do not assume the previous network operation failed
before updating the server:

```text
git status
git branch -vv
git remote -v
gh auth status --active --hostname github.com
git fetch origin
```

For an interrupted **task push**, compare both histories:

```text
git log --oneline origin/feature/task-name..feature/task-name
git log --oneline feature/task-name..origin/feature/task-name
```

If the remote task branch does not exist yet, verify its absence with:

```text
git ls-remote --heads origin refs/heads/feature/task-name
```

If only local commits are ahead (or this is the first push and the remote ref
is confirmed absent), retry the normal push:

```text
git push --set-upstream origin feature/task-name
```

If both histories differ, preserve the local commits and review an explicit
merge of `origin/feature/task-name` into the task branch using the same
`--no-commit --no-ff` procedure as H. Do not force-push.

For an interrupted **main pull**, require a clean tree with no operation in
progress and inspect divergence before retrying:

```text
git switch main
git log --oneline --left-right main...origin/main
git pull --ff-only origin main
```

If unexpected local commits exist on `main`, first preserve them under a new
unique `feature/<recovery-task-name>` branch using `git switch -c`, and stop for
review; do not reset `main` or try to force a pull. If Git reports an existing
merge/rebase, do not begin another pull: make a private backup, inspect the
operation, and explicitly finish it or choose `git merge --abort` /
`git rebase --abort` after preserving valuable resolution work. Never remove
Git lock files while a Git process may still be running.

## Owner-only Step 0 publication / resume

Use this only in the original local repository after B succeeds. It publishes
infrastructure only; do not begin Step 1. Inspect the account and local state:

```text
gh api user --jq .login
git status --short --branch
git branch --show-current
git log -1 --oneline
git ls-files
git remote -v
gh repo view TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1 --json nameWithOwner,url,visibility,defaultBranchRef
```

Require the intended authenticated owner (`TOPSONN`), a clean committed `main`,
and exactly the six Step 0 files. If the repository already exists, stop and
inspect it; do not overwrite, replace, or recreate it. A failed lookup can mean
network or permission failure, not just absence. Confirm absence using the
authenticated owner's repository listing before first creation:

```text
gh repo list TOPSONN --limit 1000 --json name,nameWithOwner
```

If the list reaches the limit, paginate or check the owner's repository page;
do not assume an incomplete list establishes absence. If `origin` already
exists from a partially completed attempt, inspect it and skip repository
creation. Only after absence is confirmed and no origin exists, deliberately
create the public repository and set its remote, without an automatic push:

```text
gh repo create TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1 --public --source . --remote origin --description "Public-data-only C++17 and CERN ROOT 6 project infrastructure"
git remote -v
```

If creation was interrupted, rerun the inspection commands rather than the
creation command. Confirm the new repository is empty and the URL is exactly
`https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1.git`. If the verified empty
repository was created but no origin was added, add it once:

```text
git remote add origin https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1.git
```

Do not run `remote add` if origin already exists. After confirming the local
commit is safe to publish and the remote has no conflicting history:

```text
git push --set-upstream origin main
gh repo edit TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1 --default-branch main
git status
git remote -v
git branch -vv
git ls-remote origin
git ls-remote --symref origin HEAD
git rev-parse HEAD
git ls-files
gh repo view TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1 --json nameWithOwner,url,visibility,defaultBranchRef
```

Confirm PUBLIC visibility, `main` as default, `main` tracking `origin/main`,
matching local and remote main commit hashes, the six intended tracked files,
and a clean tree. Verify cloning to a **new, unused** sibling folder:

```text
git clone https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1.git ATLAS_HH_BBGG_PUBLIC_V1_clone_check
git -C ATLAS_HH_BBGG_PUBLIC_V1_clone_check status
git -C ATLAS_HH_BBGG_PUBLIC_V1_clone_check rev-parse HEAD
git -C ATLAS_HH_BBGG_PUBLIC_V1_clone_check ls-files
```

That clone test is still on this computer. It cannot establish PC2/PC3 success.
Keep their status PENDING until they independently execute B, A, C, a task
branch push, an approved PR workflow, and G as applicable. Record actual evidence
per computer. Stop after Step 0; Step 1 requires explicit authorization.

Repository creation reference: [gh repo create](https://cli.github.com/manual/gh_repo_create).
