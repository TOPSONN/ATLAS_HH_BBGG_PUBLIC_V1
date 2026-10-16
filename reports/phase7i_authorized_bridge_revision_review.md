# Phase7 已授權積分：exact-revision review

日期：2026-10-16（Asia/Taipei）。**FINAL_VERDICT: BLOCKED_NATIVE_RUNTIME；EXECUTION_STATUS: NOT_EXECUTED_NEW_REVISION_APPROVAL_REQUIRED。**

已收到對 PR24 / `1f3c5fc4efa141a0e3e6831aa3b44c0e6bd32ee7` 的明確有界物理授權。然而該 revision 的 Python dispatcher 與 native driver 都固定拒絕物理積分。修正必然改變 implementation，依本次使用者第2條「If the implementation changes, record the new exact revision and require approval ... before physical execution」，須先交付新 commit 核准。因此未啟動 Stage A；這不是已觀察到的 genuine runtime science failure。

## 已完成的具體修正與實測

- 新獨立 bridge 保留 original computational bodies、candidate bookkeeping、RNG、formatted scratch readback、grid、停止與 error estimator；原 F/G STOP80/STOP86 及 closure CLI 不改。
- 四份真 native executables 已建置；八個 adaptation/measurement pre-ME input/config probes 通過，四個無 supervisor 入口均實際 exit80。
- 六個 computational source 投影移除明示觀測/I-O差異後，逐位元組還原 frozen original；不是用相同結果猜測等價。
- 固定 synthetic p4 probe 實際通過，錯 ren/fac scale、錯 alpha、負 PDF、NaN 均依預期停止。binary 沒有 ME/sampler symbols，沒有 genuine ME。
- Landlock 寫入拒絕、匿名 scratch、raw stdout丟棄、live CPU、wall/disk、整個 process-group 清理、parent-death kill等18項新 tests 全通過；加既有回歸共451項、五組reference validators。
- 8420原始campaign檔案再次逐一raw SHA256一致；B/C/D與舊報告不重寫。

## 科學設定審查

Physics contract SHA256：`a8a093e2ec47283dd9cb503b2c83fe95b89df4761df5fb7afc623fa291c937cb`。CTEQ6L1／αs=.130 one-loop／13TeV／finite mt,mb／κλ=κt=1／μR=μF=mHH/2。
舊 input multichannel1 啟用 matrix1.f 的 AMP2(SUBDIAG)/sum(AMP2) 分支；源碼有16 loop diagrams與1 exposed channel。不能只憑這點斷言歷史積分錯誤或重新正規化。新 input 明示 multichannel0 full coherent amplitude、exact helicity sum0、configuration1；此變更也須隨新 revision 核准。
固定 adaptation250/4輪、measurement250/3輪、accuracy0、min=max。measurement只讀自己的hash-bound adaptation grid；八組seed/offset初始化需不碰撞。

## Executable identities

| seed | SHA256 | pre-ME probes | unsupervised exit |
|---|---|---|---|
| 910001 | `c70949e1538fc53e2725c126a1527edf2e268c85e82e4149d3d3a1f46ccd426c` | 2 | 80 |
| 910019 | `7dc0b4150a9f0a17973e23016b679a16bde5621ab46b48f11a0d9c30badff3ff` | 2 | 80 |
| 910037 | `1a458edc8320dfe03ef8af681c5d88099f171117b8dc8746def4f2c13f79f3f6` | 2 | 80 |
| 910061 | `ff465034a83e815be7db974e26f0ff6c88215fa15fb6a76cdd20b66dbbf4f6b3` | 2 | 80 |

每份 executable、immutable inputs與動態library SHA固定於 executable_review.json。local build JSON改值不會替代已提交的 frozen identity。`--reviewed-revision`只核對Git identity，不授權；匿名不可修改的 supervisor memfd只證明監控存在，也不授權。

## 物理執行與統計結果

| seed | actual integral | sigma / internal error | grid / ME / tail |
|---|---|---|---|
| 910001 | NOT_EXECUTED | null / null | null / null / null |
| 910019 | NOT_EXECUTED | null / null | null / null / null |
| 910037 | NOT_EXECUTED | null / null | null / null / null |
| 910061 | NOT_EXECUTED | null / null | null / null / null |

新genuine ME=0；新integral=0；retained physical LHE=0。mean、between-replica SE及convergence皆未評估。沒有執行新hard-event production、Pythia或Delphes。

## 資源／儲存／停止政策

共享4h CPU與4h wall、一job一worker、額外5GiB。單核affinity、禁止fork、thread1、2GiB address-space subcap、32FD、64MiB/file、process-group kill。磁碟watchdog包含所有本輪review attempts與64MiB source/Git預留，2GiB保守停止以保留3GiB餘裕。
Landlock只允許三個數值output inode及private scratch可寫；source/model/library不准寫。每次writer先核對regular/unlinked/registered inode，保留descriptor lease。會有短暫libgfortran名稱及transient bytes；不冒稱無暫存寫入。FD polling有時間解析度限制，不是hard filesystem quota；真實完整coverage仍需Stage A。
stdout/stderr原始bytes在memory hash後丟棄，只留數值protocol與有界runtime error，避免保留warning裡的四向量。ME outer entry/return計數不當內部rescue總呼叫數；partial時可能只有lower-bound/latest-observed counter。
任何科學、輸出或資源gate failure都STOP，保留partial，不替換failed seed。不允許自動重跑或擴大上限。四個完成也只分列native errors、mean/SD/SE、t3 interval及其假設，不編造calibrated precision/coverage；本實作保守給INCONCLUSIVE_CONVERGENCE。

## 下一步

本次只更新同一個Draft PR24。新完整commit SHA在發布後的交付及PR描述記錄；須明確核准該SHA與上述executable identities後，才可啟動seed910001 Stage A。原授權中的四個seed與全部上限不擴張，原始1f3c5fc等歷史版本不改。
完整命令／限制見[繁中bridge指南](../simulation/hh_signal/final_closure/integration_runtime/README_ZH_TW.md)。數值證據見[manifest](../simulation/hh_signal/final_closure/integration_runtime/evidence/manifest.json)。
