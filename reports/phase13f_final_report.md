# Phase13F 完整驗收報告

**FINAL_VERDICT：FULL_LAUNCH_ENVELOPE_VERIFIED（限本機宣告的無害完整流程）**

Base：PR30，`aa6eb8c9abdcc4d177af2e84296180624faf835a`；新分支：`codex/phase13f-full-job-resource-closure`。本報告的第一個 source/evidence commit 與新 stacked Draft PR 在 delivery commit 補入；舊 PR24–30 保持 OPEN/DRAFT、head 不變。

## PASS：實際完整工作流程

`workflow_final_05` 真正執行了31個固定正反案例，31/31符合預期；其最終來源 snapshot identity：`6a7ab32f5f4c261eee2e840d4d3cf567bde7b736b6129bc45e805f91510a9fd5`。source preflight、supervisor、child stand-in、business receipt writing、postflight全部在套用cgroup／namespace／RLIMIT之後才啟動。正例真的完成四階段與完整private runtime前後雜湊，child真的套用原native_guard，沒有MG5或model import。

| 資源 | 固定限制 | 實際證據 |
|---|---|---|
| aggregate CPU | 4 CPU seconds；2.5s累計watchdog；cpu.max=3000/10000、burst0；配合start2s/run10s/stop100ms | 全31case最大全組CPU：3.018297 s；控制器真正退出後仍持續耗CPU，最後由systemd runtime timeout終止；不是單把quota當累計上限。 |
| aggregate RAM | 512MiB，swap0，memory.oom.group1，OOMPolicykill | 四階段各自兩個300MiB process觸發真正group OOM；最大全組MemoryPeak：536870912 bytes。 |
| total wall | 13s完整payload envelope；manager start/runtime/stop與remaining-deadline cleanup | 最長含host cleanup：10.157736859999659 s；raw monotonic start/exit及controller-loss timeout逐案保存。 |
| aggregate disk | private tmpfs8MiB/1024inodes；兩個host log各64KiB；至多四個metadata各64KiB；9MiB ceiling | 四階段實際ENOSPC；inode0負例；stdoutSIGXFSZ；host工作目錄終止後空白；固定輸出配置保守上界8781888 bytes。 |
| 殘留與逃逸 | 整個cgroup kill、procs空且populated0；readonly source/cgroup、限制namespace與tasks | setsid orphan被發現並清除；controller-loss cleanup驗證；PID上限、source canary write/cgroup write/namespace escape皆拒絕。 |

31案例清單、每案真實kernel值、Result/exit、CPU/MemoryPeak/wall、launch來源身份及host輸出hash見 [final suite](../analysis/phase13f/evidence/final_suite/suite_summary.json)、[逐案數值](../analysis/phase13f/evidence/final_native_metrics.json)、[live cleanup](../analysis/phase13f/evidence/post_suite_live_cleanup.json)。原child CPU2s/wall3s/AS512MiB/log64KiB沒有放寬；新固定profile欄位或type改動均拒絕。

CPU quota×start/runtime/stop的保守nominal配置3.633s<4s；實際值另量測，不把理想timer公式當作硬即時系統保證。控制面systemd/kernel與host測試觀察器不包含在payload CPU/RAM統計中；觀察器只做固定unit transport/termination與bounded exports。這不是整台主機或Codex程序的CPU/RAM驗證，也不是其他PC的驗收。

## PASS：回歸、來源審查與歷史保留

| 審查 | 實際結果 | 證據 |
|---|---|---|
| Phase11 | 172 tests PASS | `analysis/phase13f/evidence/phase11_regression_01.txt` |
| Phase12 | 167 tests PASS | `analysis/phase13f/evidence/phase12_regression_01.txt` |
| Phase13 | 188 tests PASS | `analysis/phase13f/evidence/phase13_regression_01.txt` |
| Phase13F | 48 tests PASS；含13項獨立data-only raw receipt檢查 | `analysis/phase13f/evidence/phase13f_regression_01.txt` |
| 合計 | 575 tests PASS；另31項真實native cases | 沒有把offline tests宣稱為MG5執行。 |
| 獨立實作來源審查 | 736 checks PASS；stdlib AST/literal policy/Git bytes；不import producer | `analysis/phase13f/evidence/independent_source_audit.json` |
| 歷史SHA256 | 23221 regular path observations、5094843289 bytes、225 symlink records；本任務前後0變更 | `analysis/phase13f/evidence/historical_preservation_summary.json` |

保留scope涵蓋原Phases、安裝toolchain/MG5/PDF、舊P13結果與私有runtime，以及既有Phase7I唯讀稽核資料；沒有執行Phase7I。完整private preservation manifest只留本機，公開summary與SHA，沒有全主機完整性宣稱。原P13四個blocker receipt、launcher、direct child、native_guard、contract bytes保留；沒有翻轉舊FULL_LAUNCH_ENVELOPE_IMPLEMENTED=False來讓驗收過關。新backend經實測後另立證據，不改寫舊cgroup探測結論。

## FAIL：歷史失敗與既有設定差異

完整保留初始tmpfs被ReadWritePaths遮蔽的probe；unsupported MemoryOOMGroup property；observer完成branch縮排與過寬正例判定；OOM cleanup race；滿碟後child stdout診斷失敗。最早錯誤正例有明確invalidation；後來完整`workflow_final_01`也保留並標明被更嚴格controller-loss檢查取代。修正沒有提高限額；最終使用全新`workflow_final_05`完整重測，未挑選失敗case後用旗標偽造PASS。詳見 `analysis/phase13f/evidence/preserved_attempts/` 及invalidation JSON。

本任務任何fixture開始前，installed全域MG5 config已是9326 bytes／SHA256 `5e8460eee42abcf08840b5a9d7666c1d9ae6abf92c4692abbee6428f7945b08e`，與P13 baseline9302 bytes／`e4567fd50d47a317407eb10cca76387053cdf06631949773296314702f77dca1`不符。這項identity comparison為FAIL；writer **UNKNOWN**。本任務前後該9326設定未變，P13 private9302/e456亦未變，舊baseline不修改；沒有將drifted config升格為核准設定。

## BLOCKED／UNKNOWN：下一關

- **BLOCKED**：下一次parser-only執行。必須先釐清config drift/provenance，審查唯一受envelope保護的exact-source入口與configuration binding，再取得新的明確人類授權。舊launcher/direct child保持hard stop；此PR沒有實際MG5 dispatcher或核准物件。
- **BLOCKED**：ME、integration、events、Pythia8、Delphes、Phase7I，以及任何物理正規化／背景解釋。沒有新物理計算授權。
- **UNKNOWN**：真實MG5在readonly source下的cache/history/implicit write相容性；其他PC或GitHub runner的native backend；全域config差異的外部來源。
- **UNKNOWN**：外部人員／另一agent的來源審查未執行。這裡的independent指獨立實作、不匯入producer的AST/byte/data checker，不冒充外部審核。

MG5_INVOCATIONS=0；NEW_ME_CALLS=0；NEW_INTEGRALS=0；NEW_HARD_EVENTS=0；NEW_PYTHIA_EVENTS=0；NEW_DELPHES_EVENTS=0；PARSER_EXECUTED=false；HUMAN_AUTHORIZATION_CREATED=false。

## GitHub與交付

只發布來源、tests、Markdown與有界數值收據；無PDF/PNG、私有設定原文、PDFgrid、binary、event dump。每次push前檢查index及所有outgoing commit的中間payload。新PR保持Draft、stack在PR30；不merge、不forcepush。

SOURCE_PAYLOAD_COMMIT：PENDING_SOURCE_COMMIT
DELIVERY_COMMIT：見此報告所在的最後delivery commit；完整40位SHA於本機FINAL_REPORT.json記錄。
PR_URL：https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1/pull/31
GITHUB_CI：待exact最終source/evidence commit push後驗證；workflow只跑offline source/method與frozen native evidence，不在CI重跑MG5或native服務。

完整本機結果與各次未刪除執行目錄：`/home/btu/simulations/hh_phase13f/run_01`；新ext4 checkout：`/home/btu/projects/atlas_hh_phase13f_v1`。

NEXT_RECOMMENDED_STEP：提交exact-source parser-only入口／config provenance review後，另行取得明確授權。資源fixture驗收本身不構成parser或物理執行授權。

## 最終補充：失敗保留與exact來源

實際完整suite使用乾淨source commit `accc7cb4cb4da6f87abc204b9a986dbcc99c020a`；48項Phase13F tests加527項Phase11–13回歸，共575項。最後全部31案例來源snapshot均匹配本PR目前可執行來源。

最初stacked PR的舊Phase13 publication checker拒絕新增Phase13F路徑；原log與job結果保留。只將publication audit在Phase13F manifest存在時路由到新的additive checker，保留原fallback、全部舊regression steps；exact workflow差異及禁止`|| true`/test替換的負例均驗證。沒有放寬資源或舊parser gate。

`workflow_final_03`被clean-source preflight正確拒絕tracked edits，先commit後才重測。`workflow_final_04`的RAM負例先被CPU2s硬限終止，未取得group OOM，因此停止且不接受該輪；完整原記錄與journal保留。RAM fixture改為兩process各300MiB匿名mmap，每4096-byte page觸碰一byte，確保相同resident target並降低無關memset CPU成本；所有限額與OOM判定不變。四RAM smoke通過後，`workflow_final_05`再完整31/31通過；沒有以重複舊收據或挑選成功case拼接最終suite。
