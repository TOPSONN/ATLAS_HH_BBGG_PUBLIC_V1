# 可恢復的 Phase7I–7L 安全執行器

此執行器只實作 SAFE_ENGINEERING_AND_READ_ONLY；沒有 privileged、S4、build、MG5、ME、integration 或 event-generation dispatcher。JSON、環境變數、CLI旗標與歷史文件的PASS都不能解鎖它。人類另外批准live工作後，仍需獨立的受審executor；不能將此程式直接當成正式production控制器。

沿用原 closure 的純方法與已有表格，新增跨stage DAG、真實安全子程序exit紀錄、append-only ledger與resume核對。原device_policy、instance_binding、8×4096B evidence_slots及612／81 runners不變。這個engineering ledger與舊production slots是不同用途；普通檔案fsync不等於容量硬限制或power-loss PASS。

## 在確切且clean的checkout執行

Windows PowerShell，使用現有Python3.12以上。以下可以直接執行，沒有假UUID；`python`若不是已驗證的現有版本，請用其完整路徑，不安裝新環境：

```powershell
python -B -m simulation.hh_signal.final_closure.master plan
$masterResult = python -B -m simulation.hh_signal.final_closure.master run-safe | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw 'Safe run failed; preserve its receipt before further work' }
$masterRunId = $masterResult.run_id
python -B -m simulation.hh_signal.final_closure.master status --run-id $masterRunId
python -B -m simulation.hh_signal.final_closure.master verify --run-id $masterRunId
python -B -m simulation.hh_signal.final_closure.master resume-safe --run-id $masterRunId
python -B -m simulation.hh_signal.final_closure.master export-review --run-id $masterRunId
```

Linux只有在既有、已確認啟動的shell執行；這些命令不會從Windows啟動WSL：

```bash
python3 -B -m simulation.hh_signal.final_closure.master plan
master_result=$(python3 -B -m simulation.hh_signal.final_closure.master run-safe)
master_run_id=$(printf '%s' "$master_result" | python3 -c 'import json,sys; print(json.load(sys.stdin)["run_id"])')
python3 -B -m simulation.hh_signal.final_closure.master verify --run-id "$master_run_id"
python3 -B -m simulation.hh_signal.final_closure.master resume-safe --run-id "$master_run_id"
python3 -B -m simulation.hh_signal.final_closure.master export-review --run-id "$master_run_id"
```

正式進度固定在checkout `.local/master_progress_v1/<新UUID>/`，不能以`--output`改到歷史目錄。`run-safe`預設不派送host/guest查詢；G1缺input時仍繼續沒有依賴它的安全分析。若`run-safe`非零退出，先保留其原始JSON與run ID，不繼續把失敗當成功；直接用status檢查。

若已有本機受保護的host capture，可以在**建立新run**時以`--host-capture`提供路徑。程式只做bounded讀取、來源hash核對及去識別投影，不認證輸入來源、不啟動distro。不要公開原始資料或把手動JSON當host attestation。新capture或新source要用新run，不能重綁舊run。

## 進度與恢復

- `ledger/000001.json`等事件以exclusive create寫入，含前一筆SHA、source/input SHA、stage、monotonic起訖、argv identity、真正子程序exit及output manifest。
- 同run的協作controller使用非阻塞OS檔案鎖；這不是對惡意同UID程序的production隔離。
- `MASTER_PROGRESS.json`、`MASTER_STATUS_ZH_TW.md`、`MASTER_BLOCKERS.json`、`MASTER_SOURCE_MANIFEST.json`、`MASTER_TEST_SUMMARY.json`、`MASTER_NEXT_AUTHORIZATION.md`是可重建的latest views；每次舊版本保留在snapshots。
- resume先核對exact revision、來源、input及所有已記錄output。成功、失敗或blocked的既有stage不會自動重跑。尚未開始且依賴已通過的安全stage才可執行。
- 每次核對實際重算1019份frozen inputs的SHA，不能只核對宣告manifest或host capture。唯一已知CI路由差異以精確相容規則獨立記錄，其他資料漂移拒絕。
- 報告commit也會改HEAD；resume必須在run所記錄的exact source revision、同一checkout路徑進行。交付流程保留該source checkout及ignored進度，另保存delivery commit；不自動重綁報告HEAD或修改舊receipt。
- RUNNING中斷會留下UNKNOWN；前次child是否退出無法確認時，不補跑、不猜PID所有權、不接著啟動新child。
- 不同invocation的monotonic時間不拿來計跨boot duration。未執行的kernel資源或物理測量保持null。

本機檢查上限：16個runs、每run128個ledger events、64份snapshots、16份exports、每event32768B、每stage128個檔案且單檔2MiB；整run4096個檔案、logical bytes64MiB。單child retained log65536B、soft wall timeout120s、一次一個safe child。部分容量檢查在寫入後進行，不能防止暫時超額；這些是可審查的工程軟界限，**不等於CPU/RAM/allocated-disk/full-workflow kernel hard envelope**。

`export-review`只複製明列的摘要，沒有raw inventory、source event rows、ROOT/LHE/HepMC、private traceback、binary或PDF/PNG。發布仍須獨立跑 `python -B -m simulation.hh_signal.final_closure.master.publication`，檢查全部outgoing commits與index；export本身不等於批准push。

## 下一個外部關卡

先取得可讀的host inventory、確認既有guest/session與實際controls/storage。選擇原A的其他可控制平台，或逐條審B1–B8與新VM成本歸屬提案。provisioning、S4、完整resource matrix、BUILD_ONLY、binary人類review、physical restart、SM1000分別批准，不能相互繼承。

沒有真實device、guest workspace或binary時，review request會明列null與blockers，不能稱為可直接執行的完整批准套件，也不能拿舊104-token scope替新source授權。
