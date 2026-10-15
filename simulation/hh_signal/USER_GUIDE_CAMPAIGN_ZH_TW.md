# ggF HH 訊號活動操作指南

在 WSL Ubuntu、專案根目錄執行。沿用已安裝的 MG5 3.5.16、Pythia 8.317、HepMC3 3.3.1、Delphes 3.5.1、ROOT 6.40.04 / C++20。程式不會下載或重裝軟體。

本活動只有兩個獨立來源：7B 的 100 事件，以及通過 7B 後才允許的 7C 新 1000 事件，合計上限 1100。7D 完全重用 7C。下游 10/100 前綴是同一來源的測試子集，不能相加成獨立統計。

先檢查命令與安全限制：

```bash
bash simulation/hh_signal/scripts/run_campaign.sh --help
bash simulation/hh_signal/scripts/run_campaign.sh \
  --phase all --process ggf_hh_sm --energy 13000 \
  --output "$HOME/simulations/hh_signal_runs/campaign_01" --dry-run
```

實際執行完整活動，依序檢查各階段的實際結果：

```bash
bash simulation/hh_signal/scripts/run_campaign.sh \
  --phase all --process ggf_hh_sm --energy 13000 \
  --output "$HOME/simulations/hh_signal_runs/campaign_01"
```

也可以逐階段執行。正式範例的 7B 命令已實際啟動；最終成功與否、實際事件數及後續階段的執行紀錄，以 `metadata/phase7_quality_gates.json` 和各階段實際收據為準。

```bash
bash simulation/hh_signal/scripts/run_campaign.sh \
  --phase 7b --process ggf_hh_sm --events 100 --seed 20261121 \
  --energy 13000 --max-hours 6 --max-disk-gb 10 \
  --output "$HOME/simulations/hh_signal_runs/campaign_01/7b"

bash simulation/hh_signal/scripts/run_campaign.sh \
  --phase 7c --process ggf_hh_sm --events 1000 --seed 20261122 \
  --energy 13000 --max-hours 12 --max-disk-gb 20 \
  --output "$HOME/simulations/hh_signal_runs/campaign_01/7c"

bash simulation/hh_signal/scripts/run_campaign.sh \
  --phase 7d --process ggf_hh_sm --events 1000 --energy 13000 \
  --max-hours 4 --max-disk-gb 10 \
  --kappa-config simulation/hh_signal/campaign/config/kappa_scan.json \
  --output "$HOME/simulations/hh_signal_runs/campaign_01/7d"
```

7B/7C 可在首次預留前指定不同合法 seed，兩者必須不同。`all` 使用上面兩個固定 seed；7D 是確定性的重加權，不接受 seed。此次審核固定 13 TeV、製程與事件數；超出範圍會明確拒絕，不能用旗標偷偷開啟額外製程、能量或大量生產。

所有物理工作共用互斥鎖，一次只執行一個工作、一個生成核心。MG5 可能顯示 loop-induced 必須使用多核心模式，但其原生有效核心數固定為 1。會監控時間、輸出大小、可用記憶體、子程序及停止標記。首次缺少快取時，先在使用者本機目錄複製既有安裝、編譯橋接工具，執行零事件模型表初始化、有限質量矩陣元素和 Ward 檢查；不會安裝軟體。失效或不完整快取不會默默替換。

輸出必須位於 `$HOME/simulations/hh_signal_runs/` 下的新目錄，不接受相對路徑、符號連結或覆寫來源。每個來源預留會記入專案本機的 `.local/phase7_campaign/campaign_registry.json`；本活動的預算已使用後，再換資料夾也不能重開額外來源。

`--resume` 只可用於原目錄、原事件數與原 seed。若完整 LHE 已存在，重新驗證同一份資料；若在積分前編譯失敗，必須先有明確的零事件證明，才能在同一預留繼續。無法證明的部分產物會阻擋自動續跑。不得刪除預留紀錄、改 seed 補失敗事件或用新的物理來源掩蓋錯誤。

各來源目錄內：

- `source/process/Events/hh_7b/` 或 `hh_7c/`：原生 `unweighted_events.lhe.gz`。
- `source/reviewed_*_card.dat`：提交給 MG5 的卡；`embedded_*_card.dat`：實際 LHE 內的卡。PDF 初始化可能覆寫強耦合；驗證以實際卡及每事件參數為準。
- `source/lhe_validation.json`：真實事件數、截面及積分誤差、權重、質量殼、四動量、尺度和 SHA256。
- `decay/`：原始來源不變；物理二體衰變的 LHE、逐事件對稱角色、母子索引、角度及四動量閉合收據。
- `stages/prefix10/`、`stages/prefix100/`、`stages/full100/` 或 `full1000/`：真實 shower、獨立 ReaderAscii、Delphes ROOT 與 native ROOT 檢查。
- `phase_receipt.json`：僅在完整來源、衰變、shower、ReaderAscii、Delphes、ROOT 都通過後才建立。
- `logs/`、`execution_*.json`、失敗收據：保留真實資源及失敗紀錄。

逐 Higgs 衰變角色為獨立、對稱的 50/50 分配，再對每顆純量作等向二體衰變，保留來源四動量。缺少的衰變因子是實際初始化模型表的 `2*BR(H→bb)*BR(H→γγ)`，只乘一次。所有產量維持 `MODEL_BR_ONLY`；外部參考 BR 與正式採用 BR 仍分開、可以是未採用。

7D 的 `event_reweights.csv` 使用相同原始四動量、每事件強耦合及尺度，直接呼叫完整有限質量矩陣元素。檢查重複 SM、κλ=0 的 HHH 頂點移除、保留點的二次式閉合、分母、離群比例、ESS 及共同事件協方差。沒有獨立 benchmark 積分時，絕對率明確為 `INCONCLUSIVE_ABSOLUTE_RATE`。

重建 cuts 固定為 Phase6C 定義，不能在此次活動改動。各次執行保存精確卡、實際隨機種子和來源 SHA。若未來要修改 cuts、能量或製程，先另立有驗證依據的版本與事件預算，保留歷史參考。

個人樣本預設只留本機。程式不會自行推送 GitHub。僅選定、通過驗證的參考 LHE 與有界 HepMC/ROOT、原始卡和來源收據可列入本活動 Draft PR；完整 1000 shower/ROOT 留本機。任何新 PDF/PNG 均須使用者核准精確版本與 SHA256 後才能提交或推送。

背景比較逐一保留 B01–B06。單位面積是 `UNIT_AREA_SHAPE_ONLY`；100 fb⁻¹ 產量是 `COMMON_LUMINOSITY_EXPLORATORY`，換算為 pb × fb⁻¹ × 1000。來源重疊、光子 fake、ttH spin、BR 和 detector 校正限制仍然存在，不計算合併物理背景、發現或排除顯著性。
