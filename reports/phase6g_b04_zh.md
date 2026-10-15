# B04 實際 1000-event 鏈

目前狀態：`PASS_FULL_CHAIN_MODEL_SCOPE`。實際 source / validated HepMC / validated ROOT 為 1000 / 1000 / 1000；完整物理資料鏈 PASS = `True`。

| 項目 | 實測或凍結設定 |
| --- | --- |
| Hard process | `generate p p > z h QCD=0 QED=2, z > b b~` |
| 模型/PDF | sm-no_b_mass；5F massless b/c；內建 CTEQ6L1 LO |
| 碰撞能量 | 13000 GeV；兩束各6500 GeV |
| muR=muF (GeV) | 216.188 |
| Source cross section (pb) | 0.08953800 |
| MG5 integration uncertainty (pb) | 0.0003975100 |
| Seeds MG5/Pythia/Delphes | 20261104/610401/610501 |
| 完整原始 denominator | 1000 |
| Unique independent source streams | 1 |

Exact frozen Phase6F muR=muF=MZ+MH=216.188 GeV LO pilot.

實際 amplitude/card gate：`{"receipt_sha256": "b6377a1bf9f65949e42734318342ac751e40960b47d1544fbbaca0a9d7603467", "records": 6, "production_records": 5, "Z_decay_records": 1, "diagram_sum": 6, "orders_by_scope": {"Z_decay": [{"QCD": 0, "QED": 1}], "production": [{"QCD": 0, "QED": 2}]}, "actual_parameters": {"mdl_MZ": 91.188, "mdl_MH": 125.0, "mdl_MT": 173.0, "mdl_WZ": 2.441404, "mdl_WH": 0.00638233934, "mdl_WT": 1.4915, "mdl_WW": 2.0476, "mdl_ymt": 173.0, "aEWM1": 132.507, "mdl_Gf": 1.16639e-05, "aS": 0.129783}}`。Initial/header/post-working-card/final internal seeds分開記錄：`{"initial_request": 20261104, "effective_header": 20261104, "post_run_working_card_iseed": 0, "final_internal_randinit": "r=20261110", "scope": "Different stages: MG5 working-card reset after reading seed and internal integration increments are administrative, not additional source streams"}`。

Source 已包含 Z→bb，H 在 source 中穩定。Loop-induced ggZH 與 NLO 不含在此選定 LO component；不重乘 Z BR。

實際完整驗證 receipts 與樣本 hashes：

| Role | Events/Scope | SHA256 | Bytes |
| --- | --- | --- | --- |
| genuine_source_LHE_GZ_1000 | 1000 | `526ac2896b4f8951a4514be2e97846cfbbee3d42ef4db047bf180c0ede7a82c6` | 164495 |
| full1000_HepMC3_ASCII | 1000 | `ae2055e5738ea228b38927c4b4008b6cd2e3ba7acecb28276dd0acd4c38cd0f5` | 95013521 |
| full1000_Delphes_ROOT | 1000 | `eb719ff179918d2be1ac540a1ef617c815241c872e4276e5b2408a7d13c1692c` | 24640561 |
| closed_run_manifest | complete bound receipt | `311843cb430c1e478cb20fa50b676b6225250e3019dd1571754e648f8194fd59` | 191075 |
| complete_LHE_validation | complete bound receipt | `db6a8f3779144d2992d8d1f3f1e804178d8f48b2e6048eb8b579e8fe0fc6c670` | 4429155 |
| actual_MG5_banner | complete bound receipt | `062f1358f8e9cb80f707971459eafbe7260ba37b3cb4a4c23808726b08c3d56d` | 26519 |
| actual_MG5_run_log | complete bound receipt | `6b1980192b741b5ff245ce5aa7881875194b2130c1480a668996dcb916806636` | 11721 |
| native_full_HepMC_reader | complete bound receipt | `62e1db70a028647db8c25f1b56e36e8520223eec179b626c022cb6e3fa0fa7ce` | 2144 |
| actual_full_shower_summary | complete bound receipt | `976058a657f4f74a82014f93011de8abb68a5f488ef189937e5161ce11f6670d` | 3980 |
| full1000_input_index | complete bound receipt | `e4d19bb08a698bca40af6aff88763b7ac4c848890865335a340e19acd0c7ff31` | 47916529 |
| full1000_truth_index | complete bound receipt | `fec43e8fd83cc3fed28150ed2a397e880aa15b787c4455be80ca59b6bf510f04` | 343901 |
| all_event_BR_weight_closure | complete bound receipt | `24da59d300d20346c9723f1df9f4c1b1b20bf89bb0ecc09ccab0692e80de6eea` | 4228 |
| full1000_reco_events | complete bound receipt | `13a1e6e91e8eb2781ef6b46c7043a6918823fe185f1ed95c7af0c4d922f6edd8` | 1426930 |
| full1000_native_cutflow | complete bound receipt | `985069e9449b4a9bb2b59ac7f77769f0648888f5cf8378119b428238f154fc4e` | 365 |
| independent_full1000_statistics | complete bound receipt | `d310ca86f54090c8fb67d7367cf4527282e951446e437c1c6cac01ad4fa01fbf` | 6061 |
| independent_actual_ROOT_and_statistics | complete bound receipt | `3b5b7954fb40c4c2fc73f6b63c98b49ca27b461c7c8eacdee8820297653fb1c8` | 5898 |
| independent_all1000_raw_and_model_weight_closure | complete bound receipt | `49d8740b4bdbb657603a4457a53de09709a9f041512dbe2a636efa32443c9270` | 2133 |

實際 ancestry 計數：

```json
{
  "higgs_two_photon_birth_events": 1000,
  "source_Z_bottom_birth_events": 1000,
  "top_W_model_decay_events": 0,
  "one_Born_photon_identity_events": 0,
  "stable_photon_origin_counts": {
    "born_prompt": 0,
    "shower_radiation": 53,
    "hadron_decay": 64960,
    "other": 2000
  },
  "top_decay_quark_pdg_counts": {},
  "W_birth_product_pdg_counts": {},
  "H_final_photon_multiplicity_histogram": {
    "2": 1000
  },
  "top_W_decay_scope": "inclusive supported Pythia model; production-decay spin correlations unvalidated"
}
```

| Stage | Raw /1000 | Acceptance | Wilson95 interval | Source sum (pb) | Source sum2 (pb²) | MC sampling SE (pb) | MODEL_BR_ONLY sum (pb) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 00_input | 1000 | 1 | [0.996173241514, 1] | 0.089538 | 8.017053444e-06 | 0 | 0.00020562682086 |
| 01_photons | 370 | 0.37 | [0.340626675334, 0.400368281872] | 0.03312906 | 2.96630977428e-06 | 0.00136771554192 | 7.60819237183e-05 |
| 02_jets | 220 | 0.22 | [0.195423493389, 0.246719491363] | 0.01969836 | 1.76375175768e-06 | 0.00117350052171 | 4.52379005892e-05 |
| 03_two_btags | 77 | 0.077 | [0.0620479070606, 0.0951895306182] | 0.006894426 | 6.17313115188e-07 | 0.000755215436597 | 1.58332652062e-05 |
| 04_mgg_105_160 | 75 | 0.075 | [0.0602518049735, 0.0930009397393] | 0.00671535 | 6.012790083e-07 | 0.00074615 | 1.54220115645e-05 |

實際重建變數診斷（有定義事件的線性插值 quantiles；PT/mass為GeV）：

| Variable | Defined/null | q16 | q50 | q84 |
| --- | --- | --- | --- | --- |
| photon_multiplicity | 1000/0 | 1 | 2 | 2 |
| jet_multiplicity | 1000/0 | 1 | 2 | 4 |
| tagged_bit0 | 1000/0 | 0 | 1 | 2 |
| pT_gamma1 | 880/120 | 49.6613014221 | 79.0992050171 | 128.298366089 |
| pT_gamma2 | 502/498 | 29.033946991 | 46.7589626312 | 64.718927002 |
| pT_jet1 | 981/19 | 44.7423187256 | 72.7466964722 | 120.894592285 |
| pT_jet2 | 814/186 | 30.3951799011 | 46.5113658905 | 74.3181478882 |
| m_gamma_gamma | 371/629 | 123.898358383 | 124.954779929 | 126.141689647 |
| m_jj | 605/395 | 65.0671739004 | 90.6993616787 | 172.139480831 |
| m_bb | 182/818 | 59.7352502279 | 82.2914505032 | 97.2143848057 |
| m_bb_gamma_gamma | 77/923 | 233.18765056 | 312.940183299 | 520.954499841 |
| DeltaR_gamma_gamma | 371/629 | 1.45367854253 | 2.36450849529 | 3.03483155605 |
| DeltaR_bb | 182/818 | 0.732517471474 | 1.44504204116 | 2.5444689401 |

H-origin reconstructed match multiplicity histogram：`{"0": 120, "1": 380, "2": 500}`；與 inclusive selected diphoton pair 分開，不把geometricmatch當作calibrated效率。

Raw/source 與 MODEL_BR_ONLY sums 分別保存在 [weight accounting](../metadata/phase6g_weight_accounting.json)。無 implicit luminosity、無 HH factor2、無第二次 sigma/N。未取得官方 calibration 或 validated overlap，不能把這些 streams 相加解釋成完整物理背景。

## 保留的驗證歷程快照

下列為 full1000 detector 完成前保留的歷程；其中「待完成」描述該快照時點，現在狀態以上方 actual receipts 為準。所有原始 failed receipts、source 與 producers 維持 immutable。

# B04 ZH：實際 1000-event source 與下游驗證狀態

一份真正的 MG5 `Z(bb)H` source 已生成，全部 1000 筆 LHE、Pythia/HepMC3、Delphes/ROOT 及獨立唯讀 regression 均已通過。Source 始終是同一份 1000 events；診斷及恢復重用既有輸出，沒有新增獨立 source statistics。此結果是凍結 LO/fast-simulation/model-BR component 的 pilot，不是官方 ATLAS normalization 或 discovery sensitivity。

| 項目 | 已確認結果 |
|---|---|
| Source profile | `B04_ZH_BBGG`；MG5 中 H 保持穩定 |
| 實際 hard process | `p p > z h QCD=0 QED=2, z > b b~` |
| 模型 | `sm-no_b_mass`，五味質子定義，b/c 無質量 |
| MG5 | 3.5.16；既有安裝，未重裝 |
| 碰撞能量 | 13000 GeV；兩束各 6500 GeV |
| PDF | MG5 內建 CTEQ6L1，LO，ID 10042 |
| 固定尺度 | muR = muF1 = muF2 = 216.188 GeV |
| Source Higgs / Z | MH = 125 GeV；MZ = 91.188 GeV；GammaZ = 2.441404 GeV |
| Z resonance 視窗 | `bwcutoff = 15`；54.56694–127.80906 GeV |
| 初始 MG5 seed | 20261104；effective LHE banner 保留此值 |
| 生成 / 驗證數 | 1000 / 1000；invalid = 0 |
| Source cross section | 0.08953800 pb |
| MG5 integration uncertainty | 0.0003975100 pb |
| Source gzip SHA256 | `526ac2896b4f8951a4514be2e97846cfbbee3d42ef4db047bf180c0ede7a82c6` |
| 解壓內容 SHA256 | `b58ef3983969d7bae1fbb765045202def694e668c71366bea21d524b20c5ea6b` |

這個截面是所凍結 LO card、PDF、尺度、Z 寬度及 resonance 視窗下的 `Z(bb)H` component。MG5 已在 source 中包含 Z 衰變，不能再次乘 `BR(Z -> bb)`。這份 source 沒有 Born photons；1000 筆皆保留穩定 H 與實際 Z→b bbar ancestry。Loop-induced ggZH、NLO 修正及完整 precision ZH 預測均不包含在此 pilot。

Source 使用 LHE3、`IDWTUP = -4`、`event_norm = average`。實際 raw XWGTUP 平均為 0.089538000 pb，總和為 89.538000000 pb，沒有 negative 或 zero weights。每筆 source contribution 定義為原始 signed XWGTUP 除以原始完整分母 1000；完整 source contribution 總和為 0.08953800 pb。MG5 integration uncertainty 與未來 selection sampling uncertainty 分開記錄，不再乘第二次 sigma/N，也沒有套用 luminosity。

第一次命令在 MG5 自動儲存 `auto_update` 設定時，被既有安裝寫入保護攔下，沒有進入 amplitude export 或 event generation。修正後，每個 generator/launch `set` 命令採用安裝版本實際支援的 `--no_save`，只改動該程序的設定；安裝內容未變。此失敗的輸出與紀錄保留，沒有替換任何生成統計。

後續唯一的 source production 完成 1000 events，但原 validator 以明寫文字欄位集合判斷 run card，將 MG5 自動序列化的五個既有 implicit defaults 視為差異而停止下游。實際 header 與準備卡的所有明寫 request、physics、cut、scale 值相同。新增欄位只有 `alpsfact = 1.0`、`asrwgtflavor = 5`、`auto_ptj_mjj = True`、`chcluster = False`、`xqcut = 0.0`；它們與官方 `RunCardLO` 讀取原始輸入卡時的 defaults 完全一致。`ickkw = 0`、`xqcut = 0`、`use_syst = False` 保持原值。

修正只接受這五個精確 defaults 的明寫或 implicit 表示；未知額外欄位、非預期 default，以及缺少或改變的明寫欄位仍會失敗。原始 LHE、cards、authority、execution plan 與先前 failed receipt 均未改寫。重新驗證另存新 receipt，並以原始完整 source-file 清單的 canonical SHA256 `caa6fbb5560a0069c557bb4253c8bb9dcf46420d5f1c8f69377377dd15a4ed59` 綁定這一份已生成 source；原始 generator、physics cards、shower runner 及 physics header 維持相同 hashes；read-only reader 的精確 status-context 修正另列為受限例外。這個受限 recheck 不授權新的 MG5 source events。

MG5 在取用 initial seed 後將 working `run_card.dat` 的 `iseed` 重設為 0，並於 integration stages 推進內部 random seed。本次保留的最後 `randinit` 為 20261110。Initial seed、effective banner seed、post-run administrative card 與 final internal seed 分開記錄，避免將這些不同時點的值混為一個 seed。

在首次實際 Delphes 執行之前，ROOT 6.40.04 的 zero-event 檔名測試確認 absolute output filename 會把本機路徑序列化到 ROOT 檔。Delphes helper 因此只將 output argument 改為相同工作目錄中的 `detector.root`；既有 cwd、cards、seed、native binary 與 physics 設定不變。歷史 source recheck 只接受這個精確檔名修正的 hash，並綁定原始 manifest 的 SHA256，要求其中 Delphes entries 為 0 且沒有 Delphes stage。任何其他 Delphes code 改動仍會阻擋。依據：[實際 ROOT 檔名測試](../simulation/new_backgrounds/evidence/root_output_filename_privacy.json)。

重新讀取 gzip 完整內容及 CRC，並對全部 1000 筆檢查 beams、topology、mothers、colors、mass shells、全域及 Z 衰變局部四動量閉合、實際 cards、banner、generator log、signed weights 與來源 hashes。獨立 Decimal 檢查得到最大全域四動量殘差 1.268e-7 GeV，最大 mass-shell 殘差 0.00039104762625714176 GeV²，皆在既定含能量相對項的浮點容差內。原始 failed receipt 保留；修正後唯讀的完整 source gate 為 `PASS_LHE_RECORDS`。

實際 prefix10 的 N_input、N_attempted、N_pythia_next_calls、N_source_identity_verified、N_shower_success 與 N_written 皆為 10；source/shower/internal rejection counters 皆為 0。Generic validator 完整讀回 10 events、3604 particles、1942 vertices，graph、stable mass shell、beam-to-stable 四動量與 hadronization gate 通過，沒有 stable coloured particles。其 receipt SHA256 為 `03f7e36e642580855cae96f0f5e531d353434db9bad874be82af63782bc28232`，原始 HepMC SHA256 為 `ad51a02e982ae83368768e84569f20093de304714c54e7496aadc12a438f9e00`。

專用 ancestry reader 原先以沒有 Event context 的 dummy Pythia Particle 呼叫 `statusHepMC()`，在第一筆中停止；原 receipt 明確是 readback = 1、pass = 0、failed = 1、not assessed = 9，不等同 10 筆皆已完成 ancestry validation。這個 failed receipt、原始 prefix10 與 closed manifest 保留。受限修正重建官方 contextual status 分支，以原始 native index 及完整 daughter graph 驗證；runner、physics header 與 cards 不改。新的 reader 必須先對相同 10 筆 HepMC 通過實際唯讀檢查，才可繼續 100/1000 stages。

修正後的 native reader 已以同一份 prefix10 實際執行，exit code = 0、readback = 10、pass = 10、failed = 0。全部 3604 個 native particles 通過 contextual status 檢查；H→γγ birth 與 Z→bb birth 各有 10 筆。新 reader receipt SHA256 為 `2dc673645bb144a95adabd5820d1927c771f41a511ab6c6cc8b4835ace8417a7`。此檢查未呼叫 MG5、Pythia `next()` 或 Delphes，所有原始輸出與 failed receipts 的 hashes 不變。這只確認既有 prefix10 可由正確 reader 讀回，不等同 full1000 鏈已完成或 H 分支比已採用。數值與 source pins 保存在[序列化及既有事件重新驗證 evidence](../simulation/new_backgrounds/evidence/mg5_official_runtime_serialization.json)。

後續原定的 Pythia full1000 已實際完成，HepMC SHA256 為 `ae2055e5738ea228b38927c4b4008b6cd2e3ba7acecb28276dd0acd4c38cd0f5`，native reader receipt SHA256 為 `62e1db70a028647db8c25f1b56e36e8520223eec179b626c022cb6e3fa0fa7ce`。全部 1000 筆保留 source indices 1–1000、H→γγ birth 與 source Z→bb birth。原始 signed XWGTUP、Pythia Info 與 HepMC converter nominal weights 在 binary64 serialization 精度內閉合；Info 與 converter 最大差為 0，沒有 source index 替換或事件 filtering。

Initialized inclusive Higgs table 的 total width 為 0.0040834219879883659 GeV，γγ partial width 為 0.0000093777064667590622 GeV，實測 model BR = 0.0022965313147512443；forced γγ conditional probability = 1。Full1000 實際 closure 因此允許以 `MODEL_BR_ONLY` 對 missing H→γγ factor 乘一次，model-inclusive sum 為 0.0002056268208601969328 pb。Source 已包含 Z→bb，不重乘 Z BR，也沒有 HH factor 2。Phase6F Pythia reference 與 YR4 comparison reference 0.002270 分別保留；此 model BR 不是官方 ATLAS calibration。原始 source 權重與 model-BR quantities 分別記錄。

ROOT prefix100 的原 analyzer 在 source event14、Jet0 上把已通過歷史 `polar()` bounded signed-mass 規則的個別 jet，再套用適用於 summed vectors 的嚴格 mass check 而停止。Stored mass 為 −1.3486991292666062e-6 GeV，signed mass² 的大小 1.8189893412845017e-12 GeV²，小於原 input double-cancellation bound 4.264015898928536e-11 GeV²。修正保留此 jet 原始四動量，只對 individual jets 檢查 Cartesian finiteness；materially negative native mass、nonfinite values 及 spacelike summed vectors 仍拒絕。Cuts、tagging、native ROOT、cards 與 source events 不變。

實際唯讀重查已通過 ROOT10/100 的全部 110 筆；ROOT100 read = processed = assessed = 100，invalid = skipped = 0。ROOT10 的 reco_events 與 cutflow bytes 完全相同。ROOT100 SHA256 `490e39374e8a6dc9ffe626d2f97f0c07eba59786d03e98482b148c4326de0b3e` 不變，新 validation receipt SHA256 為 `46b0c0e74e5edae0786300beee6b05db9c067abe1283199b54c3214e1ddffb2e`。這次重查的 MG5/Pythia/Delphes invocations 均為 0，沒有新增獨立統計。依據：[signed native jet 實際重新驗證](../simulation/new_backgrounds/evidence/signed_native_jet_revalidation.json)。

Recovery 重用已驗證的 full1000 shower 與既有 ROOT10/100；MG5 event-generation invocation、reused shower new next calls、reused ROOT10/100 Delphes invocations 均為 0。其後唯一尚未執行的 full1000 Delphes/ROOT 已完成，獨立重新編譯的 native analyzer 再讀同一 ROOT1000 通過。Full ROOT SHA256 為 `eb719ff179918d2be1ac540a1ef617c815241c872e4276e5b2408a7d13c1692c`；獨立 replay 的 reco_events、cutflow bytes 與 statistics 均等於 pipeline，沒有修正或替換 detector records。

Full1000 原始 cutflow 為 1000 input、370 photon selection、220 jet selection、77 two-btag、75 通過既有 105–160 GeV diphoton mass window。Final acceptance = 0.075，Wilson 95% interval = [0.06025180497346736, 0.0930009397392545]。Final raw-source contribution = 0.0067153500 pb，finite-source sampling standard error = 0.0007461500 pb；乘一次 model H BR 後為 0.00001542201156451477 pb，sampling standard error = 0.0000017135568405016412 pb。MG5 integration uncertainty 獨立保留，這些 sampling errors 不能當作 generator integration 或官方 systematic uncertainty。

既有 detector card、bit0 b-tag、Photon/Jet selections 與 mass window 不變，不以這 1000 events 最佳化選擇。ROOT readback = assessed = processed = 1000，source denominator = 1000；prefix checks 及重複唯讀 checks 不增加獨立統計。依據：[full1000 獨立 ROOT/numerical QA](../simulation/new_backgrounds/evidence/B04_ZH_independent_ROOT_QA.json)、[full1000 raw/model-BR closure](../simulation/new_backgrounds/evidence/B04_ZH_independent_weight_closure.json)。

依據：[官方 runtime serialization 與實際 source recheck evidence](../simulation/new_backgrounds/evidence/mg5_official_runtime_serialization.json)、[cards 與方法驗證](../simulation/new_backgrounds/evidence/mg5_preparation.json)、[context reader 的實際唯讀修正](../simulation/new_backgrounds/evidence/status_context_readonly_repair.json)。本報告保留原始停止與修正的紀錄，完整鏈的最終數值則來自同一 source 的實際 full1000 outputs。
