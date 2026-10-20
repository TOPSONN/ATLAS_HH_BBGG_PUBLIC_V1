# Phase13F：完整 supervisor workflow 的資源限制

本階段只有來源工程與固定無害 fixtures。**不啟動 MG5 parser／model import／ME／integration／events／Pythia8／Delphes／Phase7I**，不產生或重用 human approval。最終 PASS／FAIL／BLOCKED／UNKNOWN 與 commit／PR 連結見 `reports/phase13f_final_report.md`。

## 執行邊界

新 ext4 checkout：`/home/btu/projects/atlas_hh_phase13f_v1`；base 是 PR30 exact HEAD `aa6eb8c9abdcc4d177af2e84296180624faf835a`。既有 Phase11–13／Phase7I checkout、失敗紀錄、installed MG5/PDF 保持原樣。

完整計算工作從 user-systemd 建立的 transient `.service` 開始。Python import、source preflight、supervisor、固定 child stand-in、business receipt writing、postflight 都位於同一個 cgroup／mount namespace。管理服務與 host 測試觀察器屬控制面；它們不做 generator／source-preflight／model／scientific processing。測試觀察器的結果與兩個預先開啟的 host exports 另有固定檔案數與大小界線。

| 項目 | 固定限制與實際機制 |
|---|---|
| 累計 CPU | 4 CPU seconds ceiling；`cpu.stat`到2.5s先停止，`cpu.max=3000 10000`限整組30% core；start≤2s、run≤10s、stop100ms提供控制器失效時的保守 quota×wall bound。另每process RLIMIT_CPU2s。不是把CPUQuota誤當累計CPU limit。 |
| 總 wall | 13s envelope；systemd TimeoutStartSec2s／RuntimeMaxSec10s／TimeoutStopSec100ms，加host13s watchdog。最後cleanup只使用原剩餘時間。 |
| RAM | `MemoryMax=536870912`、`MemorySwapMax=0`、OOMPolicy=kill，實際要求memory.oom.group=1；涵蓋parent、Git、child、grandchild、tmpfs等cgroup charged memory。每process RLIMIT_AS512MiB另保留。 |
| aggregate disk | 私有tmpfs8MiB／1024inodes；所有原檔案系統唯讀。2個host stream各64KiB、最多4個host metadata各64KiB＋canary的保守總配置8,781,888 bytes，低於9MiB。 |
| child／殘留 | TasksMax8限制整組最大tasks，供supervisor/helper及對抗fixture；正常stand-in只有1個worker，並實際套用原Phase13 child guard。整組cgroup.kill涵蓋setsid後代，確認procs空且populated=0。 |
| 原始資料 | ProtectSystem=strict、ProtectHome=read-only、readonly cgroup、PrivateUsers／Network／IPC、RestrictNamespaces、NoNewPrivileges；只有私有tmpfs與bounded既開啟logFD可寫。 |

原 Phase13 child 的 CPU2s／wall3s／AS512MiB／每log64KiB沒有放寬。新profile寫在 `config/full_job_profile.json`；任何欄位、type或permission drift都拒絕，沒有CLI放寬參數。所有實際kernel值必須由worker重讀並符合profile，不能只信任requested systemd properties。

此資源驗證範圍是宣告的本機 WSL/kernel/user-systemd。CI只驗offline方法、source bytes與已保存native證據，不能宣稱其他PC或GitHub runner已重現相同kernel backend。

## 真正可執行的無害命令

```bash
cd /home/btu/projects/atlas_hh_phase13f_v1
python3 -B -m unittest discover -s analysis/phase13f/tests -v
python3 -B -m unittest discover -s analysis/phase11/tests -v
python3 -B -m unittest discover -s analysis/phase12/tests -v
python3 -B -m unittest discover -s analysis/phase13/tests -v
```

若要另做一個新的完整無害正例，先確認下面 output 尚未存在；工具會拒絕覆寫：

```bash
python3 -B analysis/phase13f/scripts/run_full_job_fixtures.py \
  --output /home/btu/simulations/hh_phase13f/run_01/user_resource_normal_01 \
  --case normal
```

不加`--case`會依固定清單依序執行31個無害正反案例；首個未符合預期的案例即停止，舊結果保留。這個命令只接受固定fixture enum，沒有任意executable或MG5入口。

## 科學與核准界線

`normal` child讀取並雜湊既有private config，只回傳bytes/SHA，不import模型。對抗child只用固定CPU loop、resident mmap頁面、sleep、檔案填滿等方法驗證外層資源界線；不改舊guard或核准旗標。CPU是cgroup統計口徑，RAM是cgroup charge口徑；記錄實際timer／kill／reap與kernel measurement粒度，不宣稱零延遲的理想即時系統。

全域installed config在本次任何fixture前就已是9326 bytes／SHA256 `5e8460eee42abcf08840b5a9d7666c1d9ae6abf92c4692abbee6428f7945b08e`，與Phase13舊9302/e456…不同，writer UNKNOWN。原Phase13private copy仍9302/e456…。本階段不改setting、不重寫舊baseline、不將9326升格為核准physics config；獨立記錄其before/after保留結果。

即使FULL_LAUNCH_ENVELOPE_VERIFIED通過，也只建立資源執行邊界。既有Phase13 parser launcher/direct child保持原hard stop，沒有改成可執行。下一關必須審查唯一受此envelope包覆的exact-source parser-only入口、configuration binding及新的明確human authorization；數值ME、integral、events仍未授權。

## 證據與來源審查

本機結果：`/home/btu/simulations/hh_phase13f/run_01`。失敗probe、被invalidated正例、未完成suite都保留。Private preservation manifest不進Git；公開的只有bounded summaries／hashes／case receipts／source／tests／Markdown，沒有config原文、PDFgrid、binary、event dump、PDF/PNG。

`independent_source_audit.py` 是獨立實作的stdlib AST、literal policy與Git原始bytes checker，不匯入envelope/worker實作；另有實際kernel與case資料檢查。這不是外部人員或另一個agent的審查，外部human review維持UNKNOWN。發布guard檢查index與每個outgoing commit的中間payload；PR維持Draft，不merge或forcepush。
