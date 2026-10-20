# Phase13F full-job resource enforcement：機制、證據與適用範圍

本報告描述固定的完整job資源設計；當前最終測試狀態與exact commit／PR見 `phase13f_final_report.md` 及 `phase13f_quality_gates.json`。不得由單一case或requested property直接宣稱 FULL_LAUNCH_ENVELOPE_VERIFIED。

## 全流程覆蓋

受保護程式是 `source/workflow.py`，由existing user-systemd在套用cgroup、namespace、RLIMIT後才exec Python。整個preflight、supervisor、固定child、business receipt writing及postflight都在該單元中。測試的pre/postflight真的核對完整Phase13 private tree content manifest及tracked Git status；不是以空白no-op替代。child是固定無害stand-in，positive child實際安裝原native_guard；沒有啟動MG5或model。

host controller只建立固定unit／採樣cgroup／停止本次unit／收集bounded scalar exports，沒有source/model/scientific preflight。source-snapshot transport metadata在host上有固定檔數／size bounds；控制面與systemd/kernel服務不包含於payload cgroup的CPU/RAM數字。這是明確的execution boundary，不是整台主機／Codex本身的resource claim。

## CPU與時間

不能把CPUQuota百分比直接稱為累計CPU秒數。此設計同時使用：

- cgroup全組quota 3000us/10000us；
- kernel cumulative cpu.stat在2.5CPU seconds即由observer提前整組終止；
- systemd start2s、runtime10s、stop100ms；
- 每processCPU2s；
- 13s整體watchdog及仍在原剩餘時間內的cleanup。

在start/runtime/stop envelope與一個quota period內的保守nominal CPU配置為 `(2+10+0.1)×0.30+0.003 = 3.633s`，低於4s ceiling；實際quota／manager timer／cleanup值另記錄，不把nominal計算冒充獨立coverage實驗。controller loss負例必須在真正controller process離開後，留下三個持續耗CPU的descendants，由獨立observer驗證systemd仍停止整個job，並核對cached最終CPU及empty/unpopulated cgroup。

## RAM

所有descendants共用MemoryMax512MiB與SwapMax0。要求實際memory.oom.group=1與OOMPolicy=kill；parent／child各自AS512MiB只是額外限制。RAM負例同時在兩個process各配置300MiB，所以必須由aggregate cgroup而非單一AS cap阻擋。MemoryPeak、Result=oom-kill及cleanup結果保留，沒有將單process上限當作aggregate證明。

## Disk與輸出

TemporaryFileSystem只有8MiB、1024inodes，host來源與cgroup控制檔readonly。host stdout/stderr是兩個預先開啟的regular files，各受64KiB RLIMIT_FSIZE限制。每case host metadata最多4檔×64KiB；含canary的總配置上界8,781,888 bytes，低於9MiB。系統/kernel自己的journal屬host OS accounting，不是job可任意寫入的event或scratch輸出；job stdout不接journal。

磁碟負例在四個phase實際填滿private tmpfs；另測零長檔案達inode quota。child的兩個diagnostic files先在相同原限額內預留pages，滿碟後仍可回報ENOSPC，不靠未捕捉的Python stdout flush錯誤推定成功。tmpfs終止後host mountpoint必須空白。

最初probe的額外ReadWritePaths host bind遮蔽了tmpfs，實際capacity約1TiB且留下inert檔，已記為失敗。移除多餘bind後實測1MiB probe及後續固定8MiB filesystem。沒有放寬限額以接受錯誤backend。

## 清理與失敗保留

cgroup.kill／KillMode=control-group／SIGKILL涵蓋setsid後代，並實際等待cgroup.procs空與populated=0。任何仍有PID、timeout或case證據不完整都不能PASS。初期observer完成branch縮排與正例assessor過寬曾導致誤判；原trial保留並有明確invalidation，新增獨立AST可達性與resource_stop負例。OOM清理競態及child滿碟失去診斷的失敗也保留；修正後需重做完整suite。

31案例：normal；preflight/child/receipt/postflight各自CPU、RAM、wall、disk、abnormal；aggregate CPU；orphan；controller loss；pids；readonly source canary；cgroup write；namespace escape；stdout overflow；inode quota；legacy missing approval。所有case的parser與物理counter為0，這是固定來源／入口的建構限制，不是genuine ME儀器量測。

## 保留與仍然阻擋的項目

本次測試前已有全域config漂移9326/5e846…，writer UNKNOWN；Phase13私有9302/e456…仍匹配。舊baseline不修改。歷史before/after SHA scope含23,221個regular path觀測及225個symlink記錄，並包括原Phases、toolchain、P13結果與之前Phase7I readonly audit；不是全主機掃描。只有新建Phase13F source/results可寫。

舊parser gate的FULL_LAUNCH_ENVELOPE_IMPLEMENTED=False及相關來源bytes不改。通過resource fixtures也不產生human approval、不啟動parser、不許ME/integrals/events。實際MG5在readonly source下的cache/history/implicit writes相容性仍UNKNOWN。外部human source review未由本任務產生或宣稱完成。
