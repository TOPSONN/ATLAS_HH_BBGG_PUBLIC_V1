# Phase6G 實際 full1000 HepMC3 validation

| Process | Input | Attempted | Success | Failed | Written | Validated | Next calls |
| --- | --- | --- | --- | --- | --- | --- | --- |
| B04 | 1000 | 1000 | 1000 | 0 | 1000 | 1000 | 1000 |
| B05 | 1000 | 1000 | 1000 | 0 | 1000 | 1000 | 1000 |
| B06 | 1000 | 1000 | 1000 | 0 | 1000 | 1000 | 1000 |

Full graph、units、beam-to-stable momentum/charge closure、stable mass shell、hadronization、source identity mapping、native contextual statuses 及 nominal weights 都由 actual native ReaderAscii 驗證。沒有 replacement hard events；10/100/1000 shower QA 都取相同 source indices，只有 full1000 計入 acceptance target。

B04 stable photon origin counts：`{'born_prompt': 0, 'shower_radiation': 53, 'hadron_decay': 64960, 'other': 2000}`。

B05 stable photon origin counts：`{'born_prompt': 0, 'shower_radiation': 677, 'hadron_decay': 110676, 'other': 2000}`。

B06 stable photon origin counts：`{'born_prompt': 1000, 'shower_radiation': 55, 'hadron_decay': 91080, 'other': 0}`。

B04 ancestry reader 原 dummy Particle 缺少 Event context，修正以官方 status mapping 與完整 daughter graph 對原始 prefix10 唯讀驗證後才續行。原 failed receipt 保留，producer未重播 prefix10。Actual full1000 HMC hashes、bytes 與 readback receipt hashes 見 [run manifest](../metadata/phase6g_run_manifest.json)。
