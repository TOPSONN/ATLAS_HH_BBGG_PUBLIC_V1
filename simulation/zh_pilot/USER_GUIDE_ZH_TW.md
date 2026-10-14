# Phase6F：ZH 100-event pilot 準備與 dry-run 操作

本階段只準備 source、卡片、驗證規則與本機文字計畫。**實體生成未授權**。
下列 dry-run 命令會真的檢查既有工具身分與本機資源，但不執行 MG5
integration、Pythia `next()`、shower 或 Delphes。它不會建立物理事件檔。
既有 MG5／Pythia／Delphes／ROOT 不必重新安裝。

## 1. 執行本機 dry-run

在 WSL Ubuntu 開啟 repository，使用一個尚不存在的本機輸出目錄：

```bash
cd /mnt/c/HH
bash simulation/zh_pilot/scripts/generate_pilot.sh \
  --process zh --events 100 --seed 20261104 --energy 13000 \
  --output "$HOME/simulations/zh_pilot_plans/phase6f_dryrun_01" \
  --dry-run --max-hours 2 --max-disk-gb 5
```

`--energy 13000` 是兩束合計的 pp 碰撞能量，單位 GeV；每束6500 GeV。
目前準備契約只涵蓋 zh／100 events／13 TeV。其他事件數、程序或能量
會被拒絕，不能藉此自動啟動更大樣本。seed 可改為1到900000000；
計畫會明列 MG5、Pythia、Delphes 各自將使用的 seed。相同整數對不同
隨機數引擎不代表相同序列，也不取代未來 source-event 身分／獨立性檢查。

`--max-hours 2` 是未來工作的行政停止上限；`--max-disk-gb 5` 的實際
單位為 GiB（1024³ bytes）。這些數字不是 ZH 實測時間、RAM 或磁碟預測。
dry-run 會檢查目前可用 CPU、RAM、磁碟及是否能容納磁碟 budget；
新程序的 projected wall time／peak RAM／storage 均維持 `UNKNOWN`。

若省略 `--output`，文字計畫預設留在本機
`$HOME/simulations/zh_pilot_plans/`。已存在的目錄、repository、工具安裝
與舊樣本的重疊路徑均不得覆寫。缺少 `.local/*_installation.json`、
工具指紋不符、卡片改動或不合法 request 會停止。

## 2. 檢查結果與卡片

```bash
plan="$HOME/simulations/zh_pilot_plans/phase6f_dryrun_01"
python3 -m json.tool "$plan/readiness_plan.json"
find "$plan/frozen" -type f -print
```

預期狀態是 `PASS_DRY_RUN_WITH_PHYSICAL_GATES_BLOCKED`；
`physical_execution_gate` 必須是 `NOT_AUTHORIZED`，events generated 必須為0。
`frozen/` 保存本次精確 process／run／param／decay cards 與 configuration，
`cards_and_contracts` 保存逐檔 SHA256。dry-run PASS 只代表計畫／預檢通過。
`prepared/run_card.dat` 另存本次 request 的完整 run card，只調整已允許的
nevents／iseed／兩束 beam energy，保留模板與準備版本各自的 SHA256。
這份文字卡片尚未交給任何物理生成工作；scale／PDF／其他 cuts 不因此改動。

完整工具身分檢查也可單獨執行，使用尚不存在的 receipt 路徑：

```bash
python3 -B simulation/zh_pilot/scripts/check_environment.py \
  --output "$HOME/simulations/zh_pilot_plans/environment_check_01.json"
```

可重播已公開的零事件衰變表證據：

```bash
python3 -B simulation/zh_pilot/scripts/check_decay_tables.py \
  --verify-evidence simulation/zh_pilot/evidence/decay_tables.json
```

它只檢查表格。另行執行真正的零事件初始化探針，則使用全新的本機目錄：

```bash
python3 -B simulation/zh_pilot/scripts/check_decay_tables.py \
  --output "$HOME/simulations/zh_pilot_checks/decay_check_001"
```

此探針只讀取設定、編譯本專案的小型檢查程式並初始化模型；不呼叫
`next()`，也不取代外部 LHE 的實際衰變／權重驗證。

## 3. 生產與衰變的區分

hard process 是 tree qqbar-initiated ZH，未包含 loop-induced ggZH。
優先方案在 MG5 中包含 `Z→b bbar` decay chain、保留 stable H，
再準備 Pythia `H→gamma gamma`。這保留 MG5 生產與 Z 衰變的相關性。
外部 stable-Z/H 再交給 Pythia 衰變是另一路線；其 Z 極化限制要明列。

forced decay probability=1 不等於物理 branching ratio。機器 decay IDs 是
`Z_to_b_bbar` 與 `H_to_gamma_gamma`，不使用會混淆 gluon gluon 的縮寫。
優先方案的來源截面已包含 Z 衰變，不可再乘一次 Z BR；尚缺的 H BR
也必須由獨立、具來源與寬度定義的帳本處理。原始 signed production
weights、完整 source denominator、Pythia Info weights、HepMC named
columns 與 exclusive-rate 分量會分別保存，不能默默改寫截面。

物理 BR／width 數字與採用限制請讀
[BR 契約](../../reports/phase6f_br_normalization_contract.md)；
模型原始表、強制後的有效表與物理建議值必須分清楚。

## 4. 尚未生成的輸出位置

`readiness_plan.json` 的相對路徑只描述未來工作布局：

| 工作階段 | 未來預期路徑 |
|---|---|
| MG5 production LHE | `mg5/Events/pilot100/unweighted_events.lhe.gz` |
| Pythia shower HepMC3 | `pythia/shower.hepmc3.gz` |
| Delphes ROOT | `delphes/detector.root` |
| source identity ledger | `pythia/source_events.jsonl` |
| decay／BR／validation receipts | `validation/` |

本階段不建立這些物理檔案。未來 ROOT 分析須檢查 mγγ、mbb、mbbγγ、
H-origin photons、Z-origin b quarks、native jet candidates 與既有 bit0。
原始 Delphes card 不改動；`FAST_SIM_ATLAS_LIKE` 不是官方 ATLAS 校正效率。

## 5. 驗證 profiles 與未來授權

準備的獨立 profiles 是 `ZH_STABLE`、`ZH_ZBB_STABLE_H`、
`ZH_BBGG_FORCED_DECAYS`。它們不修改既有 continuum validator，也不要求
H 衰變光子是 continuum Born photon。語法與拒絕條件可用以下命令檢查：

```bash
python3 -B simulation/zh_pilot/scripts/validate_profiles.py --help
python3 -B -m unittest discover -s simulation/zh_pilot/tests -v
```

合成 fixture 只測代數、序列化及拒絕條件；`METHOD_ONLY` 不等於物理衰變 PASS。
去掉 `--dry-run` 的請求會在任何 generator 執行前被拒絕，沒有可繞過授權
的 command-line 開關。使用者另行授權100-event pilot 後，仍需審查／完成
實體執行接口與衰變／權重閉合，才能啟用物理路徑；不能直接啟動1000或1M。

ZH 是 single-Higgs resonant background，不可靜默重算為 continuum bbγγ。
不同 process labels 不能證明 shower 後樣本互斥；未建立 stitching weights。

## 6. 本機結果與 GitHub

文字計畫預設只留本機，不自動 git add／commit／push。公開的 source、
卡片、測試與選定小型文字證據見
[最終決策](../../reports/phase6f_decision.md)。本階段沒有新的 ROOT／LHE／
HepMC reference。未核准的 PDF／PNG 不發布，PR 不自動 merge。
