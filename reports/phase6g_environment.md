# Phase6G 環境與歷史保存

| Component | Actually verified |
| --- | --- |
| MG5 | 3.5.16 |
| Pythia8 | 8.317 |
| HepMC3 | 3.3.1 |
| Delphes | 3.5.1 |
| ROOT | 6.40.04 |
| CXX_standard | 20 |

既有依賴未重裝，retained source / configuration / loaded-library identity 皆通過實際檢查。Regression receipt `5b95ad39900df02eb45c5950a1c0572cd41cab7a4514ece7013729336c6acc60` 記錄16 suites、42 C++ tests、歷史 B01/B02/B03 共3000 ROOT entries 唯讀 PASS；453 個 base blobs 原始 bytes/sizes 全保留。

Original Phase6F 100-event CLI、Phase6A/B/C/D/E/F cards、source997 evidence、weights、reports 與歷史 outputs 保留。八個 portable Delphes skips 由八個 actual native tests 補足。Method/adversarial fixtures 不是新物理樣本。

新 three-process actual counts：{'MG5_source_events': 3000, 'HepMC_validated_events': 3000, 'Delphes_validated_entries': 3000, 'unique_independent_source_streams': 3, 'prefix_events_are_new_independent_statistics': False}。資料物理 gates 與 historical regression gates 分開判斷。

Three productions 全部完成後，另以final hash readback確認installed identity before/after exactly equal、453 blobs與原始 B01/B02/B03 source LHE/HMC/ROOT/cards/weights/reports/indices hashchains均不變。此final check產生0MC，不重跑historical native ROOT，原先3000-entry actual native proof保留。

[實際 regression evidence](../simulation/new_backgrounds/evidence/regressions_and_preservation.json)；[production後final preservation](../simulation/new_backgrounds/evidence/final_preservation.json)；[完整 bounded manifest](../metadata/phase6g_run_manifest.json)。

Publication repair後的最終local tests：

| Host | Discovered | Passed | Explicit skips | Seconds | Log SHA256 |
| --- | --- | --- | --- | --- | --- |
| Windows | 134 | 131 | 3 | 13.021 | cddf5e2595d5c574bacca73bd55772411800e4297f6b7c3a7a8098d7feac42dd |
| WSL | 134 | 134 | 0 | 64.396 | c67b048722a6a7bfd8279e40715dfe24cc2aec4df59045bf90a8d75b9e5fc6c3 |

Actual documented ZH `--dry-run` = `PASS_TEXT_ONLY_DRY_RUN`，0新MC。Dry-run不替代上方三條實際full1000物理鏈。
