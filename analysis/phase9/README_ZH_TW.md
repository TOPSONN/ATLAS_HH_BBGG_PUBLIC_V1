# Phase9 既有資料背景物理診斷

本目錄使用 Phase8 已存在的事件與 ROOT histograms，新增重味／光子 ancestry、稀有 MC 統計、控制區域與本機 ROOT 圖。沒有 ME、積分、硬事件、Pythia、Delphes 或 Phase7I build/restart dispatch。

起點為 `8ecd91106acb1dae065cde14f1d62867d10b073f`（PR25）；Phase8 真正執行的 core 為 `19faeaf487fb1f9b49ff00f5cf85eeeb1c949930`。Phase8 source 與歷史資料保持不變。

## 本次真的做了什麼

- 新的 native ROOT readback：B01–B06，各1000筆，共6000筆。來源 hash、原始ordinal、HepMC byte hash、ROOT object/index、權重及五階段 cutflow 全部閉合。
- Phase8 persisted-event 獨立審查：八個來源共7100筆；本次沒有重新讀取1100筆signal ROOT，也沒有把800個重疊prefix算成新增獨立統計。
- 新 ancestry join：6000筆 photon、其中3000筆 HF；Pythia／HepMC exact tuple與母圖關係驗證，歧義保留。
- 144張 histogram與既有 ROOT CSV逐bin比對；固定原始N的正規化誤差包含bin–total covariance。ROOT另核對33個exact-binomial案例。
- 12類ROOT圖只留本機。公開plot manifest有最終PDF／PNG SHA、caption及provenance，不包含圖檔。

完整物理筆記在 [phase9f_analysis_note.md](../../reports/phase9f_analysis_note.md)，總驗收在 [phase9_final_report.md](../../reports/phase9_final_report.md)。A–G專題報告各自保留方法、實際數字與限制。

## 環境與可重跑範圍

使用已安裝的ROOT **6.40.04**／C++20及Delphes library；不需要重裝。完整ROOT、HepMC與原始diagnostic檔留在本機，GitHub CI只跑source/method及公開bounded-evidence檢查，不能宣稱remote重跑6000筆ROOT。

本次位置：

```text
source: /home/btu/projects/atlas_hh_phase9_v1
build:  /home/btu/build/atlas_hh_phase9_v1
input:  /home/btu/simulations/hh_phase8/run_01
result: /home/btu/simulations/hh_phase9/run_01
```

重跑時請選全新output子目錄。以下是實際介面的可執行範例，`timeout`只限制新分析程式，不會啟動generator：

```bash
cd /home/btu/projects/atlas_hh_phase9_v1
P8=/home/btu/simulations/hh_phase8/run_01
OUT=/home/btu/simulations/hh_phase9/my_review_02
BUILD=/home/btu/build/atlas_hh_phase9_v1
CONDA=/home/btu/miniforge3/bin/conda
ENVROOT=/home/btu/miniforge3/envs/atlas-hh-root
test ! -e "$OUT" && mkdir "$OUT"

timeout 120s "$CONDA" run --no-capture-output -p "$ENVROOT" \
  "$BUILD/analysis/phase9/phase9_readback" \
  --manifest "$P8/phase8_local_manifest.json" --output "$OUT/native"

timeout 900s python3 -B analysis/phase9/scripts/phase9_origins.py \
  --manifest "$P8/phase8_local_manifest.json" \
  --native-jsonl "$OUT/native/phase9_native_events.jsonl" \
  --output "$OUT/origins"

timeout 120s python3 -B analysis/phase9/scripts/phase9_statistics.py \
  --source "$PWD" --phase8-results "$P8" --output "$OUT/statistics"

timeout 120s python3 -B analysis/phase9/scripts/review_phase8.py \
  --source "$PWD" --phase8-results "$P8" --output "$OUT/review"

timeout 120s python3 -B analysis/phase9/scripts/readiness.py \
  --source "$PWD" --phase8-results "$P8" \
  --review "$OUT/review/phase9a_independent_review.json" \
  --output "$OUT/phase9_physical_readiness.json"
```

`phase9_origins.py`還需要既有 `/home/btu/simulations/pythia8_runs/{bbgg,ccgg,jjgg}_1k/` 原始diagnostics及manifest。缺少時會停止，不能用新事件、假資料或條件不明的替代來源填補。每筆原始事件均須加入，不可把filtered N當成權重分母。

獨立驗證：

```bash
timeout 120s python3 -B analysis/phase9/scripts/validate_hf_evidence.py \
  --origins "$OUT/origins" --native-jsonl "$OUT/native/phase9_native_events.jsonl" \
  --output "$OUT/hf_validation.json"
timeout 120s python3 -B analysis/phase9/scripts/validate_photon_evidence.py \
  --details "$OUT/origins/phase9_origins_event_details.jsonl" \
  --summary "$OUT/origins/phase9_origins_summary.json" \
  --csv "$OUT/origins/phase9_photon_origin_study.csv" \
  --output "$OUT/photon_validation.json"
timeout 120s python3 -B analysis/phase9/scripts/validate_statistics.py \
  --statistics "$OUT/statistics" --phase8-results "$P8" \
  --output "$OUT/statistics_validation.json"
timeout 120s "$CONDA" run --no-capture-output -p "$ENVROOT" \
  "$BUILD/analysis/phase9/phase9_binomial_reference" \
  --input "$OUT/statistics/phase9_binomial_reference.json" \
  --output "$OUT/ROOT_binomial_validation.json"
```

若要建立新build：

```bash
"$CONDA" run --no-capture-output -p "$ENVROOT" cmake -S . -B "$BUILD" \
  -DATLAS_BUILD_PHASE9=ON -DBUILD_TESTING=ON \
  -DDELPHES_ROOT=/home/btu/opt/delphes -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_COMPILER="$ENVROOT/bin/x86_64-conda-linux-gnu-c++"
"$CONDA" run --no-capture-output -p "$ENVROOT" cmake --build "$BUILD" --parallel 1
```

這是analysis build；沒有呼叫或改寫Phase7I production builder。本次用未改動的Phase8 generic `execute()`做單一process-group containment，分析commands皆有資源收據，總限制為Phase9自行採用的4h CPU／4h job-wall／2GiB新增輸出／1 job／1 worker，與舊Phase7I授權分開。

## 圖的產生與批准

```bash
timeout 120s python3 -B analysis/phase9/scripts/prepare_plots.py \
  --data "$OUT/statistics/phase9_plot_data.json" \
  --root-csv "$P8/native/phase8_histograms.csv" \
  --hf-csv "$OUT/origins/phase9_heavy_flavour_origins.csv" \
  --output "$OUT/plot_spec.json"
timeout 120s "$CONDA" run --no-capture-output -p "$ENVROOT" \
  "$BUILD/analysis/phase9/phase9_plots" --input "$OUT/plot_spec.json" \
  --output "$OUT/figures_ROOT"
```

所有科學圖由CERN ROOT繪製。PDF driver可能留下紙張空白；`trim_pdf_pages.py`用既有pypdf和Poppler只裁紙張，並要求decoded ROOT vector drawing stream前後SHA完全相同，不重畫或改動數據。環境已有pypdf時：

```bash
python3 -B analysis/phase9/scripts/trim_pdf_pages.py \
  --source "$OUT/figures_ROOT" --output "$OUT/figures_final"
```

本次使用Codex已附的pure-Python pypdf 6.10.0，以 `--pypdf-path /mnt/c/Users/User/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/Lib/site-packages` 讀取；沒有安裝新軟體。每一最終PDF另經Poppler重新渲染並人工視覺檢查。本機早期比較版本與失敗輸出保留，最終版本由plot manifest精確指定。

**QA通過不等於批准上傳。** 全部PDF／PNG仍為 `AWAITING_USER_APPROVAL`。只有使用者另外核准確切路徑、SHA及caption/provenance後，才能另行發布。一般source PR不帶圖。

## CSV與統計解讀

- `phase9_heavy_flavour_origins.csv`含event-indicator與jet-composition兩種row；event為統計單位。`weight_scope`空白的object-composition列仍由`*_pb`／`*_pb2`欄明確表示RAW_SOURCE，沒有MODEL_BR或lumi縮放；見B報告字典。
- photon CSV另含object-multiplicity rows；多個photons與jets共用同一source事件，variance採event-clustered計算，不能當成獨立objects。
- precision CSV包含40個stage rows；零存活的empirical variance為0不代表真實率為0，必須一起讀CP／Wilson與單側95%上限。
- planning是相同proposal／相同selection的假設情境，目標是漸近relative SE；不是保證達到的event需求，零存活不提供有限保證。
- region以TWO_JETS為基底，0／1／≥2 tags乘上low／Higgs／high／outside及undefined mgg。低tag區沒有tagged bb或HH candidate，`null`不可改成0。
- shape為fraction per bin，包含flow分母；非均勻bin不是density/GeV。JS／CDF距離只是描述值，沒有p-value、cut optimization或physical sensitivity。
- κ各點共用1000個sources，具有跨κ covariance。2.5／5為`INCONCLUSIVE_REWEIGHTING`，不能把低ESS當成更多獨立events。

## 驗證與公開限制

```bash
python3 -B -m unittest discover -s analysis/phase9/tests -p 'test_phase9_*.py' -v
python3 -B -m unittest discover -s analysis/phase8/tests -p 'test_*.py' -v
"$CONDA" run --no-capture-output -p "$ENVROOT" ctest --test-dir "$BUILD" --output-on-failure --parallel 1
python3 -B analysis/phase9/scripts/validate_publication.py --repo .
```

測試清楚分別標示`SYNTHETIC_METHOD_TEST`、`ACTUAL_EXISTING_DATA_READBACK`、`HISTORICAL_EVIDENCE_AUDIT`、`PUBLIC_CALIBRATION_SOURCE_AUDIT`。source/method guards、保存收據與actual full readback不能互相冒充。

`evidence/`只公開bounded CSV／JSON。完整ROOT、6000-event細節JSONL、完整plot-data/ranks及native binaries不進Git。Publication guard核對所有改動／staged／untracked與每個outgoing commit的path、manifest coverage、SHA、size、type與binary magic。

最終物理狀態：HF overlap未解決、fake calibration不可用、historical C1000 signal normalization尚未匹配校正；因此physical total background為BLOCKED，significance／CLs／κ interval全部NOT_EVALUATED。沒有計算官方ATLAS系統誤差或排除能力。