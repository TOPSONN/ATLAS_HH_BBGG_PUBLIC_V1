# Phase6G：ZH 100-event 執行、驗證與審查

目前 **PHYSICAL_EXECUTION_AUTHORIZED=NO**。本次只完成接口與非物理測試。
Codex 必須收到使用者明確命令 `AUTHORIZE_PHASE6G_ZH_100_RUN`，才可建立
實體執行授權並生成事件。Source／CI 通過不代表已授權或已生成。

使用既有 WSL Ubuntu 與 MG5/Pythia/HepMC3/Delphes/ROOT；不必重新安裝。

## 1. 可立即執行的 dry-run

輸出目錄必須尚不存在。這個例子只建立文字計畫與精確卡片：

```bash
cd /mnt/c/HH
bash simulation/zh_pilot/scripts/generate_pilot.sh \
  --process zh --events 100 --seed 20261104 --energy 13000 \
  --output "$HOME/simulations/zh_pilot_plans/phase6g_user_dryrun_01" \
  --dry-run --max-hours 2 --max-disk-gb 5
python3 -m json.tool \
  "$HOME/simulations/zh_pilot_plans/phase6g_user_dryrun_01/execution_plan.json"
```

預期 `PASS_PHASE6G_DRY_RUN_NOT_AUTHORIZED`、events_generated=0、Gate C未授權、
D–L未評估。即使環境已有 authorization file，dry-run 也不消耗它。
`frozen/` 保存 Phase6F 卡片與 configuration；`mg5/inputs/` 保存本次
seed 的完整 process/run/param cards。`mg5/generate.mg5`／`launch.mg5`
此時只是文字，不會送給 MG5 integration。

`--energy 13000` 是總碰撞能量，GeV，每束6500。只接受 zh／100／13000；
seed可改1..900000000，其他事件數／process／energy被拒絕。不得修改已凍結
的 cuts、PDF、scale或decay卡來繞過檢查。上限不得超過2小時／5GiB。

## 2. 明確授權後的實體命令

以下步驟會授權並啟動實體生成；**目前尚未執行**。使用者可以在終端機
自行作出明確 acknowledgement；若交給 Codex 執行，先在聊天送出上述
授權命令。授權不包含採用物理 HBR，也不允許新增1000或1M樣本。

```bash
cd /mnt/c/HH
run="$HOME/simulations/zh_pilot_runs/phase6g_zh100_seed20261104"
ticket="$HOME/simulations/zh_pilot_authorizations/phase6g_zh100_01.json"

python3 -B simulation/zh_pilot/phase6g/authorize_pilot.py \
  --acknowledgement AUTHORIZE_PHASE6G_ZH_100_RUN \
  --process zh --events 100 --seed 20261104 --energy 13000 \
  --output "$run" --max-hours 2 --max-disk-gb 5 --receipt "$ticket"

PHASE6G_AUTHORIZATION_FILE="$ticket" \
bash simulation/zh_pilot/scripts/generate_pilot.sh \
  --process zh --events 100 --seed 20261104 --energy 13000 \
  --output "$run" --max-hours 2 --max-disk-gb 5
```

Ticket綁定 request、輸出路徑與執行 source SHA；24小時有效，且剩餘時間
必須容納工作上限。實體開始時原 ticket會改名為`.consumed-UUID`。
相同／不同 ticket都不能自動重跑本階段第二份100-event來源。
`.local/phase6g/physical_campaign.json` 保留一次嘗試的 reservation；
失敗時保留它及輸出，等待另行審查，不自行刪除以重試。

缺少有效 ticket時，命令在任何生成器／輸出建立前拒絕。資源不足回報
`BLOCKED_RESOURCES`。預檢要求一CPU、至少2GiB可用RAM與磁碟budget加reserve；
這些是保守最低門檻，不是已測量的ZH需求。時間／磁碟／memory-pressure
停止保護會留下partial與實際失敗紀錄；磁碟與RSS使用採樣，瞬時峰值不保證。
停止可按Ctrl+C，或在本次run建立`STOP`，不要手動替换／刪除事件。

## 3. 實體成功處理後的位置與計數

| 內容 | 相對於run的路徑 |
|---|---|
| 原始100 LHE.GZ與banner | `mg5/process/Events/zh100/` |
| 實際generator provenance／全部LHE驗證 | `validation/mg5_execution.json`、`lhe_validation.json` |
| 同來源前10筆下游smoke | `pythia/prefix10/` |
| 完整100 HepMC3／GZ | `pythia/full100/shower.hepmc3`、`shower.hepmc3.gz` |
| 原始／inclusive／effective decay tables | `pythia/full100/decay_tables_*.json`及XML |
| 每筆來源／嘗試／失敗／weight | `pythia/full100/event_ledger.jsonl` |
| 真正ReaderAscii ancestry／驗證 | `hepmc_ancestry.jsonl`、`zh_hepmc_validation.json` |
| ROOT／native readback／cutflow | `delphes/detector.root`、`native_validation.json`、`cutflow.csv` |
| 完整狀態與資源 | `run_manifest.json` |

```bash
python3 -m json.tool "$run/run_manifest.json"
python3 -m json.tool "$run/validation/lhe_validation.json"
python3 -m json.tool "$run/validation/weight_and_BR_ledger.json"
cat "$run/delphes/cutflow.csv"
sha256sum "$run/mg5/process/Events/zh100/unweighted_events.lhe.gz" \
  "$run/pythia/full100/shower.hepmc3.gz" "$run/delphes/detector.root"
```

來源截面與integration error讀LHE驗證的`cross_section_pb`／
`cross_section_uncertainty_pb`，不可用四位有效數字的終端摘要替代。
失敗紀錄會保留已寫出／已讀取／invalid／not-assessed數量；缺失證據為UNKNOWN，
不把失敗後的已寫出100筆重設成0，也不偷偷用新事件補滿。

## 4. 權重、BR與reconstruction

MG來源已含Z→bb；不得再乘ZBR。原始XWGTUP、sourceσ、完整分母100、
Info nominal與converter nominal各自保存，pb/mb僅按明列規則換算。
Forced H→γγ的conditional probability1不是physicalBR。
Phase6F Pythia模型0.0022965313147512443與CERN YR4 reference0.002270
是不同慣例；實際外部LHE初始化表另行量測並保存，不能默默替換或採用。

目前程式只允許raw simulation diagnostics，未採用外部physicalBR。
即使raw LHE/shower/ROOT全部通過，`BLOCKED_BR_WEIGHT_CLOSURE`仍可表示
exclusive物理normalization待審查；應逐項查看gates，不能解讀成校準ZH率。

Photon／jet cuts、leading photon>35GeV及mγγ105..160GeV保持Phase6C。
m_bb使用兩個leading eligible bit0-tagged native jets；不足兩個則為null。
H-origin truth/reco matching是另一份診斷，selected mγγ pair仍按原selection。
`delphes/reco_events.jsonl` 的 `H_origin_reco_match_pairs` 保存來源H photon ID、
原始native Photon index及deltaR，可逐筆追查配對；它不改變cutflow。
Native BTag bit0為FAST_SIM_ATLAS_LIKE study，沒有官方GN2/DL1校正。
100筆可能沒有完整selection survivors；只要record／detector有效，zero不構成
處理失敗，也不證明物理背景為零。不得添加luminosity或HH顯著度。

## 5. 重新驗證與選定reference發布

下列read-only命令重新驗證全部LHE與既有native receipts／SHA／CRC綁定。
它不再呼叫Pythia.next或Delphes；不以hash檢查冒充新的native physics讀回。

```bash
python3 -B simulation/zh_pilot/phase6g/validate_run.py --run "$run"
```

實體生成與獨立驗證完成後，才可準備選定的小型100-event reference：

```bash
python3 -B simulation/zh_pilot/phase6g/prepare_references.py \
  --run "$run" --output reference_samples/zh
git status --short
```

準備工具先檢查所有sizes／SHA與來源，才複製三個選定assets及bounded文字。
每個asset及三者合計限30MiB；太大則留本機。它不執行git add、commit、push
或LFS。審查實際manifest、卡片、BR限制及驗證後，才明確stage選定路徑、
檢查所有outgoing commits，再更新Draft PR。未核准PDF/PNG不stage；不merge。
本機個人run預設不發布。
