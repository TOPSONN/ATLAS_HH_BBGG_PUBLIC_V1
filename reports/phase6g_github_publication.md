# Phase6G selected references 與 GitHub 狀態

| Process | Local reference status | Manifest SHA256 | Files including manifest |
| --- | --- | --- | --- |
| B04 | PASS_VALIDATED_REFERENCE_BUNDLE | 10f1484e0b1d09d5ef1c5578efba891755c5c9af96fb94c41a433cae4cbf22a9 | 30 |
| B05 | PASS_VALIDATED_REFERENCE_BUNDLE | cf2fd098a5a20e20543d871377753308d8b6f2ffa93816d8413ccf6d67abfbe2 | 30 |
| B06 | PASS_VALIDATED_REFERENCE_BUNDLE | 831eefec4ff4126e6367f7e2bc73036993c400b3f02a102fb80e87b480f6caee | 30 |

Selected references為 genuine source LHE1000.gz、full1000 shower exact first100 HepMC3.gz、actual100 ROOT及cards/native receipts。完整1000 HMC/ROOT保留本機；reference100不能替代full1000 acceptance target。No paid Git LFS、vendor/build cache、private paths、synthetic physical payload或unapproved PDF/PNG。Personal CLI outputs never automatically push。

Actual local CLI preparation and portable readback：

```json
{
  "status": "PASS_LOCAL_SELECTED_REFERENCES_PREPARED_AND_PORTABLY_VALIDATED",
  "prepared_receipt_sha256": "a4eb1cac05e3c9082583ccf086ae2110dfb942f701fda2cd24d0da8927e0145a",
  "portable_readback_receipt_sha256": "39e014b2b8b0bfae92558b65621f402336e5a8625f3389b4d456199acb34e50c",
  "files_including_manifests": 90,
  "bytes_including_manifests": 47102739,
  "processes": [
    {
      "process": "zh",
      "status": "PASS_SELECTED_REFERENCES_PREPARED_NO_GIT_ACTION",
      "manifest_sha256": "10f1484e0b1d09d5ef1c5578efba891755c5c9af96fb94c41a433cae4cbf22a9",
      "files": 30,
      "bytes": 10985747,
      "new_events_generated": 0
    },
    {
      "process": "tth",
      "status": "PASS_SELECTED_REFERENCES_PREPARED_NO_GIT_ACTION",
      "manifest_sha256": "cf2fd098a5a20e20543d871377753308d8b6f2ffa93816d8413ccf6d67abfbe2",
      "files": 30,
      "bytes": 19869688,
      "new_events_generated": 0
    },
    {
      "process": "bbgj",
      "status": "PASS_SELECTED_REFERENCES_PREPARED_NO_GIT_ACTION",
      "manifest_sha256": "831eefec4ff4126e6367f7e2bc73036993c400b3f02a102fb80e87b480f6caee",
      "files": 30,
      "bytes": 16247304,
      "new_events_generated": 0
    }
  ],
  "fresh_native_ReaderAscii_or_ROOT_during_publication": false,
  "Git_actions": "NONE_BY_PUBLICATION_CLI",
  "remote_hash_and_CI_status": "NOT_ESTABLISHED_BY_LOCAL_REFERENCE_PREPARATION"
}
```

這些本機準備/驗證未執行Git操作，也未重新執行native ReaderAscii/ROOT；native gates綁定先前真實執行的receipts。Original production bridge維持原始hash；publication-only repairs只處理exact untrimmed XML section文字hash與已綁定installed XML路徑的public logical projection，0新MG5/Pythia/Delphes、原始LHE/HMC/ROOT/cards/settings bytes不改。

[Publication-only repair evidence](../simulation/new_backgrounds/evidence/reference_publication_readback_repairs.json)。

Actual remote publication snapshot：

```json
{
  "status": "PENDING_ACTUAL_GITHUB_PUBLICATION_AND_FINAL_HEAD_CI",
  "commit_hash": "PENDING",
  "pr_url": "PENDING",
  "CI": "NOT_EXECUTED_YET",
  "remote_reference_hashes": "NOT_VERIFIED_YET"
}
```

Draft Release proposal（僅提案，未建立/上傳）：未來如經分開授權，可按 `B04_ZH_full1000.hepmc3.gz / B04_ZH_full1000.root`、B05/B06同規則發布，附exact cards、版本、SHA256與event manifests。目前完整assets SHA/bytes列於 [run manifest](../metadata/phase6g_run_manifest.json)。Ordinary Git只發布已驗證selected small references。PR維持Draft；不merge、不force-push、不自動發布Release。
