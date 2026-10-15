# Phase7 最終收尾操作指南

目前判定是 **PHASE7_BLOCKED_AUTHORIZATION**。可執行的是稽核、既有資料驗證／報告、方法測試與準備；真正積分及修正 Signal 生產均未授權。
下列命令在既有 WSL Ubuntu、儲存庫根目錄執行，使用已安裝的 MG5 3.5.16、ROOT 6.40.04／C++20 與編譯器，不需重裝。
輸出必須是不存在的 `$HOME/simulations/hh_final_closure/` 子目錄；範例名稱已存在時請換新名稱。

```bash
bash simulation/hh_signal/final_closure/scripts/run_phase7_final.sh audit \
  --output "$HOME/simulations/hh_final_closure/my_audit_01"
bash simulation/hh_signal/final_closure/scripts/run_phase7_final.sh validate \
  --output "$HOME/simulations/hh_final_closure/my_validate_01"
bash simulation/hh_signal/final_closure/scripts/run_phase7_final.sh report \
  --output "$HOME/simulations/hh_final_closure/my_report_01"
bash simulation/hh_signal/final_closure/scripts/run_phase7_final.sh prepare-integration \
  --output "$HOME/simulations/hh_final_closure/my_integration_plan_01"
bash simulation/hh_signal/final_closure/scripts/run_phase7_final.sh prepare-corrected-signal \
  --output "$HOME/simulations/hh_final_closure/my_signal_plan_01"
```

五種模式均有實際程式。`audit` 核對歷史 Git 輸入、F/G 證據、B/C/D references，以及本機原始 8420 檔案。
在沒有本機完整資料的 CI host，該本機項目會標示 UNAVAILABLE；不冒稱重新讀過完整本機資料。
`validate` 檢查公開 evidence manifest、原生方法／ROOT readback receipts、獨立數值回歸與未授權狀態。
`report` 重新計算實際 C1000 的六 κ benchmark、input／selected covariance、cutflow、形狀與低 ESS 表格。
輸出 `receipt.json`、`output_manifest.json`；終端僅列簡短 JSON。失敗保留 partial 與原因，不將它當 COMPLETE。

`prepare-integration` 保存四個 seed 的卡片、空白獨立 adaptation／measurement 目錄與固定端點，並逐一建置真正 native driver。
四份 binary 只執行 **pre-ME 初始化出口及 STOP80 拒絕分支**。建置使用隔離的原始來源／library copies，歷史 MG5 與樣本不會被修改。
本次四份隔離建置實測合計約241 MB（每份約60.2 MB，十進位 logical bytes）；請讀實際 receipt 的 CPU／wall／disk，勿把這次用量當上限保證。
本版沒有可由 token 解鎖的 survey。預定 seed 為 910001、910019、910037、910061；禁止匯入 B/C grid。
adaptation 初始250、固定4輪；measurement 初始250、固定3輪；accuracy=0、min=max。原生每輪加倍 nonzero point target，零權重／切除點會使實際嘗試數更多。
measurement 只能接同一 replica 的已驗證 grid；不同 stage 不算不同獨立樣本。

`prepare-corrected-signal` 固定提出1000個新獨立硬事件、seed20261123，產生 fresh RunCardLO include 並核對 global／beam PDF、事件數與 seed。
它只有準備卡片，不執行 MG5 生產、Pythia8 或 Delphes；實際 LHE/HepMC/ROOT counts 仍是 null。
原始 C1000 是 NNPDF23 LO／兩圈，不能改名為 CTEQ6L1，也不能套一個截面比率修正形狀。

相同 mode、程式、設定、原始資料及核心證據完全一致時，才能驗證既有輸出：

```bash
bash simulation/hh_signal/final_closure/scripts/run_phase7_final.sh report \
  --output "$HOME/simulations/hh_final_closure/my_report_01" --resume
```

`--resume` 是唯讀核對；改過任一輸出、加入舊 grid、換 source/config identity 都會拒絕。沒有任意 `--events` 覆寫選項。
未來模式目前預期 exit code 2，並留下 DENIED receipt：

```bash
bash simulation/hh_signal/final_closure/scripts/run_phase7_final.sh integration \
  --output "$HOME/simulations/hh_final_closure/denied_integral_01"
bash simulation/hh_signal/final_closure/scripts/run_phase7_final.sh corrected-signal \
  --output "$HOME/simulations/hh_final_closure/denied_signal_01"
```

另行人類授權才可提出 `AUTHORIZE_PHASE7_FINAL_INTEGRATION_ONLY`，且須明確指定最終 commit、`config/physics_contract.json` SHA256、四 seed、合計 CPU／wall各4h、一job一worker、額外5GiB、暫存與零保留政策。
這段文件、命令列 `--authorization`、環境變數或 JSON 都不是授權。之後仍需審查新執行路徑並通過真正 Stage A；不會自動開始或跨 session 自動續跑。
修正1000-event 的 `AUTHORIZE_PHASE7_FINAL_SM_1000` 是另一項授權，須先滿足 Phase7I 科學先決條件，再綁定精確來源／seed／卡片／12h與20GiB上限，最多兩worker；這些不是成本保證。

要獨立重跑原生非物理方法測試，可在儲存庫根目錄執行：

```bash
python3 -B -m simulation.hh_signal.semantics_recovery.runner \
  --native "$HOME/simulations/hh_signal_runs/campaign_01/7b/source/process" \
  --output "$HOME/simulations/hh_semantics_recovery/my_method_01"
python3 -B -m unittest simulation.hh_signal.semantics_recovery.test_semantics \
  simulation.hh_signal.final_closure.tests.test_closure -v
```

這只餵固定非物理權重／候選給 native kernels，不呼叫 phase-space sampler、HH ME 或 survey。
兩路都保留原生格式化 scratch readback 與 rounding；不是 `/dev/null`，也不是只在最後刪檔。
scratch 是 unlink 的一般檔案，會使用檔案系統／page cache，直到最後 descriptor 關閉；descriptor lease 最多保留各核准 unit 的一份，下一次核准 open 或 process exit 釋放。
完整非物理 trace 與 binary 留在本機；公開只保留 hashes、數值摘要、失敗首差與 reviewed patches。
完整真實 survey 的外部 writer／transient coverage 仍未驗證。

所有歷史率與圖形僅能依原始 source/PDF、MODEL_BR_ONLY 與 detector study 範圍解讀。
κ2.5／5 保留 INCONCLUSIVE_REWEIGHTING；空 bin 的 proposal interval 不是物理背景率上限。
B01–B03 overlap、B04/B05 model BR、ttH spin、B06 photon fake、官方校準與合併 likelihood 交接 Phase8；不計算 discovery significance。
不得提交本機安裝、工作目錄、physical samples 或未核准的 PDF/PNG；push 前須稽核每個 outgoing commit 與 index。Draft PR 不會自動 merge。
