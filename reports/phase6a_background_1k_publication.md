# Phase 6A selected reference publication

目前狀態：LOCAL_VERIFIED_AWAITING_REMOTE；Gate I/J UNKNOWN。本報告會在 actual push、remote blob hash/physical validation 與 CI 成功後附加 verification receipt。

| Profile | Archive bytes | Compressed SHA256 |
|---|---:|---|
| bbgg | 166818 | `bc8f0c4a48a1db512013552afe3ec8091dddaae8b47daf7aae808d7cb767a343` |
| ccgg | 165830 | `3042fb08802e66e1582466a59e6d4dd3deabbd6fd64f91748830a09b76bae7ef` |
| jjgg | 168744 | `606b092b3c3751bfe7a900e52a3928580a7ee015a1884f7ca6e03ac260260030` |

兩個新 path：`reference_samples/mg5/pp_ccgg_sm_lo_13tev/reference_1000.lhe.gz` 和 `reference_samples/mg5/pp_jjgg_light_sm_lo_13tev/reference_1000.lhe.gz`。bbgg 路徑與 bytes 原樣保留。新 directory 各包含 README、sample_manifest 與一份 archive。LHE decompressed bytes 和 original event content 未改；只用 deterministic gzip metadata 重新包裝。實際 banner cards 原字保存，只有 log/config 本機路徑替換 placeholder；original/published SHA 與 transformation 詳列各 manifest。

Archive allowlist 精確含四份：legacy smoke100/reference1000、新 ccgg1000、light-jjgg1000。不加入 full MG5、process build directory、datasets、未選個人樣本或任何新 PDF/PNG。所有 staging 使用 explicit paths，推送前檢查 index 與 every outgoing commit，包括 intermediate payload。binary `.gitattributes` 原樣保留。

新 Draft PR base 必須是 `codex/phase6a-mg5-lo-bbgg`，head `codex/phase6a-backgrounds-1k`。PR #9 與其他 PR 不合併、不 force-push。個人產樣仍 LOCAL_ONLY，只有本次選定兩份 reference 出版。
