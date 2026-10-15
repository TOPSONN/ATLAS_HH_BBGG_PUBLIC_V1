# Phase7A：ggF HH 全質量迴圈模型操作說明

本階段只允許模型檢查、固定相空間點矩陣元素計算與 dry-run。
**實體訊號事件數為 0**。拿掉 `--dry-run` 會以結束碼 2 回報
`PHYSICAL_SIGNAL_GENERATION_NOT_AUTHORIZED`，且不建立輸出目錄。
10、100、1000 事件都是將來另行授權的計畫，這裡沒有可解除限制的旗標。

以下在 WSL Ubuntu、專案根目錄執行。既有 MG5、Pythia、HepMC、Delphes、
ROOT 安裝由 `.local/*_installation.json` 找到；不用重新安裝。
`$HOME` 是目前 WSL 使用者的家目錄。

## 已可執行的 dry-run

```bash
bash simulation/hh_signal/scripts/generate_signal.sh \
  --process ggf_hh_sm --events 100 --seed 20261120 --energy 13000 \
  --output "$HOME/simulations/hh_signal_runs/ggf_hh_sm_100_readiness" \
  --max-hours 4 --max-disk-gb 10 --dry-run
```

使用全新目錄；命令保護既有結果、拒絕符號連結與專案內輸出。
實際結果是 `cards/` 的精確副本與 `dry_run_receipt.json`。
receipt 記錄來源 SHA256、模型/耦合、PDF/尺度與衰變/BR 契約、既有工具身分、
可用記憶體/磁碟、資源上限，以及明確的 0 事件與尚未驗證項目。
它不是 LHE event manifest。

`--events` 可填 10、100、1000 或 1–1000 的整數，只改變「待審查的未來請求」；
`--seed` 可填 1–900000000。現在只凍結 13000 GeV 的質心碰撞能量，
兩束各 6500 GeV。未經模型/PDF/尺度審查的其他能量會被拒絕。
4 小時/10 GiB 是未來生產的上限請求；**數值模型檢查另限 2 小時/5 GiB、1 worker**。

## 檢查與重做矩陣元素數值驗證

```bash
python3 -B simulation/hh_signal/scripts/verify_loop_model.py
python3 -B simulation/hh_signal/scripts/verify_loop_model.py \
  --numerical --output "$HOME/.local/share/atlas-hh-phase7a/my_numeric_check" \
  --max-hours 2 --max-disk-gb 5
python3 -B -m unittest discover -s simulation/hh_signal/tests -v
python3 -B simulation/hh_signal/scripts/validate_signal_contract.py
```

數值命令只用既有來源的隔離副本，關閉自動下載，在固定 250.001、300、400、800 GeV
的 HH 相空間點計算平方矩陣元素。每個點比較 κλ=-1、0、1、2；另驗證重複、H 交換、
固定 Yukawa 下改 MT，以及獨立 Yukawa 改動。沒有 MadEvent 積分、unweighting、
LHE、Pythia `next()` 或 Delphes。用 `touch <數值輸出目錄>/STOP` 可要求受監控程序停止；
停止與失敗紀錄都保留。不可把固定點平方矩陣元素當作 pb 截面。

## 模型、參數與 cuts 的改動

先讀 `models/MODEL_SOURCE_AUDIT.md` 和 `config/`。`ggf_hh_sm_candidate.mg5`
是 process 語法卡；`proposed_run_card.dat` 是帶有未完成尺度設定的草案，不可當成已核准生產卡。
預設 MH=125、MT=173、MB=4.7 GeV，κλ=κtop=1。
診斷 κλ 只重縮放已核對的 HHH coupling，不改 MH；不是可供任意 BSM 生產的 UFO。
CTEQ6L1 只是既有方法比較基準；真實樣本前須審查 PDF/αs 與 mHH/2 的實際尺度實作。

產生 cuts、PDF、碰撞能量或物理製程的修改要建立新契約、比對來源與耦合/圖、
重新執行數值與失敗測試，才可以送下一階段審查。HEFT 必須標
`HEFT_APPROXIMATION_ONLY`，不得冒充完整有限 MT 模型。保留 Phase6C 選擇與 Delphes 卡；
尚無真實訊號，不做 cut 最佳化。

## HH→bbγγ 的必要限制

原始 source 必須有兩個不同 PDG25 lineage。方法層級的 50/50 分配不看 pT 排名，
必須另用獨立 assignment seed；每次恰好一個 bb、一個 γγ。全域 PDG25 強制衰變設定
不能指定兩個不同模式。目前只驗證分配方法，尚未實作/驗證 native per-lineage decayer。
不得手動替換子粒子或發明 H1/H2 PDG 編號。

`GENERATOR_MODEL_BR`、`EXTERNAL_REFERENCE_BR`、`ADOPTED_STUDY_BR` 與
`FORCED_SAMPLING_PROBABILITY` 分開記錄；本訊號的 BR 尚未採用，數值為 null。
純生產 HH 截面若未包含衰變，缺少因子才是 `2*BR(H→bb)*BR(H→γγ)`，只能用一次。
生產的 identical-H symmetry factor 和混合衰變的因子 2 物理意義不同。

## 將來如何找 LHE、截面與驗證樣本

這一階段不會有訊號 LHE/HepMC/ROOT 檔案；截面欄位固定為
`NOT_EVALUATED_UNTIL_REAL_INTEGRATION`。將來若獲個別授權，先完成 10 事件 smoke，
驗證真實 LHE 的 IDWTUP/XWGTUP、source N、衰變來源、母女關係、四動量與符號權重，
再考慮 100 pilot。保留原始 N 作分母，不使用通過選擇的事件數；不重乘 σ/N 或轉換 pb/mb。
HepMC 必須由 native ReaderAscii 驗證，Delphes/ROOT 必須獨立驗證後才能稱 full chain。

## 互動入口與選定結果的 GitHub 發布

可使用既有 MG5 互動工具（其他階段的生產授權不能套用到本訊號）：

```bash
bash simulation/mg5/scripts/mg5_cli.sh
```

若要核對 process，限 import/generate/display；不要在 Phase7A 手動執行 `launch`。
本階段已授權的自動數值入口是上面的 `verify_loop_model.py --numerical`。
個人輸出不自動 push。這個 PR 只發布 source、cards、tests、JSON 數值證據與文字報告。
將來選定參考樣本須另經實際計數、SHA256、來源/權重/衰變閉合與大小/隱私檢查，
再明確 stage 指定檔案；不可把整個輸出目錄或 generator 副本加入 Git。
PDF/PNG 必須由使用者核准精確版本及 caption/provenance 後才可 push。
