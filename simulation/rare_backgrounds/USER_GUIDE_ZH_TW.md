# 條件式稀有背景統計操作指南

本模組讀取既有 bbgg／ccgg／jjgg 各 1000 個已驗證事件，進行條件式
b-tag 數值分析，沒有新增 MG5、Pythia 或 Delphes 事件。三程序仍各有
1000 個原始硬事件；重用前段、改 tag 機率或重算解析期望值都不增加
獨立統計。新 bbγj、ttH、ZH 仍只是 feasibility proposal，不能把本模組
當作這些程序的事件生成器。
最終 Linux Python3.12 controller 指令已實際執行完整 3000 個來源事件、
全部九種情境；另行執行的最終 51 個 tests 全部通過、零 skip。重新輸出的 `analysis.json`
及三個 conditional summary 與 public 結果逐位元組相同。最終分析 SHA256
為 `23fa2f4a3669c2c8bf97d422e428abda90abd67c15872e0ae8830fd9ddc57b79`。
這是數值／來源綁定驗證，不是新 MC，也不是 calibrated background prediction。

## 1. 執行環境與數值輸入

在 Windows PowerShell 輸入 `wsl -d Ubuntu`，以下在 WSL 執行：

```bash
cd /mnt/c/HH
python3 --version
sha256sum simulation/rare_backgrounds/evidence/pilot/bbgg.jsonl
python3 -m json.tool simulation/rare_backgrounds/evidence/pilot/bbgg_binding.json
```

解析標記工具只用 Python 標準函式庫，不重新安裝 generator 或 ROOT。
`evidence/pilot` 是從實際 ROOT 獨立讀出的緊湊數值表，包含全部 1000
source IDs、原始 signed contribution、native Photon/Jet 欄位及選擇值。
binding 保留原始 ROOT／native report／來源／卡片 SHA256。它是既有
事件的數值視圖，不是新 ROOT 或新 Monte Carlo 樣本。

## 2. 一次分析既有事件的全部九種情境

完整數值 controller 會分析三程序，並呼叫獨立 statistics API：

```bash
python3 -B simulation/rare_backgrounds/scripts/analyze_pilot.py \
  --pilot-dir simulation/rare_backgrounds/evidence/pilot \
  --output "$HOME/simulations/rare_backgrounds_runs/my_full_analysis"
```

輸出根目錄的 `analysis.json` 包含全部九種情境、條件式／source-pilot
不確定度、觀測與 predictive 區間、嵌套選擇 covariance、罕見事件
concentration 及新獨立統計的 forecasts。三個程序子目錄分別保留
`conditional_summary.json` 和完整本機 `conditional_events.jsonl`。
後者不列入 public payload。來源驗證、數值分析與最終 GitHub 驗收是
分開的證據；上述完整數值指令已實際通過，GitHub 最終 HEAD 另行核對。

若只要檢查某個程序的條件式模型，可直接呼叫底層工具：

```bash
python3 -B simulation/rare_backgrounds/scripts/conditional_tags.py \
  --input simulation/rare_backgrounds/evidence/pilot/bbgg.jsonl \
  --binding simulation/rare_backgrounds/evidence/pilot/bbgg_binding.json \
  --output "$HOME/simulations/rare_backgrounds_runs/my_bbgg_conditional"
```

ccgg／jjgg 使用對應的 `ccgg.jsonl`／`ccgg_binding.json` 和
`jjgg.jsonl`／`jjgg_binding.json`，各自指定新的輸出目錄。輸出已存在時
會拒絕覆寫；可另用 `my_bbgg_conditional_02` 保留比較版本。輸出為：

- `conditional_events.jsonl`：每個原始事件的來源身分、signed weight、
  各情境 two-tags／mgg 機率及 leading tagged-pair moments。
- `conditional_summary.json`：雜湊 binding、全部事件計數、原始權重和、
  條件式期望／加權截面、clipping 計數及模型限制。
- `input_binding.json`：保留這次使用的精確輸入契約。

失敗時的 `partial_status.json` 不等於可採用的完整結果。此階段的固定
pilot 必須是全部 1000 source events、原始 denominator 1000；不能只
傳入通過選擇的幾列，再用 passing count 重新正規化。

## 3. 查看結果並保留科學解釋

```bash
python3 -m json.tool "$HOME/simulations/rare_backgrounds_runs/my_bbgg_conditional/conditional_summary.json"
sha256sum "$HOME/simulations/rare_backgrounds_runs/my_bbgg_conditional/conditional_events.jsonl"
```

固定情境為 `baseline`、`b_down20`／`b_up20`、`c_down20`／`c_up20`、
`light_down20`／`light_up20`、`joint_down20`／`joint_up20`。±20% 乘子
在運算前已固定，標記為 `TOY_MODEL_SENSITIVITY_ONLY`，不是 ATLAS 校正
誤差。超出 [0,1] 的 toy 機率會 clipping，必須讀其計數。

分母依實際 Jet.Flavor 分 b／c／light，eligible jets 為 native
pT>25 GeV、|eta|<2.5。使用現有 bit0 working point；tag 機率是在固定
重建物件上的 Bernoulli 模型，不是重新抽 tag 或重新做 detector simulation。
模型在儲存的 Float_t PT 上計算；原始 Delphes tag 抽樣使用儲存前的
full-precision PT，兩者差異是明示的 storage-rounding approximation。
WSL/Linux 是這次 golden numerical bytes 的執行環境；native Windows
libm 已觀察到最後數個 binary64 bits 的差異，不宣稱跨 Windows/Linux
的機率逐位元組相同。獨立測試把同主機模型一致性和跨 math-library
rounding envelope 分開記錄，並未改寫 frozen numerical core 或資料。

`Σq` 是模型條件式 expected count；`Σwq` 沿用原始 signed contribution，
沒有再乘 sigma/N、tag efficiency 或 luminosity。`Σq` 不是觀測整數，
不可把它四捨五入後塞進二項式區間，也不可把 signed weighted sums
當作無權重的成功／失敗事件數。leading tagged-pair mass moments 也不是
把已觀測的一對 tagged jets 直接拿來替代所有潛在 tag 組合。

## 4. 不確定度與新獨立事件數規劃

`statistics.py` 是由 `analyze_pilot.py` 呼叫的 API，沒有獨立 generation
CLI。它區分固定 event 下的 tag 方差、source-event pilot variation、
觀測二項區間及條件式 predictive count distribution。每個硬事件只有
一份 shower/reconstruction 實現，不能從這個 pilot 分離三者的誤差。
未提供的 detector/calibration/theory systematics 仍為未知。
觀測 counts／exact intervals 屬於 nominal card；toy output 中重複的
nominal values 是歷史比較，不是變動 toy card 下的新抽樣或 coverage。

20%／10% 精度及不同 confidence 的 future forecasts 是基於 pilot 與
指定模型的規劃，不是新事件或保證。零觀測的區間下界為零時，所需
精度可能是 `UNBOUNDED`；禁止把零觀測推成零背景、零誤差或有限保證。
新獨立統計必須來自新的原始 MC 事件與新的 seed／來源身分；多次重算
同一份 input 或抽樣相同物件的 tag 不增加有效 hard-event sample。

## 5. 若要從本機 ROOT 重新建立來源驗證

這一步需要既有已驗證 ROOT 6.40.04／C++20、Delphes 字典及本機完整
Stage C 檔案。它只讀既有 ROOT，重新執行相容 native analyzer：

```bash
python3 -B simulation/rare_backgrounds/scripts/verify_existing_inputs.py \
  --bbgg-run "$HOME/simulations/delphes_runs/stage_c_bbgg_1000" \
  --ccgg-run "$HOME/simulations/delphes_runs/stage_c_ccgg_1000" \
  --jjgg-run "$HOME/simulations/delphes_runs/stage_c_jjgg_1000" \
  --installation .local/delphes_installation.json \
  --output "$HOME/simulations/rare_backgrounds_runs/my_native_verification"
```

原始 ROOT／reco／card／index／ledger 的 byte hashes 必須相符，而且
新的 native readback 必須通過完整計數、schema／來源身分／有限值與
科學內容檢查。輸出是新的 readback 證據，不重寫原 ROOT、不新增事件。
沒有完整檔案／已驗證安裝時，public compact 數值重現與 physical ROOT
readback 必須分別標記；portable CI 不重新安裝或執行 ROOT。

## 6. 新背景、發布與圖檔

bbγj 的 calibrated jet→photon transfer 不存在；不能自行填入固定 fake
率，或把 b-tag mistag 當 photon fake。ttH／ZH 的 H→γγ 是 loop-induced，
普通 SM tree card 不能直接當已驗證的 decay chain。H/Z/top/W 的 widths、
branching ratios、inclusive／exclusive 正規化、prompt／nonprompt／fake
partition 及 ME/PS overlap 都要另做實際驗證。參閱
[新背景 feasibility report](../../reports/phase6d_new_background_feasibility.md)。
報告中的 process cards 明示 `FEASIBILITY_ONLY`，本階段未執行。

個人數值分析預設留本機，不會自動 commit／push／建立 release。選定的
public tables／binding／數值摘要須通過 bounded payload 與實際最終 HEAD
CI，再由使用者明確選定發布。沒有圖檔是完成此數值分析的必要條件；
若日後產生 PDF／PNG，精確最終檔案 SHA256 和 caption/provenance 在得到
使用者核准前保持本機，不能因 tests PASS 就 staging／push。

公開內容只包含精確三個 compact pilot JSONL／binding／extraction、
native verification 收據、各程序 conditional summary 與完整
`evidence/results/analysis.json`。每個 pilot JSONL 上限2 MiB、三個
合計6 MiB；其餘新文字檔上限5 MiB。完整 conditional event tables、
新的 ROOT／LHE／HepMC／archives／圖檔不發布；既有歷史路徑不可修改。

```bash
python3 -B -m unittest discover -s simulation/rare_backgrounds/tests -v
python3 -B simulation/rare_backgrounds/scripts/audit_payload.py --staged
python3 -B simulation/rare_backgrounds/scripts/audit_payload.py --outgoing codex/phase6c-delphes-fast-sim
```

GitHub workflow 用 Ubuntu24.04／Python3.12 重新計算 public compact pilot，
逐位元組比較 `analysis.json` 與三個 conditional summary，再稽核 payload。
它不在 runner 讀 native ROOT／安裝或執行 generator。每次 push 前須先
檢查 staged 和每個 outgoing commit；push 後再確認真正的最終 HEAD CI。

本指南列出目前真實可呼叫的數值／readback 介面；完整 Phase6D 的物理
來源、數值執行、統計 controller 與 GitHub 驗收收據分開記錄，尚未取得
對應收據時，不把指令範例或 source tests 宣稱為完成的執行。
