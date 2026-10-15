# Phase7F 設定鎖與積分保護操作

本版只允許隔離建置、設定初始化及 guard 測試。**新積分與新硬事件均未授權**。既有 ROOT 6.40.04／C++20、MG5 3.5.16 環境不重裝、不修改。

在 WSL Ubuntu 的 repository 根目錄執行：

```bash
# 準備四個 seed、編譯四個隔離 driver，執行初始化出口與拒絕測試。
# 此命令不執行 survey、measurement 或矩陣元素。
bash simulation/hh_signal/config_lock/integration_only.sh \
  --output "$HOME/simulations/hh_config_lock/my_plan_01"

# 驗證原生證據、完整本機 manifest、所有卡片與 seed。
bash simulation/hh_signal/config_lock/integration_only.sh \
  --output "$HOME/simulations/hh_config_lock/my_plan_01" --validate

# 必須 exit 2；在讀寫 output、啟動 native process 前拒絕。
bash simulation/hh_signal/config_lock/integration_only.sh \
  --output "$HOME/simulations/hh_config_lock/my_plan_01" --execute
```

Output 必須為新目錄，位於 `$HOME/simulations/hh_config_lock/`。重複準備會拒絕，不覆蓋、不清除原輸出。實際執行並發布證據的版本為本機 `plan_09`；其他 development plans 不是使用者操作範本，早期未含完整拒絕機制的中間 binaries 已移除 executable permission 並標示 disabled。

每個 `seed_910001`、`seed_910019`、`seed_910037`、`seed_910061` 目錄包含：

* `cards/`：reviewed、working、準備中的 embedded card、原生 include preview、param card、MG5 Banner。這不是新生成 LHE 的 banner。
* `runtime_initialization.json`：原生 PDF／αs／seed 初始化結果與數值 RGE probe。
* `native_build/process/`：831 個 hash-bound 原生 source/library/auxiliary inputs 的隔離副本，不含歷史 G1 grids／events。Symlink inputs 複製為普通檔案。
* `native_build/hh_integral_guarded`：真正編譯的 driver。初始化模式在第一個 helicity／ME 呼叫前退出；其他模式都以 `STOP 80` 拒絕積分。
* `runtime/`：空的 future stage 工作區，拒絕 stale grids。不是目前已跑過的 survey。

固定目標是 CTEQ6L1、αs(MZ)=0.130、一圈 running、`g g > h h [noborn=QCD]`、loop_sm、MH/MT/MB=125/173/4.7 GeV、κλ=κt=1、13 TeV、μR=μF=mHH/2。新 Phase7F param template 的 SMINPUTS[3] 明確設為 .130；舊 B/C 卡片完全保留。matching 的 hidden default `ickkw=0` 也改為新模板中的明確值。

Requested seed、launch request、準備的 MG5 Banner、compiled include、原生 `get_base` 與 driver pre-sampling seed 必須相等。RANMAR 在真正初始化時會將內部 common seed 乘 31300；iproc/moffset、後續 stage 增量不能冒充使用者的原始 seed。這次 probe 只讀 seed/offset files，不抽 RNG 或新相空間點。未來 measurement 的 moffset=1 是規劃，尚未執行。

Writer 保護抑制 candidate 序列化、將 native store 路徑改成只計數的 shim，並令任何直接 permanent `write_event` 呼叫終止。原版 store/unweight 演算法不會執行。磁碟掃描另外拒絕 LHE/HepMC/ROOT、events.dat、偽裝副檔名的 event records；publication guard 拒絕 sample／未核准圖片。內部動量陣列與空的 Fortran scratch unit 不等同 retained LHE。

**`NATIVE_RUNTIME_GATE=NOT_EVALUATED`**：初始化出口、synthetic writer/gate tests 與零輸出檢查都已實測，但沒有跑真正 survey。抑制 writer 會改變 candidate 狀態及可能的 RNG 消耗，不能宣稱已驗證完整 integration semantics、收斂或 transient zero-retention。`nevents=0` 不是驗收證據。

```bash
# 不需要 MG5 的 portable 檢查；CI 讀取已綁定的本機實測證據。
python3 -B -m simulation.hh_signal.config_lock.validate
python3 -B -m unittest simulation.hh_signal.config_lock.test_guards \
  simulation.hh_signal.integration_audit.test_audit \
  simulation.hh_signal.campaign.test_campaign -v
python3 -B -m simulation.hh_signal.config_lock.audit_payload
```

本版也關閉現有 HH campaign 與 child launch 的實際產生入口；dry-run 與歷史 reference 稽核保留。保護範圍是此 repository 的受控入口及本版隔離 binaries；手動執行外部 MG5 不會自動受到本程式控制。

下一階段須針對精確 source revision、lock SHA、stage budgets、零保留驗證另行取得明確授權；[authorization_contract.json](authorization_contract.json) 只是審查契約，填寫檔案、CLI token 或環境變數都不授予執行權限。準備上限為單 job、單 worker、4h aggregate wall/CPU、5 GiB 額外磁碟；不是精度／執行時間保證，也不自動擴張。

歷史 B 仍為 CTEQ6L1／一圈、actual seed21；C/D 仍為 NNPDF23 LO／兩圈。絕對截面 `INCONCLUSIVE`；κλ=2.5、5 為 `INCONCLUSIVE_REWEIGHTING`。
