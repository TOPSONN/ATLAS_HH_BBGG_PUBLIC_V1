# Phase10E：光子假訊號轉移因子的可行性

本階段的實際轉移量測為 **BLOCKED_MISSING_COMPATIBLE_OBSERVABLES**；物理光子假率保持 **UNKNOWN**。完成的工作是既有事件的可觀測性讀回、公開校準適用性審查，以及標明 **SYNTHETIC_METHOD_ONLY** 的二維旁帶方法測試。方法閉合不解除物理背景、顯著性、CLs 或耦合區間的阻擋。

## 證據、分母與實際支持

實際事件來自 Phase8 的六個完整背景檔，每個 1000 個原始獨立來源事件。Phase10 原生標量 profiler 只為一個新的問題讀回 6000 個既有 Delphes events：Phase8/9 的正規化事件輸出沒有保存全部 ID／隔離／conversion 控制欄位，僅讀 dictionary 無法知道欄位是否實際有值。本程式重用 Phase8 的原生 Adapter、dictionary／streamer 檢查與檔案 SHA-256 驗證；不複製完整事件 reader，也不重跑 signal ROOT events。前後來源驗證均須通過。ROOT 為 6.40.04，C++20。

後續 Python 將 Phase9 native 與 origins_03 的完整 6000 事件，以 dataset、source ordinal、source event SHA-256、HepMC event SHA-256 做一對一連接，要求事件分母、五階段選擇與各原始 cutflow 相同。Phase10 原生 profiler 是 scalar inventory，完整來源 ancestry join 的依據仍是 Phase9。兩者的證據範圍不混用。

Phase9 選中的重建光子物件共 6999 個：

| 來源標籤 | 物件數 | 解讀 |
|---|---:|---|
| PROMPT_HARD_PROCESS | 6298 | 已有的 hard-root／copy-chain 來源證據 |
| SHOWER_RADIATION | 24 | 放射來源診斷 |
| ELECTRON_ASSOCIATED | 3 | 電子關聯診斷，非校準 electron-to-photon rate |
| UNCLASSIFIED | 674 | 來源無法唯一確定，保留 unknown |
| HADRON_DECAY | 0 | 此 selected-object 標籤計數為零 |

這是物件計數，分母不是所有真實 jets，也不是 tight／anti-tight 控制候選。674 個 unclassified 不改標 fake；不同來源旗標與事件選擇亦不能自動轉成 fake-rate 分子分母。

B06 的歷史 cutflow 維持 **[1000, 2, 2, 2, 0]**。其中 1000 個輸入事件、2 個 two-photon selected events、0 個 final events，既沒有相容的假光子控制分母，也沒有 transfer closure，故不是 fake-rate measurement。不能用 2/1000 充作 jet-to-photon probability，亦不能以 final=0 宣稱物理 fake background 為零。

## 實際 Delphes 欄位與未保存的控制事件

原生 dictionary 為 Photon v4（checksum 4175710330）、Electron v4（3973934735）、Jet v5（527275606）。標量 profiler 保存每個欄位的物件數、finite／nonfinite、nonzero、min／max 與最多 64 個 distinct values；distinct 清單超限會明確標 capped，並不是完整分布。

| 樣本 | 原生 Photon | Photon IsolationVar 非零 | IsolationVar 最大值 | 原生 Electron | 原生 Jet |
|---|---:|---:|---:|---:|---:|
| B01 | 1600 | 319 | 0.1199259683 | 0 | 2535 |
| B02 | 1483 | 345 | 0.1196391210 | 0 | 2784 |
| B03 | 1562 | 352 | 0.1175874323 | 0 | 2706 |
| B04 | 1386 | 268 | 0.1167337000 | 0 | 2480 |
| B05 | 1345 | 463 | 0.1175835729 | 132 | 5536 |
| B06 | 703 | 194 | 0.1145635247 | 0 | 3527 |
| 合計 | 8079 | 1941 | 0.1199259683 | 132 | 19568 |

這些是原生輸出物件；8079 不應和通過 Phase8 fiducial/selected 定義的 6999 混為同一分母。

Photon 實際包含 PT、Eta、Phi、E、T、EhadOverEem、IsolationVar、IsolationVarRhoCorr、SumPtCharged、SumPtNeutral、SumPtChargedPU、SumPt、Status，另有 generated-particle references。後者不構成 shower-shape ID。Photon 的 **EhadOverEem、Status、SumPtChargedPU 在六個樣本全部為零**；不能僅因欄位存在就宣稱具有 fake truth label、ID 判別力或 pileup 資訊。IsolationVar 與 isolation sums 則有非平凡值。

Electron branch 存在，但只有 B05 的 132 個候選；其 charge、isolation 和 impact parameters 可讀，並不等於 ATLAS tight identified electron 或 Z→ee/eγ 控制分母。Jet Flavor 與 BTag 有非平凡值，但 FlavorAlgo、FlavorPhys 皆零；原生 flavour、hadron ancestry、hard-process flavour 和 sampled bit0 tag 維持各自語義。

歷史 detector card 明確執行 PhotonIsolation：CandidateInputArray=PhotonEfficiency/photons、IsolationInputArray=EFlowFilter/eflow、DeltaRMax=0.5、PTMin=0.5、PTRatioMax=0.12。UniqueObjectFinder 接收 PhotonIsolation/photons；TreeWriter 最後只輸出 UniqueObjectFinder/photons。Electron 亦先經同形式隔離。這是既有 Delphes study 定義，沒有新增或調整閾值。實際 Photon 隔離值皆低於 0.12 與此流程一致，但**沒有保存原本失敗的 photon 候選集合**。把已通過隔離的物件再切一個較低閾值，不能回復被刪掉的 nonisolated 控制分母。Track、Tower 或 EFlow 存在，也不等於重新建立且驗證過的 photon ID／conversion 或反隔離 candidate。

| 量測需求 | 現有狀態 | 阻擋原因 |
|---|---|---|
| tight／anti-tight ID | ABSENT_VALIDATED_DEFINITION | 無 ATLAS shower-shape cut 變數或 validated ID 位元 |
| isolated／nonisolated | CENSORED_NONISOLATED_DENOMINATOR | 只保存隔離之後的 photon collection |
| converted／unconverted | ABSENT | 無相容 conversion vertex/category 定義 |
| electron control | PRESENT_UNCALIBRATED | 候選存在，緊電子分母與 Z 控制校準不存在 |
| prompt leakage | TRUTH_DIAGNOSTIC_ONLY | ancestry 診斷不是控制資料中的 prompt subtraction |
| background subtraction | ABSENT_COMPATIBLE_CONTROL_DATA | 缺資料控制樣本、減除量與聯合 covariance |
| jet composition | PRESENT_DESCRIPTIVE | 有 flavour／tag 診斷，沒有控制區到目標區的 transport closure |

## 公開官方校準審查

新 catalog 為 analysis/phase10/config/photon_public_calibration.json；Phase9 原 catalog 保持不變。只檢查公開 ATLAS Collaboration 主文；沒有讀入 restricted material，也沒有下載圖作為新產出。此為有範圍的來源審查，不能解讀為全球不存在相容的公開校準。

[ATLAS HH→bbγγ，arXiv:2112.11876v2](https://arxiv.org/pdf/2112.11876v2)，2022-09-12 版本、PRD 106 052001，使用 2015–2018、13 TeV、139 fb⁻¹，公開 CC BY 4.0。第 4.3 節以 tight photon 的 ID／isolation controls 推定 common-preselection mass-sideband composition；第 5.2 節進行 data-sideband normalization。分母是該分析選中的 sideband events，並非所有 jets。quoted composition 誤差含統計與 ID 選擇系統項；未提供可直接搬到本 Delphes 定義的完整相關矩陣。適用判決為 METHOD_ONLY，不匯入 fractions 或 fake probability。

[ATLAS photon-ID，arXiv:1810.05087v2](https://arxiv.org/pdf/1810.05087v2)，2019-03-29 版本、EPJC 79 205，使用 2015–2016、13 TeV、36.1–36.7 fb⁻¹，公開 CC BY 4.0。第 3 節的 converted/unconverted tight photon 倚賴 calorimeter shower shapes；prompt-ID 分母是 isolated genuine photons。第 6 節 electron transfer 的分母是正確重建且通過 electron selection 的電子，transfer 為錯認成 photon 的機率與正確認成 electron 的機率之比，乘上相容 electron control yield。ID／isolation 依賴、Z 控制背景減除及能量校準誤差不可忽略；本地無對應 conversion／ID／控制分母與 covariance。適用判決仍為 METHOD_ONLY。prompt efficiency、electron transfer 與 jet fake transfer 三者不能互換。

未來任何校準匯入均須同時驗證 version、energy/period、object 定義、分母、pT/eta、conversion、jet flavour/b-tag 環境、prompt leakage／subtraction、shared-control correlations、target closure 與 license。source compatibility validator 明確拒絕 prompt-ID efficiency、electron transfer、synthetic source 及缺控制資料的輸入。

## Synthetic-method-only 二維旁帶

以下數字全部是人造方法 fixtures，不是上述 6000 事件的 fit。此處的 tight／anti-tight 是外部傳入且已互斥的布林標籤；程式不替現有 Delphes 發明 ID 閾值。四區定義為：

| 區域 | ID | 隔離 | 用途 |
|---|---|---|---|
| A | tight | isolated | 目標 |
| B | tight | nonisolated | 控制 |
| C | anti-tight | isolated | 控制 |
| D | anti-tight | nonisolated | 控制 |

令 F_r=N_r−P_r，P 為 prompt contamination 估計；κ_ID,iso=F_A F_D/(F_B F_C)。假設 κ 有外部、獨立驗證的值，則預測 F̂_A=κ F_B F_C/F_D。C/D 是 anti-tight 中 isolated-to-nonisolated 的 **yield transfer ratio**，並非 per-jet fake probability。κ=1 表示此二維 fake-only 分布的 factorization；不是預設適用於真實資料的定律。此 κ_ID,iso 與 Higgs 自耦合 κ_lambda 無關。

九維輸入向量為 (N_A,N_B,N_C,N_D,P_A,P_B,P_C,P_D,κ)。程式先檢查 covariance 有限、對稱與半正定，再以完整 Jacobian 計算 gᵀΣg；保留 N–P、跨 region、κ 與各 yield 的交叉項。closure residual F_A−F̂_A 也用同一聯合 covariance，包含觀測目標與預測共享事件的影響。若 κ 來自同一區域的 fit，必須提供相應 covariance，不能把代數自我閉合當獨立驗證。

固定 N 個獨立來源事件的 vector-total covariance 使用 N/(N−1) Σ_i(v_i−v̄)(v_i−v̄)ᵀ。每個來源事件先聚合全部候選及 subtraction contributions；同一事件不能拆成多個獨立 photon。互斥 categorical region 的負 covariance 亦保留。不同獨立減除來源須分別算 block，再以實際共同 nuisance 建立聯合 covariance。這是 sampling variance；物理 normalization uncertainty 仍須另外提供。

人造案例的結果：

| fixture | 預測 A | prediction variance | 結果 |
|---|---:|---:|---|
| F=[120,80,60,40]、κ=1，獨立 Poisson 區域 | 120 | 780 | closure residual=0 |
| N=[150,90,80,45]，P=[30,10,20,5] | 120 | 1075 | prompt 減除後閉合；減除誤差有傳播 |
| A=180、B=80、C=60、D=40、κ=1.5 | 180 | 0，僅代數 fixture | 強設 κ=1 會少 60 |
| 300 個獨立事件、同事件 P=0.25N | 90 | 413.127090301 | 事件 influence 獨立實作=413.127090301 |
| 上一案例錯設 N 與 P 獨立 | 90 | 780.351170569 | 顯示忽略 subtraction 共變異的影響 |

第三列零 variance 是明確固定輸入的代數檢查，不能宣稱實際 κ 無誤差。fixture 的區域 Poisson 假設與固定 N categorical 假設各自標示；不能不加說明互換。

D≤0 時回傳 invalid，沒有 0-rate fallback；B 或 C 零支持時不提供有限相對精度。負的 F=N−P 預設無效；可選的 signed diagnostic 計算仍標 valid=false／diagnostic_only=true，絕不截成零或變成物理 yield。D≤3σ_D 會標 ILL_CONDITIONED_DENOMINATOR，避免把不穩定 ratio 的一階 delta 誤差當可靠區間。這是 synthetic stability guard，不能取代日後資料 likelihood、profile interval、coverage 或 nuisance validation。

12 個 synthetic scenario checks 全數通過；20 個 focused tests 包含互斥性、prompt contamination、κ correlation、zero C/D、負 subtraction、full covariance、finite-difference Jacobian、獨立 categorical/influence variance、ill conditioning、來源 key/stage 拒絕與校準語義拒絕。這些測試驗證方法與防呆，不是 data-driven fake-rate closure。

## 交付與下一步邊界

原生 scalar inventory 為 phase10_native_photon_observability.json；完整可觀測性與來源 join 為 phase10_photon_observability.json；人造方法結果獨立保存在 phase10_synthetic_sideband_tests.json，且每項 method result 都帶 physical_usable=false。物理校準數值為 null，PHOTON_FAKE_RATE=UNKNOWN，實際 transfer measurement=BLOCKED_MISSING_COMPATIBLE_OBSERVABLES。未形成 physical total background。

下一個可審查的契約是先取得相容且獲授權的 data controls，凍結 photon/electron/jet 分母、ATLAS ID/anti-ID 與 conversion 分類，估計 prompt leakage/subtraction/full covariance，再在目標 pT/eta、0/1/≥2-tag 與 mass regions 驗證 transport closure。現有檔案不能事後生成缺失的 candidate denominator。此階段沒有新 ME、integrals、hard events、Pythia 或 Delphes events；沒有建立、再生或發布 PDF/PNG。
