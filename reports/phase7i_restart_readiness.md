# Phase7I restart readiness: engineering gates only

**PASS_PRECHECK_RECOVERY_READY_FOR_REAPPROVAL. No physical restart is authorized.**

New executable-source review target: **`58d39888a024028e32f3071db9215c0db6fe0a89`**. Previous approved source: `79f779ef6d96340681242f86afe06bc90975728d`. The later commit containing this readiness report is report-only; it is not silently substituted for the source target. A future invocation must use its actual separately approved revision. This task performed no checkout and no new physical execution workspace preparation.

Three actual read-only runs of the committed enhanced precheck passed: **44.708101s, 35.950052s, 46.072576s wall; 5.055291s, 4.193602s, 4.976272s CPU**. All scanned1257tracked paths, verified required source and contract bytes, and preserved the index within each precheck. Each includes two full status scans; these totals are not a speedup comparison with a single original status. Separate plain `git ls-files` timings are recorded in the accompanying probe receipt.

Native hash closure passed in 1.844118seconds without launching the native binary. All3603stopped-attempt files, its failure receipt and all8420historical files remain unchanged. The old frozen build identity stays98aa0054eff5ffd351928bb2adb88e336e5d9fc8372dae53831ca7472d9f4281; the new Python-source binding identity is18943dd37130641e9315fd77bf728d075f2054d017ec7914d2cfb09dca2f8253. No binary was rebuilt.

The original diagnosis includes an explicitly disclosed Git2.43diff stat-cache write and timing confound. The new guard does not use that command. Source review and payload audits use read-only, content-aware comparisons rather than clearing the index or hiding files. See [root cause](phase7i_git_precheck_root_cause.md) and [equivalence review](phase7i_git_precheck_equivalence.md).

496prior-plus-new regressions,42isolated negative cases and three readonly audit-content tests passed, plus five reference validators. Existing frozen model-method proofs remain historical method evidence. None qualifies native integration behavior or convergence.

The future physical resource/physics contract is unchanged:14400aggregate CPU/wall seconds each, one job/worker,5GiB,zero retained LHE, fixed four seeds, CTEQ6L1/one-loop alpha_s and coherent multichannel0. Git preflight has its own finite120s status,180s overall wall watchdog and30s CPU budget; it does not borrow or expand that physical budget. No physical Budget/lock/stage was entered by these read-only validations.

The stopped output directory is deliberately rejected for reuse. Preparing and reviewing a future fresh output that reuses the exact native bytes is a separate decision; no physical workspace or valid execute-reviewed command was dispatched in this task.

## Final report fields

**PROJECT:** ATLAS_HH_BBGG_PUBLIC_V1

**TASK:** PHASE7I_GIT_PRECHECK_RECOVERY_V1

**BASE_SOURCE_REVISION:** 79f779ef6d96340681242f86afe06bc90975728d

**BASE_REPORT_PUBLICATION_HEAD:** 74a55b592a4f2b5271c83a52ffbe16d3734fdcd1

**REPORT_PUBLICATION_HEAD:** Containing report-only commit; exact SHA is recorded after push in PR24 and final delivery.

**GIT_TIMEOUT_ROOT_CAUSE:** Measured9p/DrvFS full index refresh caused by Windows/WSL stat-cache mismatches;1202content scans and47.072027s refresh within48.815281s status. Exact underlying Windows I/O pressure/antivirus attribution unknown.

**FILESYSTEM_TYPE:** WSL9p/DrvFS; underlying hostNTFS verified read-only

**TRACKED_FILE_COUNT:** {"baseline": 1202, "validated_new_source": 1257}

**INDEX_SIZE:** {"baseline_bytes": 155602, "validated_new_source_bytes": 162545}

**ORIGINAL_GIT_STATUS_TIMINGS:** {"qualification": "First48.815s run used mismatched stat cache; later1.047/1.357s runs followed diagnostic Git-diff stat-cache rewrite and do not establish reliable original30s operation.", "wall_seconds": [48.81528083100001, 1.0470596840000042, 1.3566056769999761]}

**ALTERNATIVE_CHECK_TIMINGS:** {"adopted": false, "diff_files_quiet_wall_seconds": [1.1987318580000021, 1.373681729999987, 4.455295172000007], "diff_index_cached_quiet_wall_seconds": [0.08154171600000382, 0.13436451699999452, 0.08568367399999488], "reason": "plumbing false-positive on timestamp-only clean fixture; not treated as equivalent without refresh"}

**NEW_FULL_PREFLIGHT_TIMINGS:** {"CPU_seconds": [5.055290782, 4.1936017670000005, 4.976272377999999], "per_command_RSS": "Actual Git child kernel ru_maxrss is recorded for each command; no aggregate parent RSS claim.", "scope": "Whole enhanced preflight with two full status scans and hashes, not directly comparable to a single original status.", "wall_seconds": [44.70810112700002, 35.950051955999925, 46.072576476999984]}

**STAGED_CHANGE_DETECTION:** PASS full status and isolated staged/outside-path/rename/replacement fixtures

**UNSTAGED_CHANGE_DETECTION:** PASS full status, exact critical bytes and whole tracked metadata race checks; no path filter

**INDEX_CONSISTENCY:** {"diagnostic_incident": "Git2.43diff stat-cache rewrite detected, disclosed and preserved; no active index repair/reset/hiding flags", "new_prechecks": "PASS_UNCHANGED_WITHIN_ALL_THREE"}

**HASH_CLOSURE:** {"native_build": "98aa0054eff5ffd351928bb2adb88e336e5d9fc8372dae53831ca7472d9f4281", "native_sources_cards_static_and_resolved_dynamic_libraries": "UNCHANGED", "new_source_binding_identity": "18943dd37130641e9315fd77bf728d075f2054d017ec7914d2cfb09dca2f8253", "physics_contract_sha256": "a8a093e2ec47283dd9cb503b2c83fe95b89df4761df5fb7afc623fa291c937cb", "status": "PASS"}

**CHECK_EQUIVALENCE:** Original full tracked status predicate retained twice, with stricter repository/path/hash/race/flag denials. Plumbing-only optimization rejected. No atomic filesystem snapshot or calibrated future latency guarantee.

**NEGATIVE_TESTS:** {"isolated_Git_and_native_hash_fixtures": 42, "readonly_audit_content_tests": 3, "status": "PASS"}

**REGRESSION_TESTS:** {"full_prior_plus_new_tests": 496, "reference_validators": 5, "status": "PASS"}

**HISTORICAL_PRESERVATION:** {"B_C_D_weights_tables_PDF_erratum_method_and_stopped_reports": "PRESERVED", "campaign": {"files": 8420, "logical_bytes": 752305317, "status": "PASS_FULL_LOCAL_SHA256_INVENTORY"}, "old_failure_receipt_sha256": "a68d27baf2a23f3a850a4cf683682eb56029cdd60e6bb7b0da2e2ea0b2b1d11e", "stopped_attempt_files": 3603, "stopped_attempt_identity": "5164541051b85a11d8ebe94c43373da88f9a2c43490a055e6afc450887c23d16"}

**EXECUTABLE_SOURCE_CHANGED:** true

**NATIVE_BINARY_CHANGED:** false

**NEW_SOURCE_REVISION:** 58d39888a024028e32f3071db9215c0db6fe0a89

**FROZEN_BUILD_IDENTITY:** 98aa0054eff5ffd351928bb2adb88e336e5d9fc8372dae53831ca7472d9f4281

**EXECUTABLE_HASHES:** {"910001": "c70949e1538fc53e2725c126a1527edf2e268c85e82e4149d3d3a1f46ccd426c", "910019": "7dc0b4150a9f0a17973e23016b679a16bde5621ab46b48f11a0d9c30badff3ff", "910037": "1a458edc8320dfe03ef8af681c5d88099f171117b8dc8746def4f2c13f79f3f6", "910061": "ff465034a83e815be7db974e26f0ff6c88215fa15fb6a76cdd20b66dbbf4f6b3"}

**REAL_NATIVE_DISPATCH:** NO

**REAL_ME_CALLS:** 0

**NEW_INTEGRALS:** 0

**NEW_HARD_EVENTS:** 0

**RESTART_AUTHORIZED:** NO

**GITHUB_CI:** Final report-publication head CI must complete after push; exact completed checks recorded in PR24 and final delivery.

**REMOTE_BLOB_VERIFICATION:** Performed after push; final head, source commit and actual blob byte/SHA verification recorded in final delivery.

**GATES_PASS:** ["full tracked Git semantics retained", "finite120s status/180s whole wall/30s CPU preflight budgets", "process-group termination and independent watchdog negatives", "exact new committed precheck passed three actual read-only runs", "496 regression tests and5 reference validators", "42 isolated Git/native-hash and3 audit-content negatives", "unchanged native build and four executable hashes", "8420 historical and3603 stopped-attempt files unchanged", "stopped output reuse rejected; no physical restart"]

**GATES_FAIL:** []

**HISTORICAL_FAILURES_PRESERVED:** ["original30-second pre-dispatch timeout", "diagnostic git diff stat-cache write despite optional locks0", "readonly audit stat-only false positive; corrected using exact/canonical byte comparisons and three tests"]

**GATES_BLOCKED:** ["separate explicit restart approval for actual source revision", "future fresh prepared output review; old stopped output immutable", "genuine native ME/PDF/alpha_s/seed/grid/writer/error/tail and convergence validation"]

**GATES_UNKNOWN:** ["exact original concurrent Windows filesystem pressure", "latency under unmeasured future load", "changes after the bounded precheck observation"]

**COMMIT_HASH:** Containing report-only commit; exact SHA after commit/push in PR24 and final delivery.

**DRAFT_PR_URL:** https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1/pull/24

**FINAL_VERDICT:** PASS_PRECHECK_RECOVERY_READY_FOR_REAPPROVAL

**NEXT_RECOMMENDED_STEP:** Review exact source58d39888a024028e32f3071db9215c0db6fe0a89, source binding and unchanged native hashes. A separate explicit restart approval and future prepared-output review are required. Do not reuse the immutable stopped directory or invoke execute-reviewed under this engineering authorization.

The exact final publication HEAD and completed CI/remote verification are filled after push in PR24 and the final local delivery report, avoiding a self-referential commit hash. All bounded source/test/evidence files remain in Draft PR24; no PDF/PNG, binary, installation/cache, event sample, merge or force push.
