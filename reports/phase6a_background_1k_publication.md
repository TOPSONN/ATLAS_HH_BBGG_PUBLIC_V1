# Phase 6A selected reference publication

狀態：PASS_PUBLISHED_VERIFIED_DRAFT；Gate I/J PASS。已實際 push 並從 GitHub API 重新下載 selected sample/card/provenance bytes，remote SHA 與 physics validation PASS；真正 GitHub Actions 成功。

| Profile | Archive bytes | Compressed SHA256 |
|---|---:|---|
| bbgg | 166818 | `bc8f0c4a48a1db512013552afe3ec8091dddaae8b47daf7aae808d7cb767a343` |
| ccgg | 165830 | `3042fb08802e66e1582466a59e6d4dd3deabbd6fd64f91748830a09b76bae7ef` |
| jjgg | 168744 | `606b092b3c3751bfe7a900e52a3928580a7ee015a1884f7ca6e03ac260260030` |

兩個新 path：`reference_samples/mg5/pp_ccgg_sm_lo_13tev/reference_1000.lhe.gz` 和 `reference_samples/mg5/pp_jjgg_light_sm_lo_13tev/reference_1000.lhe.gz`。bbgg 路徑與 bytes 原樣保留。新 directory 各包含 README、sample_manifest 與一份 archive。LHE decompressed bytes 和 original event content 未改；只用 deterministic gzip metadata 重新包裝。實際 banner cards 原字保存，只有 log/config 本機路徑替換 placeholder；original/published SHA 與 transformation 詳列各 manifest。

Archive allowlist 精確含四份：legacy smoke100/reference1000、新 ccgg1000、light-jjgg1000。不加入 full MG5、process build directory、datasets、未選個人樣本或任何新 PDF/PNG。所有 staging 使用 explicit paths，推送前檢查 index 與 every outgoing commit，包括 intermediate payload。binary `.gitattributes` 原樣保留。

新 Draft PR base 必須是 `codex/phase6a-mg5-lo-bbgg`，head `codex/phase6a-backgrounds-1k`。PR #9 與其他 PR 不合併、不 force-push。個人產樣仍 LOCAL_ONLY，只有本次選定兩份 reference 出版。

## Actual remote verification receipt

Draft PR：https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1/pull/11，base `codex/phase6a-mg5-lo-bbgg`；source head `d38020948bd7e766119e085cdcc7a3f441e46f6b`。PR #9 head 保持 `640bec6b64b2533bd33ac23d0a1e2e328e93e842`，仍 OPEN、未 merge。

實際遠端下載 49 個 sample/manifest/README/card/provenance files，compressed/decompressed/event-content SHA、4 個 sample archives（含 smoke regression）、LHE/card/cut/PDG 檢查均 PASS；reference3000、smoke100 另計。完整 local/GitHub Git blob tree 147 files identity 相同。每個 remote fetched file SHA/bytes/blob ID 詳見 `simulation/mg5/evidence/background_1k/github-source-verification.json`。

GitHub CI actual run：https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1/actions/runs/38240760152；completed success，四個必需 validator/library/adversarial/payload steps 全部 success，Actions log 實際顯示 Ran59tests、OK。NO_CHECKS 未用作 PASS。

此 receipt 綁定已驗證的 source/sample commit。後續 seal commit 只保存 verification reports/metadata；其 final head 會再次下載核對並檢查真正 CI，精確 final hash 在本機 final report/receipt 記錄，避免在 commit 內宣稱它自己的尚未存在 hash。
