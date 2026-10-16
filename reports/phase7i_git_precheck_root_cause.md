# Phase7I Git precheck root cause

The original approved CLI failed in Git pre-dispatch verification, not in a native integrator or loop amplitude. Its immutable receipt remains31.11wall/1.77CPU seconds and zero native dispatch. This engineering task invoked no execute-reviewed route or native integration executable.

The actual repository is on WSL `/mnt/c`, mounted as **9p/DrvFS**, backed by host **NTFS** (verified with .NET DriveInfo). Baseline HEAD is74a55b592a4f2b5271c83a52ffbe16d3734fdcd1. It contains **1202 tracked files**,150503885working-tree logical bytes, and a **155602-byte index**. The largest tracked directories are new-background references47.10MB, HH references33.39MB, and Delphes references32.99MB. No worktree was moved; no config, reset, checkout, clean, gc, repack or skip/assume flags were used on the active repository.

## Measured bottleneck

| Probe | Repetition wall seconds |
|---|---|
| HEAD | 0.032505, 0.058233, 0.032425 |
| Index listing | 0.034784, 0.030796, 0.030088 |
| Original full status | 48.815281, 1.047060, 1.356606 |
| Staged diff | 0.116800, 0.054884, 0.083366 |
| Unstaged diff (see side effect) | 37.288568, 1.901876, 1.170563 |
| Candidate diff-index --cached --quiet | 0.081542, 0.134365, 0.085684 |
| Candidate diff-files --quiet | 1.198732, 1.373682, 4.455295 |

The slow clean status took **48.815281wall/2.171662CPU seconds**, with kernel ru_maxrss34668544bytes. Trace2 attributes47.072027seconds (about96.4percent of total) to index refresh, versus1.413071seconds to preload and about0.005712seconds to index read. It reports1202lstat operations and1202content scans during refresh; untracked enumeration was approximately0.001071seconds and disabled. HEAD/index listing were around0.03seconds. This rejects a HEAD lookup or index-file-size explanation.

Before that run, all1202index entries differed from actual WSL dev/inode/uid/gid metadata;550also differed in ctime seconds. Recorded index dev/inode/uid/gid values were0, while actual WSL values included device67 and uid/gid1000. These mismatches forced content revalidation. The low CPU compared with walltime,9p mount and refresh traces support a filesystem-backed stat/content refresh bottleneck. They do not identify a specific Windows antivirus, disk or concurrent process as the cause. strace was unavailable and was not installed; Trace2 counters are not a syscall trace.

## Observed diagnostic side effect

**The diagnostic sequence was not entirely index-immutable.** Every requested probe set GIT_OPTIONAL_LOCKS=0, yet installed Git2.43.0 `git diff --name-only` refreshed the index stat cache. The script's final before/after assertion detected this and returned1. We preserved both index hashes/stat samples and did not repair/reset the index. Index blob content remained equal to HEAD; only cached filesystem metadata changed. The changed mtime matches the end of the first unstaged-diff probe. The isolated negative fixture independently reproduces this behavior; upstream2.43.0diff source has this refresh path.

Consequently status repeats1.047060and1.356606seconds occurred after an index refresh and **do not demonstrate reliable operation of the unchanged30-second precheck**. They are retained, not averaged away or relabeled as independent cold-cache measurements. Subsequent review/audit diff commands use a transient `diff.autoRefreshIndex=false` override; this changes no repository configuration file. The runtime guard uses the original full status predicate and never that diff command.

## Bounded correction

Keep complete tracked-worktree status, with no path filter. Other Git commands retain30seconds; full status gets120seconds, about2.46times the observed48.815second slow run. An independent180second SIGALRM watchdog covers the complete Git preflight, including Python path/hash reads; its separate aggregate CPU budget is30seconds. Each Git process has a new process group, CPU/file-output limits, and group-kill/reap on failure or timeout. There are no retries. Diagnostics retain command, exit/timeout, measured wall/CPU/RSS where available, bounded stderr and stream hashes; unknown killed-process CPU/RSS remain null.

This is a finite fail-closed policy supported by this pilot, not a promise that future filesystem load cannot exceed it. The physical14400CPU/14400wall, one job/worker,5GiB,zero-LHE contract is unchanged; no physical Budget was constructed in this task.

## Primary references and evidence

- [Git status semantics and background refresh](https://git-scm.com/docs/git-status).
- [GIT_OPTIONAL_LOCKS documented behavior](https://git-scm.com/docs/git#Documentation/git.txt-GITOPTIONALLOCKS).
- [Git2.43.0diff refresh implementation](https://github.com/git/git/blob/v2.43.0/builtin/diff.c#L222-L234), and its invocation near lines575-577.
- [Git racy timestamp design](https://git-scm.com/docs/racy-git).
- Exact benchmark argv, exit/timeout,CPU/RSS and raw-output hashes: `phase7i_git_precheck_evidence/benchmarks.json`; bounded deidentified Trace2 and outputs accompany it.
- `diagnostic_outcome.json` explicitly preserves the index-write incident; `index_stat_comparison.json` preserves sampled metadata differences.
