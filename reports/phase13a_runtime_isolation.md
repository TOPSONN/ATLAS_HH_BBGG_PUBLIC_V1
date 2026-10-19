# Phase13A：獨立 MG5 runtime 與寫入隔離

本報告將「實際複製」「無害 kernel fixture」與「尚未執行 MG5」分開。複製工具已實際執行；MG5 啟動、model import、process parser、ME、積分、事件產生及 Phase7I 均未執行。新 baseline 與 parser 執行仍未獲核准。

## 實際完整複製

root 的有限資源 ledger 執行 prepare_runtime.py，耗時約 3.31 秒。收據位於本機 run_01/runtime_01/isolated_runtime_identity.json 與 installed_runtime_preservation.json；可公開部分會由 root 另存至 analysis/phase13/evidence。完整來源、設定 bytes、二進位檔與 manifests 留在本機 private/，不加入 Git。

| 欄位 | 實際結果 |
|---|---|
| 原始邏輯路徑 | /home/btu/opt/mg5amcnlo |
| 原始 resolved 路徑 | /home/btu/.local/share/atlas-hh-phase6a/mg5-release-v3.5.16 |
| 獨立複本 | /home/btu/simulations/hh_phase13/run_01/runtime_01/private/mg5 |
| regular files / bytes | 4733 / 133901130 |
| symlinks / broken internal symlinks | 45 / 2 |
| 原始與複本 content manifest SHA256 | d1d4976a39c5fbd08e3a7fa4db7e42c525c40c84f7be701c1dead3f81afb9e61 |
| 原始 regular file stat identities | 複製前後相同；包含 device、inode、mtime、ctime |
| 與原始檔共享 inode | 0 |
| 複本 regular files 彼此共享 hardlink | 0 |
| 原始 config 寫入 | 0；複製前後 raw bytes/hash 相同 |

工具逐檔讀取並複製 bytes，目的檔使用 O_EXCL 建立新 inode；沒有使用 hardlink、reflink 或指向原安裝的替代路徑。來源與複本逐列比較相同的相對路徑、raw SHA、檔案大小、mode 與 symlink 文字；複製後重新讀取原始 tree，確認讀取期間未變動。此證據描述本次有界區間，不承諾未來永久不變。

45 個 symlink 都是相對且解析在各自的 tree 內；複本解析後不指向原安裝。兩個既有 broken links 明確保留，未下載或補造 target：

- Template/NLO/MCatNLO/include/pineappl_maxproc.inc → ../../SubProcesses/pineappl_maxproc.inc
- vendor/SudGen/NNPDFDriver.f → ../../Template/NLO/Source/PDF/NNPDFDriver.f

broken link 的 bytes/SHA 為 null，不能當成可用 dependency。複製來源內原有的 test LHE.gz 與 compiled caches 是既有來源內容的私有複製，並非新物理事件或經本次重新驗證的可執行產物；它們不公開至 GitHub。

## Raw config 與獨立提案

原安裝和獨立複本 input/mg5_configuration.txt 均保持 9302 bytes，SHA256：

e4567fd50d47a317407eb10cca76387053cdf06631949773296314702f77dca1

原始 line 330 的 mg5_path 指向原安裝 resolved root。這是 raw config 內的設定值，並非檔案系統 symlink；因此光有獨立複製仍不足以宣稱 MG5 未來不會存取舊路徑。

工具另存 private/config_proposals/mg5_configuration_proposed_v1.txt，只將 mg5_path 改成獨立複本路徑。提案為 9305 bytes，SHA256：

6451b6a7ebdc7bb396b3608a73ba7e7f4f01d4d0584f9acab6ff0d7a6666172f

提案狀態 PROPOSED_UNAPPROVED_UNACTIVATED；未覆蓋原安裝、未覆蓋 exact copied raw config、未自動啟用。這是明列理由且有不同 raw SHA 的新提案，不是空白正規化，也不會將舊 Phase11 gate 改成 PASS。未來若核准啟用，仍須在獨立新目標做明列的 activation receipt 與重新 hash，再進入唯讀 guard。

歷史 writer 保持 UNKNOWN；舊 Phase11 gate 保持 BLOCKED_EXTERNAL_RUNTIME_CONFIGURATION_DRIFT。相同的 formatter 行為不證明歷史實際 writer。

## HOME、TMP 與輸出

private/home、tmp、output、logs、xdg_config、xdg_cache、xdg_state 均是本次新建目錄；環境提案設定 HOME、TMPDIR、TMP、TEMP、XDG_CONFIG_HOME、XDG_CACHE_HOME、XDG_STATE_HOME，以及 PYTHONDONTWRITEBYTECODE=1。prepare 工具不以環境變數取代 OS enforcement；複製收據因此保留 ROOT_SEPARATE_ENFORCEMENT_REVIEW_REQUIRED，而未聲稱僅建立目錄就已隔離。

原始 raw copy 與 proposed config 皆保持未執行。無害 writer fixture 使用自己的輸出位置；不得為了示範而改寫 prepared runtime 的 exact config。

## 來源中可見的隱含寫入

這是靜態 source inspection，不是執行觀測或歷史 writer 歸因：

| 已安裝來源與 SHA256 | 精確來源範圍與意義 |
|---|---|
| madgraph/interface/madgraph_interface.py，be96f305974bfee0108089af04d12dac55fccbdcd7791787fc8976ce8f930bc3 | 3071–3077：constructor 可能補寫或刷新 make_opts；7233–7237：缺少設定/default run cards 時可能複製預設檔；7721–7736：save options 選擇 config 目的地並呼叫 writer。 |
| madgraph/interface/extended_cmd.py，6a4f1616ffd7910850e6776ae3f922965a757a7dee9130990e0a579b3ad70c56 | 1959–1992：讀取 HOME/XDG 設定位置與選擇 save 目標；2055–2057：以 write mode 寫 config；1618–1631：history 可寫入指定檔。 |

因此未來執行不得只靠「應該不會 save」的約定。OS guard 應拒絕任何額外寫入；若 MG5 自行嘗試更新設定、cache 或 history，該次必須 STOP，不能忽略錯誤後宣稱 parser 通過。本次沒有 import 這些 MG5 模組或執行其函式。

## Native guard 與驗證範圍

native_guard.py 提供 install(read_roots, limits)，沒有 MG5 或任意 executable dispatcher。提案精確資源設定為 cpu_seconds=2、wall_seconds=3、address_space_bytes=536870912、output_file_bytes=65536；每項需 strict integer 且不可自行擴大。2 秒 CPU／3 秒 wall 對未來 parser 可能不足；超限應誠實 STOP，不能自動延長。

預定機制為 Linux x86_64 Landlock ABI≥3，僅對明列 root 授予 READ_FILE/READ_DIR；seccomp 對未列入 syscall 使用 KILL_PROCESS。open/openat 的 write/create/truncate/append flags、fork/clone/exec/network、檔案修改 syscall 都被拒絕；write 僅允許預開且不同 regular file 的 fd1/2。子程序設 RLIMIT_AS、CPU、FSIZE、CORE、NOFILE；父程序以 wall watchdog、process group 與 PDEATHSIG 管理生命週期。未支援或安裝失敗時 fail closed。

run_resource_fixtures.py 只接受 13 項固定無害 fixture：正常 read、原 config write、複本 config write、escape symlink write、fork、exec、network、CPU spin、wall sleep、memory overflow、stdout/stderr overflow，以及獨立的 orphan group cleanup。orphan fixture 唯一允許的額外 fork 發生於 hardcoded fixture 安裝 guard 之前；並非准許未來 parser fork。

root 已實際執行全部 13 項 kernel fixtures，ledger wall 約 7.29 秒。run_01/resource_01/resource_fixture_summary.json 為 PASS_NATIVE_RESOURCE_FIXTURES；enforcement_verified=true 只描述這些 child fixtures，evidence_class=SYNTHETIC_METHOD_ONLY，不是完整 launcher 或物理驗證。原安裝與 copied raw config 在測試前後均保持 9302/e4567fd5… 相同。

| 實際 fixture | kernel / supervisor 結果 |
|---|---|
| approved read | exit 0，讀取 9302 bytes 成功 |
| 原安裝 config、copied config、escape symlink 寫入 | 各為 SIGSYS=31；沒有寫入 |
| fork、exec、network | 各為 SIGSYS=31 |
| CPU spin | SIGKILL=9，rusage CPU 2.02432 秒，wall 2.02597 秒；未觸發 wall watchdog |
| wall sleep | wall watchdog 後 SIGKILL=9；實測約 3.00986 秒 |
| 1 GiB allocation | RLIMIT_AS 下 MemoryError，固定 fixture exit 73 |
| stdout overflow、stderr overflow | 各為 SIGXFSZ=25；對應 log 恰為 65536 bytes |
| orphan cleanup | leader exit 0；已知 group 的 orphan PID 142795 被 SIGKILL，supervisor wait4 收回 |

RLIMIT_CPU 與 polling watchdog 有 kernel／排程／量測粒度，上表保留實測數字，不能把提案 2 秒／3 秒寫成所有情況下零超時的證明。read-only Landlock 和 seccomp 的 child 測試通過，也不代表 supervisor 本身已受到完整資源 envelope 約束。

最終資源 verdict 為 **BLOCKED_PHASE13_RESOURCE_ENFORCEMENT**，full_launch_envelope_verified=false。尚無獨立證據證明 supervisor 本身的 hard RAM/CPU、完整 job total wall、以及 parent receipt/disk 寫入皆受同一硬限制。這些是明確 blocker，不能用 child fixture PASS、source size precheck、有限本次 ledger 或外部程序能被終止代替。root 的 resource_enforcement_review.json 應聚合此範圍與逐項 hash；future package 必須 execution_eligible=false 並拒絕 dispatch，包含未來提供 approval file 的情形。本次不擴充成另一套未審核執行框架。

## 測試與尚未通過的 gate

runtime_layout 的 37 個可攜合成測試已實際 PASS，涵蓋 raw drift、來源 inode 替換、symlink escape/loop/broken-link、目的地 hardlink、特殊檔案、fresh output、資源大小與未核准提案。native_guard 的 25 個可攜政策測試已實際 PASS；BPF 解譯器測試驗證多種拒絕規則，但不取代真實 kernel fixture。

整體仍為 BLOCKED_PHASE13_RESOURCE_ENFORCEMENT；child resource proof=true、完整 launch envelope=false。仍未通過或未授權的 gate：MG5 startup、model import、process parser、實際 matrix-element evaluation、積分、事件、完整 physics contract binding、新 baseline approval。所有 new_MG5_processes、new_ME_calls、new_integrals、new_hard_events、new_pythia_events、new_delphes_events 均為 0。Phase7I 結果不因這份獨立複本或 guard 而自動改變。
