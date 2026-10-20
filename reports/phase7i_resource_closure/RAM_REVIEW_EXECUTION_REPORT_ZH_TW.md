# RAM 審核後單次非壓力探測：完整驗收補件

結論：BLOCKED_FULL_CONTROLLER_AND_RUNTIME_EVIDENCE。RAM 參數已核准，完整資源工作流程尚未通過。此文件接續原 b45f0c31 報告及 RAM_REVIEW_FOLLOWUP_ZH_TW.md；不改寫歷史收據。

## 授權與來源

使用者明確核准無害測試整組 RAM 512 MiB／swap 0，未來 BUILD_ONLY 提案整組 RAM 2 GiB／swap 0。沒有正式 build、zero-ME configuration、MG5/model、ME、integration、events、Pythia、Delphes 或 Phase7I physical restart 授權。本次未建立或重用人類授權物件。

實際執行的乾淨 source commit：28b967d38f88356a1b50679ff63e0facc247c2c0。31 個執行來源／設定 snapshot：351f7e39617a75caacd6621bc9f8f99f871d46bd58b8cb61597712107d64d530。獨立來源審查只允許一次固定 true 診斷；前後來源 hash 相同。完整 tracked Git preflight 通過，wall 0.628 s、parent CPU 0.253 s；它是唯讀 source 檢查，不是 native configuration preflight。

## 實際執行及停止

命令在 exact checkout 內由已安裝 Python 執行：
    
    python3 -B -m simulation.hh_signal.final_closure.resource_closure.service_probe --output /home/btu/simulations/hh_phase7i_resource_closure/ram_review_01/nonstress_true_probe_01

這是已消耗的單次診斷，不是要求重跑的操作指令。完整 argv、profile、source hashes 與結果保存在 service_probe_execution_01.json。

實際只有 1 個 service attempt，service 只執行 /usr/bin/true。systemd 接受設定，launch exit 0；主程式 ExecMainCode=1、ExecMainStatus=0、Result=success、MainPID=0。manager CPU 計數 0.006637 s；整個 host 診斷 elapsed 0.116748 s。這些實測量不代表完整 job 的強制限額驗收。

ControlGroup 讀回空字串、MemoryPeak 未設定，沒有 kernel cgroup 限額／空群組證據，peak RAM 保留 null。stop 後 exact-unit 查詢成功，ActiveState=inactive、MainPID=0；manager_stopped_verified=true，但 kernel_cleanup=NOT_OBSERVED，cleanup_verified=false。這不是已觀察到殘留程序，也不能宣稱 kernel cleanup 已驗證。unit 卸載後的預設 infinity／Protect*=no 不是執行期間放寬設定的證據。

原始診斷工具因此保守回報 BLOCKED_EXACT_USER_SERVICE_CONFIGURATION。這個粗分類不能解讀成 namespace 啟動失敗：設定接受及 true 成功已實測；未通過的是完整 readback／kernel proof。沒有降低旗標、換 user 或補跑替代案。相依資源 matrix 已停止，47 案實際執行 0 案；RAM／CPU／disk 壓力與 filter install 均為 0。

原始探測 JSON SHA256：202ce0d350d341dd3e8cd67fa8876914b93f617fb4e636a151cc8fe9c9996f93。原始檔原樣保存，獨立解讀另存，不編輯成 PASS。

## PASS／FAIL／BLOCKED／UNKNOWN

PASS：RAM 參數明確審核；156/156 離線正反測試；81/81 固定安全 legacy；exact source Git preflight；service configuration 接受與 true exit 0；manager stop 讀回；歷史 SHA256 保存。回歸 0 failures、0 errors、0 skipped；未把 mock 正例當真實 kernel 執行。

FAIL：本輪沒有新回歸失敗或已測得資源超限。單次診斷整體未通過驗收，其原始 BLOCKED 和 UNKNOWN 值完整保存；不能因 true exit 0 改列整體 PASS。原先失敗紀錄仍在舊 commits／reports。

BLOCKED：完整 controller CPU／RAM／wall／disk 實作；持久 allocated disk 硬邊界；有效 kernel readback 與完整 cleanup 證據；47 案及全 controller 正反測試；正式 BUILD_ONLY、binary review、physical restart 與 Phase7J/K/L。

UNKNOWN：實際 kernel cgroup 限額、peak RAM、kernel 空群組證明、全工作流程 hard resource enforcement、正式 native 行為與 genuine HH convergence。不能推論整個 WSL 不支援。

## 保存、科學計數與下一關

保護 baseline 的 50,169 個 regular-path 觀測（包含宣告 links 的內容觀測）、3,588,706,711 bytes 與 122 個 symlink targets 實際重核，0 變更、0 讀取 race。scope 只含原 baseline，非整台主機。guard404dfd…、physics contracta8a093…未變；原始 MG5/PDF、B/C/D、STOP92 及其他歷史資料不改寫。

實際新增正式 builds=0、native zero-ME preflights=0、MG5=0、ME=0、integrals=0、events=0；cross section／uncertainty 仍為 null。FULL_LAUNCH_ENVELOPE_VERIFIED=false，PAYLOAD_BUSINESS_ENVELOPE_VERIFIED=false。

下一個安全工作是審查並實作同一 service 的 bounded Pre provisioning、controller、worker、receipt/postflight，處理完整生命週期預算、早期單 job mutex與持久儲存硬容量邊界。full_controller_design_review_01.json 僅是 PROPOSAL_NOT_IMPLEMENTED；沒有執行 sudo／remount／quota 設定／安裝。完成完整無害正反測試後，仍須另審新的 exact source，才可另外申請 BUILD_ONLY。RAM 核准不取代該授權。
