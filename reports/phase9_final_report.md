# Phase9 完整驗收報告

**FINAL_VERDICT：PASS_PHASE9_EXISTING_DATA_DIAGNOSTICS_WITH_LIMITS**

既有資料已產生可稽核的新背景診斷；目前仍不能建立物理總背景、顯著度或排除區間。本結論是existing-data diagnostics驗收，沒有將探索性Delphes分析提升成官方ATLAS敏感度。

## 專案與來源

| 欄位 | 結果 |
|---|---|
| PROJECT | ATLAS_HH_BBGG_PUBLIC_V1 |
| TASK | PHASE9_BACKGROUND_MODEL_AND_PHYSICS_REVIEW_V1 |
| BASE_PHASE8_REVISION | `8ecd91106acb1dae065cde14f1d62867d10b073f` |
| EXECUTED_PHASE8_CORE | `19faeaf487fb1f9b49ff00f5cf85eeeb1c949930` |
| NEW_SOURCE_REVISION | `277fd42f4985234f327ef12a159772f537054fb0` |
| SOURCE_REVISION_SCOPE | 此commit完整捕捉最終executable source；之後僅加入bounded evidence與delivery reports。個別最終ancestry／statistics run另外有前後source SHA閉合。 |
| DRAFT_PR_URL | PENDING_DRAFT_PR_URL |
| BRANCH | `codex/phase9-background-model-review`，疊在PR25分支上 |
| NEW_ME_CALLS | 0 |
| NEW_INTEGRALS | 0 |
| NEW_HARD_EVENTS | 0 |
| 新物理產生 | ME=0、積分=0、hard events=0、Pythia=0、Delphes=0 |

本機source為`/home/btu/projects/atlas_hh_phase9_v1`；結果為`/home/btu/simulations/hh_phase9/run_01`。舊Phase8／Phase7I checkout與PR24／25不變；沒有merge或force-push。

## 實際輸入與獨立審查

`ACTUAL_INPUT_DATASETS`：S01_B100、S01_C1000、B01–B06。

`ACTUAL_SOURCE_EVENTS_READ`須分開解讀：本次新的native ROOT loop是六個背景**6000筆**；八個既有來源共**7100筆**的persisted-event／權重／identity另經獨立科學審查。沒有重跑signal ROOT full loop，也沒有把重疊prefix800筆計為新增獨立來源。ancestry join為6000筆photon／其中3000筆HF；同一來源的重讀不是新增統計。

`PHASE8_INDEPENDENT_REVIEW`：13項簽核矩陣PASS，包含全cohort counts、source weight、PDF／alpha identity、BR一次、native bit0、event identity、histogram數值、regions、κ covariance／ESS與inference gates。7100筆、19483個eligible jets及180個κ covariance項已核對。

`ACTUAL_FULL_READBACK`：原ROOT/index/card/HepMC hashes逐筆核對，6000個native event與原source ordinal／source SHA／HepMC event SHA／native weight vector／particle tuple一致。六個背景完整cutflows重現：

| Dataset | Input | Photons | Jets | ≥2 tags | Final mgg |
|---|---:|---:|---:|---:|---:|
| S01_B100（沿用驗證） |100|45|38|18|18|
| S01_C1000（沿用驗證） |1000|484|403|143|143|
| B01 |1000|446|266|91|28|
| B02 |1000|378|241|7|1|
| B03 |1000|445|277|0|0|
| B04 ZH |1000|370|220|77|75|
| B05 ttH |1000|327|322|131|131|
| B06 bbγj |1000|2|2|2|0|

4668個歷史ROOT histograms本次另做唯讀native validation，canonical digest仍為`4a8899dfde5b484d49e30438b704f81e77b648cb07d643e7360b0c181a2a9ed2`。144張新繪圖來源與既有ROOT CSV有5472項數值比對PASS。GitHub CI沒有完整本機ROOT輸入，不能冒稱它重跑這些loops。

## 重味背景的物理結論

`HEAVY_FLAVOUR_ORIGIN_CLASSIFICATION`：實際完整3000筆。hard LHE、Pythia ME incoming/final records、shower birth、直接g→heavy-pair、terminal heavy hadrons、native flavour及bit0分開標示，沒有把不同層級強迫等同。

| 原始1000筆中的events | B01 | B02 | B03 |
|---|---:|---:|---:|
| Shower bottom birth |53|36|49|
| Shower charm birth |170|211|183|
| Proven direct g→heavy pair |211|240|220|
| Eligible native-bottom jet |860|13|18|
| Native flavour reproduction mismatch |0|0|0|

B03的49/1000 shower-bottom acceptance為4.9%，Wilson95%約3.726–6.419%。photon／jet selection後的三個native-bottom witnesses為170、971、997，各只有一個observed tag；native、parton cone及heavy-hadron cone不必一致。B02唯一final survivor481為兩個native-charm tags；有shower-bottom的double-tag witness82未過final mgg。

Pythia→HepMC exact-tuple ambiguity在B02有4 records、B03有2 records，原樣保留。多母hadron endpoint仍為UNKNOWN；「heavy-quark birth分類沒有剩餘unclassified」不等於所有hadron起源完全確定。

`ME_PS_OVERLAP`：**OVERLAP_UNRESOLVED_REQUIRES_MATCHED_GENERATION_OR_VALIDATED_EXCLUSIVE_DEFINITION**。

`EXCLUSIVE_BACKGROUND_DEFINITION`：NOT_VERIFIED。共享重建phase space不是精確ME／PS double-counting證明；truth partition也不是matching／merging處方。沒有建立B01+B02+B03物理總和。

## 光子與fake feasibility

`PHOTON_ORIGIN_ANALYSIS`：6000筆、8079個native photon，其中6999個通過物件acceptance：6298 prompt-hard、24 radiation、3 electron-associated、674 unclassified、0幾何關聯為hadron-decay。這裡是所有selected objects，不限leading pair；fiducial truth仍存在hadron-decay photons，不能把reco分類的0解釋成nonprompt率0。

B06僅一個Born photon。兩個雙光子選中事件的mgg為72.490612與43.091856 GeV，均在final window外。其中event245的第二個photon有原始Pythia status −51 radiation證據；event69保持幾何歧義。這些資訊不是jet→photon fake calibration。

`FAKE_PHOTON_CALIBRATION`：**BLOCKED_CALIBRATION_UNAVAILABLE**。公開官方prompt photon ID efficiency與sideband composition已查核，但object definition／transfer semantics不適用目前Delphes fake estimation；沒有匯入restricted inputs或虛構transfer rate。C報告逐項記錄來源版本、period、energy、物件定義、適用性、誤差與access。

## 稀有統計、shape與未來樣本規劃

| Final category | k/N | acceptance | Exact雙側95%區間 | source MC relative SE |
|---|---:|---:|---|---:|
| S01_C1000 |143/1000|0.143|[0.12187864, 0.16624716]|7.7453%|
| B01 |28/1000|0.028|[0.01868469, 0.04021489]|18.6411%|
| B02 |1/1000|0.001|[0.0000253175, 0.0055589243]|100%|
| B03 |0/1000|0|[0, 0.0036820839]|未定義|
| B06 |0/1000|0|[0, 0.0036820839]|未定義|

B03／B06另報單側95% acceptance上限**0.0029912495**；這是相同proposal與固定selection的binomial上限，不是物理截面或fake背景上限。empirical sumw／variance為0不表示真實背景為0。

`MC_STATISTICAL_PRECISION`：40個stage precision rows、4560個bin-quality rows、原始N weighted sampling variance、stage/bin ESS、dominant sources與tails均已輸出。沒有把integration error、tag variance或未校準systematics塞入source MC誤差。

`RARE_BACKGROUND_SAMPLE_REQUIREMENTS`：42個planning/scenario rows，使用相同IID proposal與固定selection下的漸近relative-SE公式及pilot CP acceptance envelope。B02若假設p=0.001，20%／30%／50%目標約需24975／11100／3996筆新的獨立campaign總N；CP範圍使需求非常寬，不能當保證。零存活類別只提供p=p95、p95/10、p95/100（p95=0.002991249545095296）的顯式假設情境，不給有限的實測保證。

`REGION_CLOSURE`：120 rows count／raw sumw／own BR-once sumw閉合；0／1／≥2 tags與low／Higgs／high／outside／undefined mgg互斥。1080個observable summaries保留missing/null；0／1tag沒有tagged bb或HH candidate。

`SHAPE_COMPARISON`：九個要求的observables、864個逐背景／region比較；128個有定義、736個因空或null候選未定義。JS／CDF距離、ratio variance及ESS只作描述；不做同樣小樣本上的optimized sensitivity。B02一個final事件無法支持可靠shape；B03／B06 final shape為UNDEFINED。

κ=2.5／5的input ESS為36.6943／19.5442，final ESS為16.0736／7.6501；兩者仍是**INCONCLUSIVE_REWEIGHTING**。各κ共用1000個sources，不能視為獨立MC。後續需獨立generation或有已知proposal densities的multi-proposal strategy，再檢查共同支撐與保留跨κ covariance；本次沒有產生新事件。

## 圖、筆記與likelihood gates

`ANALYSIS_FIGURES`：12類CERN ROOT PDF及PNG留在本機，最終路徑由`analysis/phase9/evidence/phase9_plot_manifest.json`指定，**QA_PASSED／AWAITING_USER_APPROVAL**。每圖有dataset、N、stage、weight、無lumi假設、誤差解讀與限制。最後PDF只裁紙張空白，decoded ROOT vector stream前後SHA完全一致；沒有重畫數據。早期錯誤PDF backend與layout版本保留且排除final deliverables。

`LIKELIHOOD_READINESS`：沿用Phase8 RooFit／RooStats，26個synthetic methods與toy closure另行回歸；沒有重寫physical fit。matched signal norm、HF exclusivity、fake估計、single-H模型驗證、detector calibration、nuisance值／correlations與MC bin support共八項仍BLOCKED／UNKNOWN。signed-expectation gate僅對現有正權重來源conditional PASS，未宣稱任意signed模型可用。

`PHYSICAL_TOTAL_BACKGROUND`：BLOCKED。`PHYSICAL_SIGNIFICANCE`、`PHYSICAL_CLs`、`PHYSICAL_KAPPA_INTERVAL`：NOT_EVALUATED。合成fits保持SYNTHETIC_METHOD_ONLY。

`PHASE7I_DEPENDENCY`：未來需另行核准corrected CTEQ6L1 one-loop matched integration、獨立signal截面與誤差、校正full chain及新source identities；不能暗中替換historical C1000。本次未觸發Phase7I build／restart。

## 驗證、保存與交付

- `EXISTING_REGRESSIONS`：Phase8 Python92／C++ ROOT9／native synthetic26，全部PASS。
- `METHOD_TESTS`：Phase9 **165/165**；包含synthetic guards與bounded historical graph regression。Phase8 Python **92/92**、C++／ROOT CTest **9/9**、native synthetic likelihood **26/26**。
- 獨立HF：3000筆、980 CSV rows、7190 numerical checks；photon：6000筆、750 rows、6300 Decimal70 checks與120 object aggregate checks。
- 獨立statistics：7100筆persisted source、144 histograms／1824 flow-inclusive bins、120 regions、40 stages，共**12904** comparisons。ROOT exact-binomial為33 cases／66 endpoints，最大差1.19904×10⁻¹⁴。
- `SOURCE_HASH_CLOSURE`：source manifest、final ancestry／statistics source前後SHA與三個actual native binaries／resolved dependencies均已記錄。歷史Phase8 source不變。
- `HISTORICAL_PRESERVATION`：**411 files、2312498346 bytes**全部重新hash相同；舊Phase8／Phase7I HEAD及index不變。所有既有physical reference validators PASS。
- `ACTUAL_ANALYSIS_CPU`、`ACTUAL_ANALYSIS_WALL`、`PEAK_MEMORY`、`DISK_USAGE`：已記錄93個science／artifact jobs：CPU 457.862 s、job wall 484.978 s，抽樣peak RSS 818286592 bytes（約780.4 MiB），當時results 122200073 bytes及build 13888677 bytes（以receipt精確值為準）；delivery bookkeeping另列於最後本機receipt。這是contained jobs的實測加總，包含失敗與superseded attempts；不冒充source editing／clone準備／零碎bookkeeping的完整端到端CPU。RSS明示為抽樣process-group值。
- `GITHUB_CI`：最終head的source/method與bounded-evidence check由GitHub Actions外部狀態驗證；不是本機full-ROOT loop。
- `REMOTE_BLOB_VERIFICATION`：publication後逐檔下載並核對source/evidence SHA與bytes，最後結論寫入本機`FINAL_REPORT.json`與delivery receipt。commit無法自我包含其未來CI結果；此報告不以placeholder PASS代替外部驗收。

`GATES_PASS`：source/input identity、native readback、ancestry／unknown保留、independent numerics、ROOT區間、region閉合、shape誤差、regressions、historical preservation、local figure QA與0 production。

`GATES_FAIL`：最終科學診斷無未解決fail。曾失敗的CSV validator row-cardinality與PDF backend由獨立檢查攔下，修正後重跑PASS；所有attempt logs／receipts保留。另修正Phase9 CSV publication的Git換行轉換：新增局部`.gitattributes`保留原始CSV bytes，加入index對working-tree精確byte guard及負例測試；原始分析數據不變，歷史commits保留。

`GATES_BLOCKED`：物理matched signal norm、HF排他定義、fake calibration、single-H／detector物理校準、nuisance值與correlation、充分MC支撐，以及未經使用者核准的PDF／PNG publication。

`GATES_UNKNOWN`：future compatible transfer factors、corrected matched signal rate/error、未校準nuisance values/correlations。未知不是0。

`NEXT_RECOMMENDED_STEP`：先審閱A–G報告及本機最終圖；科學工作優先定義可驗證的HF matched／exclusive來源與fake measurement方案，再處理獨立signal normalization及MC support。任何新積分或production均需另案授權，不能由本次成功診斷自動啟動。