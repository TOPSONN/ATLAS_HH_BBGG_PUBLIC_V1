# Phase 6B cross sections and event weights

三個原始 LO inputs 都是 `IDWTUP=-4`、`event_norm=average`、1000 positive constant nominal weights，negative=0、zero=0；這是對真正原始 LHE 的完整 streaming readback 結果。軟體保留 signed/zero weights，物理 reference 中沒有人工加入負權重。

| Profile | LHE init cross section [pb] | Integration uncertainty [pb] | Actual constant XWGTUP [pb] | Full-source normalization denominator |
|---|---:|---:|---:|---:|
| bbgg | 0.06624666 | 0.0005940933 | 0.066246662 | 1000 |
| ccgg | 0.6274417 | 0.005190692 | 0.6274417 | 1000 |
| light-jjgg | 9.436556 | 0.0547472 | 9.4365561 | 1000 |

init 與 event weight 的末位差異來自原始列印位數；不重寫為同一值。三個 samples 使用各自的截面，不相加為完整 diphoton+jets prediction，也不增加 detector acceptance 或 matching correction。

Pythia8.317 的官方 source `Info.h::setWeight(weightIn,lhaStrategyIn)` 對 strategy ±4 將其internal mb input換算為儲存的pb nominal value；`Info::weight()` 回傳已儲存的該 nominal value。官方 `Pythia8Plugins/HepMC3.h` 使用 `weightValueByIndex()` 建立 weight vector；其 cross-section API 將 `sigmaGen()`/`sigmaErr()` 的 mb 乘 `1e9` 寫為 pb。這些不同欄位不能假設都以 mb 儲存，也不能套用兩次 `1e9`。

輸出 weight names 與含義固定如下。它們是同一 nominal event 的 provenance columns，不是四個 variation weights，亦不能相加。

| HepMC3 named column | Value [pb] |
|---|---|
| `input_contribution_pb` | original signed `XWGTUP / full_original_source_count` |
| `LHE_XWGTUP_pb` | original signed LHE XWGTUP |
| `Pythia_Info_weight_pb` | actual `Pythia::Info::weight()` |
| `converter_weight_0_pb` | nominal weight returned by official HepMC3 converter |

runner 每 event 比對 original XWGTUP 與 actual Pythia nominal weight，並原樣保存 converter values；portable validator 再比對原始 source element、ledger真正的 `lhe_weight_pb`、`pythia_weight_pb`、`input_contribution_pb`、`converter_weights_pb` 與整個HepMC3 vector。所有欄位必須存在，source denominator由原始LHE完整event count獨立核對；不能只靠相同weight sum或可省略的替代欄位通過。Pythia `GenCrossSection` estimate 與原始 MG5 σ/uncertainty 各自保存，不用 estimate 取代輸入 σ。

完整1000個 inputs 無拒絕且輸出全數有效時，`sum(input_contribution_pb)` 在原始列印精度內等於該 process 的 init σ。由完整 run 抽取的100-event公開prefix仍保留 `XWGTUP/1000`，sum 約為0.1σ；它是有限 prefix，不能宣稱其 weight sum 已代表完整 sample σ。沒有依 `N_written` 重新正規化，也不把 prefix 當成另一個1000-event generation。若有失敗事件，保留每個 consumed input 與原始 contribution，將 run 標記 PARTIAL，不能用存活 output count 隱藏效率或權重損失。

moments 包含 `sum_w`、`sum_abs_w`、`sum_w2`、positive/negative/zero counts。generic signed source preflight 使用 Welford variance，檢查 mean(XWGTUP) 與 init σ 的差異是否在 `5*hypot(integration_error,sample_mean_standard_error) + printed_precision` 內；這是 consistency gate，不證明任何人工 weight assignment 的生成物理。固定三份原始 hash 另外要求 known positive constant reference convention。API tests 使用真實粒子 records 的暫存 weight-metadata copies，檢查 negative/zero preservation 和 inconsistent mean rejection；它們從未進入 reference publication。

舊 primordialKT-OFF bbgg100 實際寫出100、Pythia next failures0，但獨立 strict physical readback 有1 invalid event、3 off-shell stable particles。該 output 的完整 weights 仍保留，run 不合格，沒有刪掉 event54 或重新正規化其他99個 events。

新 baseline v2 Stage A10／B100×3／C1000×3均實際PASS。post-freeze validator再獨立讀回全部3000 outputs，逐event source/ledger/LHE/Pythia/API/converter數值與完整HepMC3 vector一致，denominator1000，每process positive1000/negative0/zero0。以下為actual independent C++ readback moments；portable accumulation在浮點rounding內相同。

| Profile | sum_w = sum_abs_w [pb] | sum_w2 [pb²] | Raw weight minus init σ [pb] | Relative printed difference | Actual Pythia σGen×1e9 [pb] |
|---|---:|---:|---:|---:|---:|
| bbgg | 0.066246662 | 4.388620226142244e-6 | +2.0e-9 | 3.01902013e-8 | 0.06624666199999935 |
| ccgg | 0.6274417 | 3.936830868988900e-4 | 0 | 0 | 0.6274417000000126 |
| light-jjgg | 9.4365561 | 8.904859102844721e-2 | +1.0e-7 | 1.05970866e-8 | 9.43655610000015 |

差異完全保留，沒有把bbgg或jjgg weights改成列印位數較少的init σ，也沒有double `1e9`或改用N_written作denominator。Pythia σErr只描述其nominal sampling estimator，不能取代MG5 integration uncertainty。公開100prefix每process contribution sum分別為0.0066246662、0.06274417、0.94365561 pb，與同一full1000源的0.1份額一致。真實full-run physical報告見各process `simulation/pythia8/evidence/<profile>/physical_validation.json`；exact full ledger1000行另存於相同evidence目錄。
