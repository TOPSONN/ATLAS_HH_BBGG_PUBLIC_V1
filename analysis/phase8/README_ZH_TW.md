# Phase8 HH→bbγγ：既有資料分析操作說明

本套件以 **C++20 / ROOT 6.40.04 / Delphes 3.5.1 native classes** 分析既有歷史事件。Python只負責來源保全、資源控制、獨立數值驗證與報告。不提供MG5、ME、Pythia、Delphes generation模式，也不會啟動Phase7I建置或積分。

## 1. 分析範圍與來源

主Signal是 `S01_C1000`；`S01_B100` 是不同有效設定的獨立pilot，必須分開。B01–B06各1000筆。合計7100個independent original sources，六組κλ weights共6000列，僅對應同一1000個C來源。重讀prefix或repeat不會增加獨立統計量。

C1000實際是NNPDF23 LO、two-loop αs、seed20261122；不能改標CTEQ6L1。B100實際是CTEQ6L1、one-loop、seed21。引用 `metadata/phase7e_audit.json` 的effective runtime證據，歷史run-card宣告不足以覆蓋它。

本套件保留baseline：photons pT>25 GeV、leading>35、|η|<2.37並排除1.37<|η|<1.52；eligible jets pT>25、|η|<2.5；native `(Jet.BTag & 1)!=0` 至少2個；105≤mγγ≤160 GeV。沒有新增m_bb baseline cut。缺少tagged pair時相關mass是null，不能用0或untagged jets補值。

## 2. 使用已安裝環境

以下是目前WSL Ubuntu既有目錄的可執行範例。`$HOME`會解析使用者自己的home；Git內manifest不記錄private absolute paths。請在新的獨立Phase8 checkout操作，保持Phase7I與舊simulation資料唯讀。

```bash
REPO="$HOME/projects/atlas_hh_phase8_v1"
BUILD="$HOME/build/atlas_hh_phase8_v1"
ROOT_ENV="$HOME/miniforge3/envs/atlas-hh-root"
CONDA="$HOME/miniforge3/bin/conda"
cd "$REPO"
"$CONDA" run --no-capture-output -p "$ROOT_ENV" root-config --version
"$CONDA" run --no-capture-output -p "$ROOT_ENV" root-config --cflags
```

需要實際ROOT版本6.40.04、ROOT本身C++20、既有conda compiler及已安裝Delphes library/dictionary。版本或dictionary不一致時必須停止，不得重新標示舊資料為已驗證。

## 3. 編譯與方法測試

Build artifacts放在source repository外。Top-level預設 `ATLAS_BUILD_PHASE8=OFF`；以下明確啟用，並保留既有Step1 tests。

```bash
"$CONDA" run --no-capture-output -p "$ROOT_ENV" cmake   -S "$REPO" -B "$BUILD" -G Ninja   -DATLAS_BUILD_PHASE8=ON -DBUILD_TESTING=ON   -DDELPHES_ROOT="$HOME/opt/delphes"   -DCMAKE_BUILD_TYPE=Release   -DCMAKE_CXX_COMPILER="$ROOT_ENV/bin/x86_64-conda-linux-gnu-c++"
"$CONDA" run --no-capture-output -p "$ROOT_ENV" cmake --build "$BUILD" --parallel 1
"$CONDA" run --no-capture-output -p "$ROOT_ENV" ctest --test-dir "$BUILD" --output-on-failure
python3 -B -m unittest discover -s analysis/phase8/tests -p 'test_*.py' -v
```

CMake拒絕wrong ROOT、non-conda compiler、缺少Delphes或in-source build。C++/Python方法測試是 `SYNTHETIC_METHOD_TEST`，通過不代表已完成實際ROOT readback。

## 4. 先核對來源，再執行完整分析

選一個**全新**結果名稱。不要刪除舊結果來重用同名目錄；程式拒絕覆寫既有收據與科學輸出。

```bash
RESULT="$HOME/simulations/hh_phase8/user_analysis_01"
python3 -B analysis/phase8/scripts/audit_inputs.py --output "$RESULT"
python3 -B analysis/phase8/scripts/make_prefix_manifest.py \
  --manifest "$RESULT/phase8_local_manifest.json" \
  --output "$RESULT/phase8_prefix_local_manifest.json"
```

此命令用 `config/datasets.json` 的portable aliases解析已存在檔案，核對所有來源SHA256，實讀LHE與input index、event ordering/identity、finite particles、原始N與raw weights、bit0 card formulas，產生：

- `phase8a_source_audit.json`
- `phase8a_event_identity_audit.json`
- `phase8_local_manifest.json`（只留本機，含resolved absolute paths）
- `phase8_input_preservation_before.json`

Source hash成功時仍標示 `SOURCE_HASH_PASS_PENDING_NATIVE_READ`。缺檔、錯hash、prefix/expected count不符、未知dataset/version或duplicate source會拒絕；不可用dummy events或調整cuts消除錯誤。

接著執行已授權的existing-data分析：

```bash
python3 -B analysis/phase8/scripts/run_full_analysis.py   --manifest "$RESULT/phase8_local_manifest.json"   --build "$BUILD" --result "$RESULT" --action all --label user01
```

主控逐一執行native schema audit、完整native event loop、synthetic likelihood methods、每組source統計、κλ common-source diagnostics、control regions/shape summaries與獨立Decimal數值驗證。一次一個process group，保留command/log/exit/resource收據；不產生任何新物理事件。CPU與wall各14400秒、additional local output 2 GiB、1job/1worker的aggregate ceilings沿同一RESULT的收據累加，不能藉更換label重置。

支援單獨action：`audit`、`full`、`prefix`、`methods`、`statistics`、`kappa`、`postprocess`、`validate`。每個有實際依賴，例：statistics/kappa/postprocess需要已完成的 `native/phase8_events.jsonl`，validate還需要statistics與kappa輸出。`all`已完成後不要對同一RESULT重跑同名action。

若要驗證canonical numerical repeatability，使用專用repeat action；它保留另一份結果，重新分析相同事件，並不增加統計量：

```bash
python3 -B analysis/phase8/scripts/run_full_analysis.py   --manifest "$RESULT/phase8_local_manifest.json"   --build "$BUILD" --result "$RESULT" --action repeat --label repeat01
```

## 5. ROOT輸出、Cutflow與重建變數

原生輸出在 `$RESULT/native/`：

- `phase8_histograms.root`：TH1D/TH2D，依dataset/stage/normalization分層。
- `phase8_histogram_manifest.json`、`phase8_histograms.csv`：edges、flows、sumw、sumw2、null/invalid counts與canonical content hashes。
- `phase8_cutflow_raw.csv`、`phase8_cutflow_weighted.csv`：原始與source-weighted cutflow分開。
- `phase8_selection_closure.json`：actual/expected/difference，完整資料才可標示full closure。
- `phase8_reconstruction_statistics.csv`：26種observables的defined/missing/finite、min/median/mean/std/max。
- `phase8_truth_matching.json`：幾何matching診斷，非calibrated效率。
- `phase8a_root_schema_audit.json`：真實native classes、dictionary/streamer、entries與event identity檢查。

ROOT檔案UUID/時間可能改變；科學可重現性看 `numerical_histogram_content_sha256`，不是只比較ROOT binary SHA。真正重開ROOT驗證histogram contents：

```bash
"$CONDA" run --no-capture-output -p "$ROOT_ENV"   "$BUILD/analysis/phase8/phase8_analyze" validate --output "$RESULT/native"
"$CONDA" run --no-capture-output -p "$ROOT_ENV"   "$BUILD/analysis/phase8/phase8_analyze" summarize --output "$RESULT/native"
```

## 6. 不用Python ROOT檢視Histogram數值

```bash
python3 -B analysis/phase8/scripts/inspect_histograms.py   --manifest "$RESULT/native/phase8_histogram_manifest.json"   --dataset S01_C1000 --stage FINAL_MGG --observable m_HH --list
python3 -B analysis/phase8/scripts/inspect_histograms.py   --manifest "$RESULT/native/phase8_histogram_manifest.json"   --dataset B01 --stage FINAL_MGG --observable m_gamma_gamma   --normalization SOURCE_WEIGHTED --bins --limit 40
python3 -B analysis/phase8/scripts/inspect_histograms.py   --manifest "$RESULT/native/phase8_histogram_manifest.json"   --dataset S01_C1000 --stage FINAL_MGG --observable m_HH   --normalization UNIT_AREA_SHAPE --bin 3
```

Bin0是underflow；最後一個bin是overflow。TH2可另加 `--bin-y`。`--flow regular` 或 `--flow flow`只篩選顯示，不能改變原有shape-normalization convention。預設最多顯示40列，`--limit`上限1000。此工具只讀metadata/CSV；不是nativeROOT validator。空或signed cancellation病態shape保留undefined，不補成0。

四種normalization：`RAW_EVENT_COUNTS`、`SOURCE_WEIGHTED`、`UNIT_AREA_SHAPE`、`EXPLORATORY_LUMINOSITY_YIELD`。最後一種只代表100 fb⁻¹的 `ILLUSTRATIVE_MODEL_YIELD`，不是calibrated ATLAS預期產額。XWGTUP/N與model BR都只能各依scope用一次。

## 7. Reference prefix與原始N

公開某些ROOT只有100筆，資料夾名稱即使寫1000也不能當成1000 entries。第4節已準備reference manifest，`--action all`也包含prefix loop；下列命令只供分步執行時使用，完成all後不要重跑：

```bash
python3 -B analysis/phase8/scripts/make_prefix_manifest.py   --manifest "$RESULT/phase8_local_manifest.json"   --output "$RESULT/phase8_prefix_local_manifest.json"
```

這個步驟只是核對8個existing ROOT prefix hashes，**尚未**完成native event readback。準備manifest後，使用同一RESULT主控與aggregate budget：

```bash
python3 -B analysis/phase8/scripts/run_full_analysis.py \
  --manifest "$RESULT/phase8_local_manifest.json" \
  --build "$BUILD" --result "$RESULT" --action prefix --label prefix01
```

Prefix保留原始N與完整source identity綁定，額外readback不增加independent sources。實際prefix loop必須透過同一資源主控執行，標示 `REFERENCE_PREFIX_TEST`，不得把它的cutflow硬比1000-event full reference。

## 8. 背景、κλ與統計限制

`statistics/`與`kappa/`輸出fixed-original-N source sampling variance、ESS、bin support、dominant source events與paired covariance。Observed bit0 outcome包含已realized的tag stream；conditional analytic tag variance分開，不能再加進observed source variance。Analytic double-tag count不代表已得到各種tagged-jet pair的m_bb/m_HH機率分布。

κλ=-1,0,1,2,2.5,5用相同1000事件，保留cross-kappa covariance；2.5與5維持 `INCONCLUSIVE_REWEIGHTING`。Zero survivor不是zero background；unweighted proposal count upper bound也不是自動的weighted cross-section或fake-rate upper limit。

B01/B02/B03的ME/PS heavy-flavour overlap未解決，不能物理相加。ZH/ttH只有 `MODEL_BR_ONLY`；ttH spin modelling有已知限制。B06缺乏calibrated photon fake model。22類systematics的unknown numerical values/constraints/correlations保持null，不偷設為0-width nuisance。

`phase8_methods methods-test`的RooFit/RooStats只用 `SYNTHETIC_METHOD_ONLY` artificial inputs，不能解除actual HH combined likelihood、significance、CLs或κλ interval gates。所有結果都是ATLAS-like exploratory study，不是official ATLAS analysis。

## 9. 保全、證據分類與GitHub

完整分析後，重新核對所有before-bound input bytes：

```bash
python3 -B analysis/phase8/scripts/audit_inputs.py   --verify-snapshot "$RESULT/phase8_input_preservation_before.json"   --output "$RESULT/phase8_input_preservation_after.json"
```

Phase8A來源、B框架、Ccutflow、D重建、Ehistograms、Fweights/MC statistics、Gregions/background、Hκλ、Ishape策略、Jsynthetic likelihood、Ksystematic readiness、Lregression/publication分開記錄。

- `SYNTHETIC_METHOD_TEST`：方法與failure-path tests。
- `REFERENCE_PREFIX_TEST`：實際公開prefix ROOT loop。
- `ACTUAL_FULL_DATA_READBACK`：實際完整local native ROOT loop。
- `HISTORICAL_EVIDENCE_AUDIT`：既有frozen manifests/cards/weights的來源審核。

GitHub CI的Python/config/frozen-reference檢查是source/evidence驗證，不會假裝重跑缺少full local inputs的native loop。預設不製作PDF/PNG。LargeROOT、native binaries、complete event dumps、privatepaths只留本機；未經使用者精確版本核准的figures不得commit/push。Source、bounded numeric summaries與繁中reports只交付一個stacked Draft PR，不merge、不force push、不修改PR24。

## 10. 整理本機結果與有限公開證據

完成all、repeat及第9節保全後，可用下列現成工具整理（輸出目錄須全新）：

```bash
python3 -B analysis/phase8/scripts/summarize_outputs.py \
  --result "$RESULT" --build "$BUILD" --destination "$RESULT/final_bundle"
python3 -B analysis/phase8/scripts/select_public_evidence.py \
  --result "$RESULT/final_bundle" --output "$RESULT/public_evidence"
```

這不會自動git add／commit／push。最後的GitHub head／CI與remote byte verification由publication receipt記錄，FINAL_REPORT只有在final-head CI及remote SHA都通過後產生。`phase8_analysis_results.json`是publication前的分析收據，其CI欄位保持pending，不能把它當成遠端CI已完成。
