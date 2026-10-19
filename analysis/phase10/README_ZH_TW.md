# Phase10 背景模型可行性與既有資料分析

本目錄只分析現有 Phase8／9 資料、審查安裝來源並驗證方法。沒有執行新 MG5 積分／事件、Pythia、Delphes、Phase7I build／restart 或實體 pilot。所有 future cards 都是逐行註解的審查文件，不能直接執行。

科學詳解見 [完整分析筆記](../../reports/phase10g_analysis_note.md)，驗收與範圍見 [最終報告](../../reports/phase10_final_report.md)。原 Phase6–9 來源、選取、權重、數據、圖件及舊 PR 保持原狀。

## 閱讀順序與證據

1. `reports/phase10a_independent_review.md`：6000 筆 LHE／HepMC／native／origin joins；獨立選取與 Decimal 算術。4668 歷史 ROOT 物件是精確 manifest／digest 綁定，沒有宣稱重讀完整 ROOT histogram。
2. `reports/phase10b_hf_stratification.md`：3000 個 B01–3 原始事件，2220 strata、6000 covariance、60 overlap rows。ME、incoming HF、shower、hadron、native flavour、bit0 不合併成同一標籤。
3. `reports/phase10c_generator_strategy.md`：8 種候選方案與實際安裝來源；目前沒有通過本精確過程驗證的 matching prescription。
4. `reports/phase10d_pilot_contract.md`：未啟用、不可實例化的未來合約；PDF／alpha_s／merging scales 等尚未確立，保留 null。
5. `reports/phase10e_photon_fake_feasibility.md`：6000 既有 ROOT 事件的新 scalar profiling；tight／anti-tight 與 conversion 缺失，nonisolated 區域被既有 isolation 前置篩選截斷。真實 fake transfer measurement 被阻擋。
6. `reports/phase10f_precision_plan.md`：10／20／30／50% 條件精度情境。獨立 Fraction／Decimal 驗證全部 88／3648／16 rows。
7. `reports/phase10g_analysis_note.md`：15 節物理敘述、既有 12 圖 caption 支持範圍與尚待解決的依賴。

`evidence/` 只收錄有界 CSV、JSON 與純文字收據；不含 ROOT、event JSONL、原生執行檔或新 PDF／PNG。五個 evidence_class 有不同意義：

| 類別 | 意義 |
|---|---|
| ACTUAL_EXISTING_DATA_READBACK | 實際讀取現有原始或持久化資料；以每項 scope 指定是否新 ROOT loop |
| HISTORICAL_SOURCE_AUDIT | 舊來源、數值、manifest 或 publication bytes 的覆核 |
| PUBLIC_SOURCE_AUDIT | 公開官方文件及安裝來源的適用性審查 |
| SYNTHETIC_METHOD_ONLY | 人工輸入的公式／方法測試，不能當成物理資料 |
| FUTURE_UNEXECUTED_PROPOSAL | 未執行的未來提案，不代表授權或可用設定 |

## 可直接執行的來源／方法檢查

在 checkout 根目錄使用現有 Python3；不會安裝軟體：

```bash
python3 -B -m unittest discover -s analysis/phase10/tests -p 'test_*.py' -v
python3 -B -m unittest discover -s analysis/phase9/tests -p 'test_phase9_*.py' -v
python3 -B -m unittest discover -s analysis/phase8/tests -p 'test_*.py' -v
python3 -B analysis/phase10/scripts/validate_publication.py --repo .
```

GitHub CI 僅執行來源／方法與已發佈有界證據檢查，不會重跑本機完整 ROOT／LHE／HepMC joins。沒有外部人類 reviewer 簽核；不同代理及不同算術實作不應被寫成人類批准。

## 現有資料重現指令

以下是本機安裝和原資料路徑；輸出必須使用未存在的新目錄。先核對 `metadata/phase10_source_manifest.json`、輸入 SHA256 與本機可用空間，勿指向任何歷史輸出。每個 CLI 拒絕覆寫已存在的收據或結果檔。

```bash
cd /home/btu/projects/atlas_hh_phase10_v1
P8=/home/btu/simulations/hh_phase8/run_01
P9=/home/btu/simulations/hh_phase9/run_01
OUT=/home/btu/simulations/hh_phase10/user_readback_01
mkdir "$OUT"
python3 -B analysis/phase10/scripts/review_phase9.py \
  --phase9-local "$P9" --phase8-local "$P8" --output "$OUT/review"
python3 -B analysis/phase10/scripts/stratify_existing.py \
  --origins "$P9/origins_03/phase9_origins_event_details.jsonl" \
  --native "$P9/native/phase9_native_events.jsonl" --output "$OUT/hf"
python3 -B analysis/phase10/scripts/precision_plan.py \
  --phase9 "$P9" --output "$OUT/precision"
python3 -B analysis/phase10/scripts/validate_precision.py \
  --plans "$OUT/precision" --phase9 "$P9" --output "$OUT/precision_review.json"
python3 -B analysis/phase10/scripts/validate_pilot_contract.py \
  --output "$OUT/inactive_pilot_review.json"
```

最後一項僅檢查 inactive 合約，不建立生成器 process、不執行 card。數值為 null 的 matching／PDF／calibration 設定不能以預設值填補後執行。

本次正式執行透過未修改的 Phase8 `execute()` 資源容器，鎖定單一工作／worker、aggregate 4h CPU／4h job-wall、build＋result 額外 2GiB。每次命令、exit code、CPU、wall、抽樣 process-group RSS、磁碟占用及失敗嘗試均保存於 `phase10_execution_ledger.json`。這些數字涵蓋登錄的計算工作，不是人工作業及編輯器的總系統 CPU；RSS 是抽樣值。

## 原生 observability 讀取器

重用既有 Phase8 ROOT／Delphes reader，新增 C++ 僅讀取先前 reader 未保留的 numeric dictionary fields。Phase10 採獨立 CMake，沒有修改舊 root CMake 或舊 workflow。使用既有 ROOT6.40.04／C++20，單執行緒編譯：

```bash
CONDA=/home/btu/miniforge3/bin/conda
ENV=/home/btu/miniforge3/envs/atlas-hh-root
BUILD=/home/btu/build/atlas_hh_phase10_user_01
"$CONDA" run --no-capture-output -p "$ENV" cmake \
  -S analysis/phase10 -B "$BUILD" -DBUILD_TESTING=ON \
  -DDELPHES_ROOT=/home/btu/opt/delphes -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_COMPILER="$ENV/bin/x86_64-conda-linux-gnu-c++"
"$CONDA" run --no-capture-output -p "$ENV" cmake --build "$BUILD" --parallel 1
"$CONDA" run --no-capture-output -p "$ENV" ctest --test-dir "$BUILD" --output-on-failure
"$CONDA" run --no-capture-output -p "$ENV" "$BUILD/phase10_photon_observability" \
  --manifest "$P8/phase8_local_manifest.json" --output "$OUT/native_photon.json"
python3 -B analysis/phase10/scripts/photon_feasibility.py \
  --repo . --phase9 "$P9" --native-observability "$OUT/native_photon.json" \
  --output-dir "$OUT"
```

這是唯讀 ROOT profiling，不是 detector simulation。資料完整性另由原始檔前後 SHA256、unique source identity 與獨立 join 檢查界定；不能把 scalar profiling 叫作重新驗證全部物理 ancestry。

## 不確定度及物理 gates

固定原始 N、每個原始事件作為統計單位；同事件多個 jet／origin flags 不算獨立。raw sumw、BR-once 正規化、shape／rate、acceptance／weighted rate、proposal／physical normalization 分開。未知 nuisance value／covariance 保留 null，不能填 0。

B02 的 20% acceptance total-N=24975 只是原提案、p̂=1/1000 的條件 plug-in；原始 N 的 source-rate Bessel 版本是25000。95% CP-p 導出的 acceptance 情境約4473–987435，沒有 production 保證。B03／B06 零倖存採上限及假設情境，不宣稱零背景，也不給有限保證 N。κλ=2.5／5 支持不足，沒有新 ME weights／事件；重抽樣不增加獨立 hard statistics。

`physical_gates.py` 固定 HF origin 為 VALIDATED_WITH_LIMITS、generator exclusivity 為 UNVERIFIED、fake rate 為 UNKNOWN、signal normalization 為 BLOCKED_PHASE7I、total background 為 BLOCKED；significance／CLs／κ interval 均 NOT_EVALUATED。合成 sideband 成功不解除任何物理 blocker。

既有 12 組 Phase9 PDF／PNG 維持 AWAITING_USER_APPROVAL。本次不產生新圖，不 stage 圖檔；每次 push 前同時檢查 index exact bytes 與所有 outgoing commit payload。新物理 pilot 需要另一份精確來源、設定、有限資源與新輸出目錄的明確授權，Phase10 不會自動繼續。
