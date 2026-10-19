# Phase 10D：未啟用的物理 pilot source contract

證據類別：**FUTURE_UNEXECUTED_PROPOSAL**。狀態：**PREPARED_INACTIVE_BLOCKED**。實際 physical pilot：**NO**。MG5 parser、ME、積分、Pythia、Delphes 均未執行。Exact-source approval receipt 和 external independent human review receipt 均為 null。

可審查的完整 contract 位於 `analysis/phase10/config/generator_pilot_contract.json`；離線驗證後的本機產物應為 `phase10_future_pilot_contract.json`。驗證器只讀 JSON／註解卡，回傳 `valid_inactive_contract`；通過代表「阻擋條件和未啟用狀態一致」，不授予物理生成許可。

## 1. Exact process syntax 與模型版本

核對來源為 MG5_aMC 3.5.16（VERSION 2026-06-03）及 Pythia 8.317（版本日期 20260120）。完整 SHA-256 位於 generator review 的 local source audit；未來 approval 仍須綁定當時精確來源、build、model、PDF 與 card hashes。

第一個供未來評審的 bounded component 是：

```text
import model sm
define p4 = g u u~ d d~ s s~ c c~
generate p4 p4 > b b~ a a QCD=2 QED=2
```

這裡的 source restriction 是 MC=0、MB=4.7 GeV。這是 **4F massive-bottom 成分的 syntax proposal**，不是已驗證的 4F prediction；相容 4F PDF、alpha_s、photon IR 目標和 shower contract 全未凍結。未執行 MG5 syntax validation。該成分不代表整個 inclusive 背景。

另一候選是 `sm-no_b_mass`、包含 incoming 和 final additional b/c 的共同 aa＋0、1、2 QCD-parton family；exact lines 在 JSON 和 `gamma_gamma_hf_processes.inactive.txt`。0..2 是供評審的有限 family，不代表已證明足夠的 Nmax，也不包含所有 loop-induced／mixed-coupling／fragmentation diphoton physics。

所有 `.inactive.txt` 的每行均為註解，含 `FUTURE_UNEXECUTED_PROPOSAL; DO_NOT_EXECUTE`；沒有 output、launch、積分、shower 或 generator dispatcher。解除註解也不構成授權。

## 2. 未凍結欄位與必須先解決的 blockers

| 項目 | 現有可證來源 | Contract 狀態／未來要求 |
|---|---|---|
| Model masses/flavours | sm／no_b_mass／c_mass restriction bytes 已讀取 | 選定一致 mass/PDF/initial-HF/final-HF 定義；目前 selected=null |
| PDF／alpha_s | 歷史來源有 CTEQ6L1；不構成新方案驗證 | exact set/member/LHAID/hash、flavour thresholds、ME/ISR/FSR order/value 全 null |
| Hard scale | 本機有 dynamic/fixed scale 欄位 | 中央定義及變化未定；不得無聲沿用 fixed125 |
| ME/PS interface | generic MLM／CKKW-L／FxFx 存在 | exact process/order/flavour 適用性待證，selected_scheme=null |
| Matching scales | 本機模板與文件確認欄位 | xqcut/qCut/TMS/qCutME 全 null；禁止用自動預設冒充 validated value |
| Shower | Pythia 8.317 source 可審查 | QCD g→bb/cc、QED radiation、tune/MPI/hadronization、starting scale 未凍結 |
| Photon cuts/isolation | MG5 有 smooth-cone 欄位 | pT/eta/ΔR/質量/isolation 數值全部 null；先解決 IR／fragmentation 範圍 |
| Flavour jets | 已確認一般 flavour label 有 IR 問題 | flavour-safe truth definition、hadron/reco migration 與未知 ancestry policy 未定 |
| Weight convention | 歷史 average、IDWTUP=-4 可追溯 | 新來源需讀本身 headers、signed sumW/sumW2、接受截面與 merging weight |
| New output identity | 本階段只有 source artifacts | 未來目錄=null；必須是新目錄、unique IDs，不能覆寫任何 Phase6–9 |
| Approval/enforcement | 沒有 physical pilot approval | exact-source receipt、finite envelope approval、獨立 enforcement review 都缺 |

Matching 狀態保留 **NO_VALIDATED_MATCHING_PRESCRIPTION_YET**。官方 FxFx 文件限制最低 core 含 jets／b 的方案，因此不能把上面的 bbγγ core 換成 FxFx 就稱問題已解決。[官方 FxFx requirements](https://amcatnlo.web.cern.ch/FxFx_merging.htm) 本機 CKKW-L 文件要求 event weight、merging weight 和 accepted cross-section normalization 的一致處理；未來須直接測試實際 HepMC conversion。[Pythia CKKW-L](https://pythia.org/latest-manual/CKKWLMerging.html)

## 3. 未來有限 matching scan，現在不執行

先由獨立 source review 選定一個 process／order／flavour 處方，確認 photon observable、jet coverage 及共同 generation cuts。再以目標 hard scales、ME cut 和 shower history 決定 **有限且明列數值的** scale grid。本 contract 刻意不填入 scale values；未來填值會形成新的 exact-source/card 版本，需重新評審與明確批准。

獲准後才可在新的 output directory 執行預先限定的 scan。每個 multiplicity 保留 attempted/accepted/vetoed/failed/written counters、source IDs、權重、cross section 及 integration error；比較 DJR、HF-resolved jet rates、inclusive shapes、cut loosening、scale/seed dependence 和 normalization closure。任何 gap、double coverage、IR instability、權重無法閉合或 tail 支持不足，都保留未驗證狀態。

最多 3 個 scan points 只是下列資源草案的規模假設，並不是核准的 scan，也不保證足以確立物理處方。所有 points 合計不得超過未來另行批准的總上限。

## 4. Resource estimates 與統計目的

以下是 **illustrative operational ceilings**，未批准、未測量、未實作 enforcement：

| 整個未來候選工作合計 | 草案 ceiling |
|---|---:|
| CPU threads | 2 |
| Wall time | 7200 s |
| RAM | 4 GiB |
| Disk | 2 GiB |
| New independent hard events（所有 scan 合計） | 1000 |
| Scan points | 3 |
| ME evaluations | 1,000,000 |
| Integration cycles | 20 |
| Event trials（含拒絕） | 100,000 |

這些有限數字是供另行 source/resource review 的停止界限，**不是 performance 預測或目前允許的用量**。目前沒有匹配方案的 ME／積分時間資料，因此新 ME wall forecast=null。未來若不能實際 enforce evaluations/cycles/trials 等 cumulative caps，pilot 仍為 BLOCKED。

可讀的歷史成本參考是 `metadata/phase6b_event_summary.csv`：已存在的 LO LHE 1000 bbgg／ccgg 事件，當時 shower CLI 約 14.21／16.99 s，HepMC gzip 約 25.20／27.38 MB。這排除了新 ME、積分、matching veto、NLO、Delphes，不能當新 pilot 的工期保證。僅以 4 倍 gzip 容量作 bookkeeping／temporary-copy 假設，對應約 100.82–109.52 MB；新 source tree、integration scratch 和 detector outputs 另未知，亦可能在 2 GiB cap 內仍無法完成。原 CSV SHA-256 已列入 local source audit。

Pilot 目的是可行性、權重和差分率 sanity checks；1000 total events 分攤後，不保證 10/20/30/50% 的任何 final-bin precision。歷史 B01 28/1000、B02 1/1000、B03/B06 0/1000 只是後續 precision plan 的既有參考；zero support 不提供有限 guaranteed N。需求必須由新 approved pilot 的實際 independent-source variance、signed weight behavior 與 bin support 再估計。細節與 kappa support 另見 Phase10F；不得把 resampling 當新的 hard statistics。

## 5. Truth identity、independent checks 與 failure criteria

所有 source events 在 rejection 前即給唯一 run/dataset/source-event identity，保存原 LHE init／weight headers、完整 nominal/variation weights、integration uncertainty 以及 denominator。HepMC 和 detector 若日後另獲准，仍須一對一追蹤來源，保存 ancestry、unknown links 和 loss/failure counters；ME/shower/hadron/reco/bit0 labels 分開。

未來 source review 要求獨立重算 signed sumW/sumW2、normalization、covariance；檢查能動量、mass shell、joins、IR/collinear limits、multiplicity coverage、veto efficiency 和 flavour migration。這些是待執行的 reviewer checklist；此文件沒有虛構外部人員簽核。

任何 unapproved physical command、非零 Phase10 new-production counter、overwrite historical source、未知 PDF／photon IR／matching parameter、無法 closure 的權重或 cap exhaustion 都停止。樣本不足只能回報 inconclusive，不可放寬資源或升級 physical gate。

`PHYSICAL_TOTAL_BACKGROUND=BLOCKED`；`MATCHED_SIGNAL_NORMALIZATION=BLOCKED_PHASE7I`；physical significance／CLs／kappa interval 均 NOT_EVALUATED。圖像仍需依 AGENTS 的 exact path/hash/caption/provenance approval 後才可 commit/push。

## 6. 離線驗證介面

```text
python3 analysis/phase10/scripts/validate_pilot_contract.py --output /home/btu/simulations/hh_phase10/run_01/phase10_future_pilot_contract.json
python3 -m unittest discover -s analysis/phase10/tests -p test_phase10_generator_schemes.py -v
```

這兩個命令只檢查 source proposal 和小型 mutation fixtures；前者寫入含 offline_validation 的 contract JSON。它們不呼叫 MG5/Pythia/Delphes，亦不聲稱完成任何物理 pilot。
