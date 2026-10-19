# Phase11E：光子控制分母、detector 原始碼與既有事件交叉驗證

本階段將未來可保存的控制候選具體化為可審查的 **inactive detector-card diff**。原始碼支持在不改變原選擇的情況下，另外保存通過 PhotonEfficiency、尚未套用 isolation 選擇的候選集合，以及 isolation 選中但尚未去除物件重疊的集合。這是 **SOURCE_SUPPORTED／PARSER_NOT_VALIDATED／PHYSICAL_PILOT_NOT_EXECUTED**，不是新模擬或量測。

**PHOTON_FAKE_RATE=UNKNOWN**。現有檔案的 nonisolated photon 分母沒有被保存；額外保存 Delphes 候選也不會自動建立 ATLAS tight／anti-tight ID、conversion 分類、真實資料控制分母或校準 fake rate。標準 TreeWriter 對精確 Candidate overlap graph 的保存仍為 **BLOCKED_REQUIRES_REVIEWED_WRITER**。

## 精確來源與集合順序

本次以 Phase8 manifest 的路徑與 SHA-256 核對 B01、B02、B03 當時真正使用的 runtime card，並唯讀檢查既有 Delphes 3.5.1 build source。沒有載入 Tcl，沒有執行 Delphes，也沒有重建原生程式。三張歷史卡片的識別如下；完整路徑、執行序列、原始碼行號與前後雜湊在 `phase11_detector_source_trace.json`。

| 來源 | 歷史 runtime-card SHA-256 |
|---|---|
| B01 | `cd91fc7982365af23e4002c6295418fbbc0077ffe381e992e7e6070052eb1f47` |
| B02 | `5507d5a49492512aa454193c3b1de007933050bf91d50c11caf751618b8a3522` |
| B03 | `762d5ff5f44b3f41783b086636df53c3c563e9ad673afd867d64926ae0b6f134` |

光子鏈是 `ECal/eflowPhotons → PhotonEfficiency/photons → PhotonIsolation/photons → UniqueObjectFinder/photons → TreeWriter:Photon`。電子鏈是 `HCal/eflowTracks → ElectronFilter/electrons → ElectronEfficiency/electrons → ElectronIsolation/electrons → UniqueObjectFinder/electrons → TreeWriter:Electron`。jet 鏈由 `Calorimeter/towers → FastJetFinder/jets → JetEnergyScale/jets`，再接受 flavour association、bit0 b-tag 等處理，最後才進入 UniqueObjectFinder。

UniqueObjectFinder 的順序是 photon、electron、muon、jet；前面的集合具有優先權。此卡沒有設定 `UseUniqueID`，3.5.1 的預設為 false，故使用遞迴的 `Candidate::Overlaps`，不是單純的幾何 DeltaR veto。TreeWriter 排在最後，歷史 Photon／Electron／Jet branch 都來自 UniqueObjectFinder 的輸出。

| 審查來源 | SHA-256 |
|---|---|
| classes/DelphesClasses.cc | `4af575be5300f59c58c81e86a9c04a817fd9ce40d01ee91760b86706f72b03ef` |
| classes/DelphesClasses.h | `ed65180989c34410390cf36ca2499009ecc123f243260d25f7cde49cb2ac5ce9` |
| modules/Efficiency.cc | `cd900285e24e08816e2f872d65ee657049d5a46285bd49d68ef02627d54e0dc9` |
| modules/Isolation.cc | `e8f12d4a008446742f632aad918f752155ecad408ef0a45272a27e49ed0a7724` |
| modules/TreeWriter.cc | `493b200746370317e16be7060aa531947c592af1c4e15bcd0aa29ceb3dcbdd92` |
| modules/UniqueObjectFinder.cc | `17bca136f0a78545719286d49a6d8798654e20c958af359a461aaabd223fb172` |

這些是具體的原始碼身份與靜態語義證據；並未以原始碼閱讀冒充新編譯、parser test、TRef runtime closure 或 detector 物理驗證。

## 為什麼 pre-isolation branch 可以保存失敗候選的 isolation 分量

`Efficiency::Process` 將原本的 Candidate 指標加入輸出陣列，沒有建立候選快照。`Isolation::Process` 對輸入陣列的**每一個候選**先寫入 `IsolationVar`、`IsolationVarRhoCorr`、`SumPtCharged`、`SumPtNeutral`、`SumPtChargedPU`、`SumPt`，然後才檢查 cut 並 `continue`。接受的候選加入輸出陣列時仍是同一個指標。因為 TreeWriter 最後才執行，讀取 PhotonEfficiency 輸入集合時可看到包括 isolation 失敗候選在內、已經計算完成的這六個欄位。

因此 `PhotonPreIsolation` 表示「isolation 篩選前的**集合成員資格**」，並不是「isolation 計算前的欄位快照」。這個分母仍以 PhotonEfficiency 通過為條件；該模組的 pT／eta 效率與隨機選擇早已生效，不是所有真實 photons 或 jets 的分母。既有 EFlowPhoton Tower branch 也不能直接改稱校準 photon-ID candidate。

歷史 isolation 使用 `DeltaRMax=0.5`、`PTMin=0.5 GeV`、`PTRatioMax=0.12`。isolation 物件的 pT 小於 PTMin 才排除，cone 判斷為 DeltaR≤0.5，自身排除以 Candidate UniqueID 不同判斷。`UsePTSum=false`，`UseRhoCorrection=true`；此卡沒有 RhoInputArray，所以該模組的 rho 是零。有效的 rho-corrected ratio 使用 `(chargedNoPU + max(neutral - max(rho,0)*pi*R^2,0))/candidatePT`；DBeta 版本與所有六個分量另行保存。這些設定是 Delphes 固定 cone 的實作，不等同 MG5 smooth-cone Frixione，也不等同 ATLAS 校準 isolation 或 ID。

## 未來的最小 inactive 差異與仍未解決的身份問題

`analysis/phase11/config/inactive_detector_diff.txt` 的每一行都是註解，不能被誤當成可執行的卡片。本次沒有套用差異。它只提出在 TreeWriter 增加五條 branch：PhotonEfficiency 的 `PhotonPreIsolation`、PhotonIsolation 的 `PhotonPostIsolation`、ElectronEfficiency 的 `ElectronPreIsolation`、ElectronIsolation 的 `ElectronPostIsolation`，以及 JetEnergyScale 的 `JetPreOverlap`。原本的 Photon／Electron／Jet branch 與所有 cut 維持原定義。

既有 TreeWriter 可寫入 Photon.Particles、Electron.Particle、Jet.Particles 與 Jet.Constituents 的 native TRef；Particle、Track、Tower branch 已經存在。然而 `FillParticles` 只處理其指定的 candidate 巢狀結構，標準 Photon／Electron／Jet writer 沒有把原始 Candidate UniqueID 複製成精確的跨 branch 身份。共同 truth-reference set 是來源關聯診斷，不能保證重建任意遞迴 Candidate::Overlaps 的原始判斷。

因此另外要求未來經審查的 provenance writer 保存事件鍵、Candidate UID、父候選 UID 邊、來源 Particle ID、pre/post isolation 成員資格、每次 jet/photon overlap 決策及排序後 branch ordinal。需以日後另行授權的有限 readback 驗證重複／空 reference、被排除候選、歧義與一對一身份。在完成這項 writer 與驗證之前，不能聲稱 branch-only diff 已保存精確 overlap graph。

Candidate 內部存在 IsFromConversion，但 Photon v4 writer 沒有把它寫進 Photon；卡片與標準 branch 不會憑空提供 conversion 分類。Photon.Status 的註解不是校準 ID 定義，Electron.EhadOverEem 在此 writer 被直接寫為零，也不是電子鑑別量測。不得從這些欄位創造 ATLAS shower-shape observable 或 fake probability。

## 本次實際既有事件讀回與 source-unit 統計

`audit_detector_events.py` 已由受控命令實際執行。6000 筆 Phase9 native／origin persisted records 以 dataset、來源序號、LHE source-event SHA-256、HepMC event SHA-256、選擇階段與權重做一對一連接；B01–B03 的 3000 筆原始來源事件進入本次統計。所有輸入與原始碼 witness 在讀回前後的雜湊一致。沒有重跑 ROOT loop，沒有重新宣稱完整 raw-HepMC ancestry 分類。

ME outgoing flavour 由既有 hard PDG 列表獨立重算；initial-heavy record、shower birth、direct g→heavy、hadron origin 與歧義標籤沿用 Phase9 凍結證據。eligible jet 的 native flavour 與觀察到的 BTag bit0 逐一核對。完整 photon stage 依凍結 selection JSON 重建：先套用 pT>25 GeV、|eta|<2.37、開區間 crack，再要求 leading pT>35 GeV；不能只用「兩個 accepted photons」取代 leading cut。首次 D01 正是由這個不完整的新檢查失敗，原失敗紀錄保留；D02 修正檢查、加入邊界 fixture 後通過，沒有改動歷史事件或選擇。

| 來源 | input／photon／jet／≥2-tag／final | 含 initial-HF record 的事件 | 含 shower b／c birth 的事件 | 含 direct g→heavy 的事件 | 含 native b／c jet 的事件 | Pythia tuple 歧義事件 |
|---|---:|---:|---:|---:|---:|---:|
| B01 | 1000 / 446 / 266 / 91 / 28 | 58 | 53 / 170 | 211 | 860 / 38 | 0 |
| B02 | 1000 / 378 / 241 / 7 / 1 | 69 | 36 / 211 | 240 | 13 / 902 | 2 |
| B03 | 1000 / 445 / 277 / 0 / 0 | 6 | 49 / 183 | 220 | 18 / 62 | 1 |

這些欄位是**含該旗標的事件數**，不是新生 quark 的總條數；同一事件可能屬於多個 origin 旗標，不可相加。ME 分別仍為 B01=bottom、B02=charm、B03=light/gluon 各 1000 個。hadron endpoint 的 unresolved 狀態保留：B01／B02／B03 分別有 928／959／947 個含 eligible jet 的事件帶此 unknown 旗標，不能把 `ambiguous_hadron_assignment=0` 誤解為唯一的 parton→hadron 來源已被證明。

02_TWO_JETS 母集合的 ≥2-tag 區域遷移如下；mass 邊界完全沿用 Phase8/9：105≤mgg<120、120≤mgg≤130、130<mgg≤160。其他 tag 類別與 unknown mass 均保留在 CSV。

| 來源 | low sideband | Higgs-like | high sideband | broad-window 外 | undefined mass |
|---|---:|---:|---:|---:|---:|
| B01 | 8 | 4 | 16 | 63 | 0 |
| B02 | 1 | 0 | 0 | 6 | 0 |
| B03 | 0 | 0 | 0 | 0 | 0 |

B01 的 91 個 ≥2-tag events 有 63 個在 broad mgg window 外，因此 final=28。B02 的 7 個有 6 個在外，僅 1 個進入 low sideband。B03 的 277 個 two-jet events 都沒有進入 ≥2-tag 類別；其中仍有 native-heavy jets 與非零單標籤事件，因此 final=0 不是物理背景為零的證明。對每一個 0/1000 的未加權 proposal acceptance，本程式保留 one-sided 95% upper limit 0.002991249545095296；此上限不是加權物理截面界限。

共輸出 225 個 origin×stage 列、675 個 origin×tag×mass 列與 3825 個 covariance 上三角元素。每個來源有 50 個 event vectors：五個 nested stages、15 個 origin flags、15 個 final∩origin flags、15 個 tag×mass cells。所有 jets／旗標都以**原始來源事件**為統計單位，固定 N=1000，失敗事件以零貢獻保留。對 `x_i=w_i I_A` 與 `y_i=w_i I_B`，source-sum covariance 為 `N/(N-1) * (sum(x_i y_i) - sum(x_i)sum(y_i)/N)`；巢狀選擇、共用旗標與互斥 region 的相關性分開保留，不能把它們當作獨立 Poisson 分類。

這是固定原始 N 的 proposal sampling covariance；不包括未知的物理 normalization／fake／matching covariance。不同來源的物理相關性保留 null，不用零替代，也沒有 B01+B02+B03 物理加總。signed-weight cancellation、原始 N、負互斥 covariance、null/zero 與來源篡改等方法／負測試已有 27 個 fixture 通過；方法測試不是外部人工審查。

## 可前進與不可前進的範圍

本次確定了未來 isolation 分母的可保存位置、欄位更新時機與 card-only 提案的精確限制，也重新核對了既有三來源的 region migration 與 event-level covariance。要取得實際 fake transfer factor，仍需相容資料的 tight／anti-tight、isolated／nonisolated 定義、electron/conversion controls、prompt leakage／subtraction、flavour 分母及目標區域 transport closure；上述缺口不由此 diff 或既有 MC 標籤解除。

未來 parser／writer／模擬測試均需另外明確授權。本階段 new ME calls、integrals、hard events、Pythia events、Delphes events 全部為 0；沒有新圖、物理總背景、顯著性或 CLs 推論。

## 完整既有數值的獨立回歸

`validate_event_covariance.py` 已在獨立受控命令中實際執行，結果為 **PASS_INDEPENDENT_RATIONAL_BITSET_EXISTING_DATA**。它不匯入 production arithmetic，以 Fraction 有理數與原始事件整數 bitset 重新計算集合交集與 covariance，逐一比對全部 3825 個 covariance 上三角元素；另核對三來源的五階段事件數、source rates 與固定原始 N variance，均與凍結 Phase10 結果相符。總共完成 3885 個數值比對，並明確核對 132 個非空、互斥 region 配對的負 covariance，沒有將共用來源事件視為獨立 Poisson 計數。

完整實際數值驗證的範圍是已逐來源確認等權重的歷史 3000 個事件；其有理數簡化公式以此條件為前提。這不是對一般 signed-weight 新樣本的實際驗證；signed-weight cancellation 由另列 fixture 檢查。獨立驗證器另有 7 個小型正負測試通過。原始 ancestry 標籤仍取自 Phase9 凍結紀錄，沒有重新分類 raw truth，也沒有新 ROOT loop、人工外部審查或物理生成。完整收據為 `phase11_independent_event_covariance.json`。

## Incoming bottom 與 charm 的精確分拆

舊的 `INITIAL_HEAVY_RECORD` 同時包含 b 與 c，不能把全部 combined-HF 事件都視為 proposed p4 所排除的 incoming bottom。Phase9 persisted origins 沒有直接保存 hard incoming PDG，所以新增的 `audit_initial_flavours.py` 已實際串流讀取三個原始 1000-event LHE，重用既有 exact-event-byte parser。每個原始 `<event>` SHA-256 與 source ordinal 均連接到凍結 input index、native 與 origins；原始 contribution、N=1000 與 HepMC event ID 也逐一核對。原始檔案與 parser 的雜湊前後不變。這次新取得的是既有 source 的精確 incoming PDG 診斷，不是新 Monte Carlo 樣本。

| 來源 | 含 incoming b | incoming c 且無 b | 不含 incoming b/c | 舊 combined Pythia initial-HF | 僅符合 p4 incoming-PDG domain |
|---|---:|---:|---:|---:|---:|
| B01 | 25 | 33 | 942 | 58 | 975 |
| B02 | 2 | 67 | 931 | 69 | 998 |
| B03 | 0 | 6 | 994 | 6 | 1000 |

**B03 的 6 個 initial-HF events 全是 charm，incoming bottom 為 0；B01 與 B02 的 combined-HF 亦大部分為 charm。** Proposed `p4 = g u u~ d d~ s s~ c c~` 允許 c，因此正確的 incoming-PDG-domain 排除項是 incoming b，不能用 combined-HF 計數替代。B01 的 b ordered pairs 為 `(5,-5):15`、`(-5,5):10`；B02 為 `(5,-5):2`；B03 沒有 b pair。三來源的 c pairs 分別為 `(4,-4)/(-4,4) = 18/15、32/35、4/2`。

| 來源 | 歷史 incoming 子集 | input | two jets | ≥2 tags | final |
|---|---|---:|---:|---:|---:|
| B01 | incoming b | 25 | 7 | 4 | 1 |
| B01 | incoming c without b | 33 | 8 | 3 | 1 |
| B02 | incoming b | 2 | 0 | 0 | 0 |
| B02 | incoming c without b | 67 | 18 | 0 | 0 |
| B03 | incoming b | 0 | 0 | 0 | 0 |
| B03 | incoming c without b | 6 | 3 | 0 | 0 |

此 source audit 保存 3000 個來源身份／ordered PDG event rows、400 個 category-or-exact-pair×stage rows，以及 1395 個固定原始 N 的 covariance 上三角元素。b/c 旗標、combined Pythia record 與 p4-domain 旗標的各階段加權 contribution、variance 與交叉 covariance 均以原始事件為單位保留，沒有改動歷史權重或 B01–B03 的選擇。12 個小型正負 fixture 包括 charm 允許、bottom 排除、mixed b/c、beam 順序、無效 incoming multiplicity、截斷、signed covariance、zero interval 與無 production dispatcher 檢查。

`SOURCE_INITIAL_PDG_ALLOWED_BY_P4_ONLY` **只檢查 incoming PDG 的集合資格**，不代表 975／998／1000 個事件可以被重用或重新標記為物理 4F 樣本。原事件的 massless-b model、5F PDF、alpha_s、硬過程、積分與 shower 仍是原設定；篩掉 incoming-b events 不會將它們轉成 massive-b 4F prediction，也不能恢復被替換的 PDF／mass-dependent matrix element。B03 觀察到 0 incoming-b 也不構成其過程定義排除 bottom 的證明。4F PDF／alpha_s／質量與獨立未來生成的相容性 gate 均維持原判定。
