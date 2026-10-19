# Phase11 完整驗收報告：精確生成器設定與未啟用 pilot gate

**FINAL_VERDICT：BLOCKED_PHASE11_NO_VALIDATED_COMPONENT。SELECTED_PILOT_COMPONENT：NONE_READY。**

本階段已把模型 restriction、PDF／alpha_s、耦合階數、LO photon isolation、matching 介面、detector 持久化與既有 source-event 身份逐項具體化；沒有為了取得選定方案而填入未經驗證的預設值。A、B 目前都欠缺完整 source-level configuration，故未選定任何第一個物理 pilot。新程式執行成功只代表指定來源／既有資料與方法檢查完成，不代表生成器 parser、matching、物理模型或 pilot 已通過。

另有一項必須獨立報告的例外：受監測的 2874 個歷史資料／報告／來源檔案保持原始 bytes，但已安裝 MG5 的 `input/mg5_configuration.txt` 出現三個不同 raw SHA-256。其有效設定相同不能替代 raw identity；變更呼叫者 UNKNOWN，未還原或改寫安裝檔。安裝 runtime configuration freeze 因此仍受阻。下列所有新物理計數只適用於本任務已登錄的 source／existing-data jobs，不是整台主機的完整歷史程序歸因。

本報告已綁定來源 commit `3652fea6f2dc8bce255cbe8cce49fe8241ba27d4` 與 [Draft PR28](https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1/pull/28)。該來源 commit 的 push／pull_request CI 均成功，125 個 source/evidence blobs 已從 immutable URL 下載並逐 byte 核對。後續僅三個交付文件更新，其最終 HEAD CI／remote closure 另記本機 `FINAL_REPORT.json`。最終 172 項方法測試全通過，不能解除 raw runtime identity mismatch。

## 1. 身份、基底與授權邊界

| 欄位 | 本次結果 |
|---|---|
| PROJECT | ATLAS_HH_BBGG_PUBLIC_V1 |
| TASK | PHASE11_EXACT_GENERATOR_CONFIGURATION_AND_PILOT_GATE_V1 |
| MODE | SOURCE_ENGINEERING_AND_EXISTING_DATA_VALIDATION_ONLY |
| BASE_REVISION | `7b65428648bd3b1040721cf569604e6d8ad1625c` |
| BASE_PR | 27；僅作堆疊基底，不修改舊 PR |
| SOURCE_SCIENCE_PREDECESSOR | `82bb66821c5bbf2bac58e9945fe7c0e9239220dd` |
| NEW_BRANCH | `codex/phase11-exact-generator-pilot-gate` |
| NEW_SOURCE_REVISION | `3652fea6f2dc8bce255cbe8cce49fe8241ba27d4` |
| DRAFT_PR_URL | [PR28](https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1/pull/28)；唯一 stacked Draft，base=PR27 branch |
| GITHUB_CI | PASS：exact source revision 的 push／PR CI；只檢查來源／方法與 bounded evidence，final delivery closure另記 |
| REMOTE_BLOB_VERIFICATION | PASS：source revision 的125檔、2,939,322bytes exact match；final delivery closure另記 |

本次允許文字／設定來源閱讀、既有資料讀回、靜態介面審查、獨立代數測試、inactive card 與有限資源合約。沒有執行 MG5 parser／process generation、ME、積分、新 hard events、Pythia、Delphes、Phase7I build／restart 或物理 likelihood。現有 ROOT 6.40.04／C++20 環境原樣保留；本階段沒有新 native build，也沒有重跑全部歷史 ROOT analyses。

## 2. 驗收欄位總表

| 使用者要求欄位 | 目前驗收結果 |
|---|---|
| 4F_COMPONENT | BLOCKED_PHASE11_PDF_OR_ALPHA_S；massive-bottom model 文字來源支持，未綁定相容 4F PDF member |
| 5F_COMPONENT | SOURCE_CONDITIONAL_NOT_READY；共同 0/1/2-parton family 尚無精確 PDF／alpha／matching／權重閉合 |
| MODEL_AND_MASS_IDENTITY | SOURCE_SUPPORTED，限凍結來源；sm/default：MB=4.7 GeV、MC=0；sm-no_b_mass：二者為 0 |
| PDF_COMPATIBILITY | BLOCKED；A 未找到可綁定的相容 4F member payload，B 也未選定新 family 的 member／hash |
| ALPHA_S_COMPATIBILITY | BLOCKED；PDF/ME/ISR/FSR、參考尺度、演化、threshold 與 backend 未共同凍結 |
| PHOTON_IR_DEFINITION | 方法／實作 SOURCE_SUPPORTED；production 數值、A bottom coverage、cut closure 與 detector mapping BLOCKED |
| MATCHING_INTERFACE | generic MLM／CKKW-L 來源存在；精確 family 未驗證；歷史 LO 的 FxFx 升格 INAPPLICABLE |
| MERGING_SCALE_STATUS | null／BLOCKED；沒有已選定或已驗證數值 |
| SELECTED_PILOT_COMPONENT | NONE_READY |
| EXACT_PROCESS_VALIDATION | PARSER_NOT_VALIDATED |
| GENERATOR_EXCLUSIVITY | UNVERIFIED；保留 NO_VALIDATED_MATCHING_PRESCRIPTION_YET |
| FAKE_CONTROL_OBSERVABILITY | 現有 nonisolated 分母缺失；未來 pre/post isolation 集合可保存的來源位置已確認 |
| FUTURE_DETECTOR_CARD | INACTIVE_SOURCE_SUPPORTED_WITH_LIMITS；全註解 diff；精確 overlap writer 仍 BLOCKED |
| CALIBRATED_FAKE_RATE | UNKNOWN；數值為 null，沒有由 MC origin 或合成方法替代 |
| PILOT_CONTRACT | INACTIVE_REVIEW_ONLY；完整缺件與停止條件已列出，不是執行命令 |
| PILOT_APPROVAL | NOT_AUTHORIZED |
| PILOT_EXECUTED | NO |
| PHYSICAL_TOTAL_BACKGROUND | BLOCKED |
| PHYSICAL_SIGNIFICANCE | NOT_EVALUATED |
| PHYSICAL_CLs | NOT_EVALUATED |
| PHYSICAL_KAPPA_INTERVAL | NOT_EVALUATED |
| TESTS | 172/172 Phase11 PASS；143/165/92 歷史回歸與五個歷史 validator PASS；物理／runtime gates 分列，詳見第 10 節 |
| HISTORICAL_PRESERVATION | 2874 檔精確 bytes PASS；不含「installed MG5 config raw freeze 已通過」的宣稱 |

## 3. Candidate A：massive-bottom 4F component

[A 報告](phase11a_4f_massive_bottom.md)與 [A02 來源收據](../analysis/phase11/evidence/phase11_model_pdf_audit_02.json)固定了有效 restriction 的差異。預設 `sm` 會讀取 `restrict_default.dat`：MB=4.7 GeV、MC=0；unrestricted UFO 的 MC=1.27 GeV 不是這個有效模型值。`sm-c_mass` 的 MC=1.55 GeV 是另一種限制，不能靜默套用到包含 massless incoming charm 的 p4 定義。

提案是 `p4 = g u u~ d d~ s s~ c c~`、`p4 p4 > b b~ a a QCD=2 QED=2`。p4 排除 incoming b，允許 c。`=` 的 amplitude order 語義是上限，不是精確等階；其直接強作用 Born 分量的 power counting 為 alpha_s² alpha_EM²，實際圖集／parser 尚未產生。這只是獨立 LO component 候選，不是 inclusive diphoton＋HF 總背景。

實際清查 10 個明確的 installed/configured PDF 搜尋範圍，沒有找到可綁定的相容 4F LO member payload。catalogue 的 CTEQ5F4、註解中的 backend、`pdfsets.index` 的 4F set 名稱與公開 .info 都不是已安裝 grid。沒有下載或安裝 member，也沒有用 CTEQ6L1 5F PDF 代替。精確 set/member/LHAID、info/grid bytes/hash、最高 active flavours、alpha_s reference scale/value、order/type/threshold 與實際 backend 必須保留 null／BLOCKED。

4F 不必然等於每個 scheme 欄位都必須寫 fixed：最高 active flavours=4、從不啟用 bottom 的 variable scheme 仍需精確 member 證據。公開 nf4 metadata 的 alpha reference scale 反例也說明，不能只因欄位名包含 MZ 就自動當成 Z 質量處的耦合。PDF evolution mass、模型 pole mass、alpha matching threshold 是不同定義，需逐項追蹤，不能混成同一個質量或從名字推定相容。

## 4. Candidate B：共同 5F diphoton＋0/1/2 partons

[B 報告](phase11b_5f_merged_family.md)與 [family／IR 收據](../analysis/phase11/evidence/phase11_family_ir_audit_03.json)涵蓋 MG5 3.5.16、Pythia 8.317 實際來源。p5/j5 都含 g、u/d/s/c/b 及其反粒子，ME restriction 為 `sm-no_b_mass`。0/1/2-parton 的嚴格等階文字提案分別使用 `QCD==0/1/2 QED==2`；舊的單一等號只表示上限。這個 tree family 沒有自動包含 loop-induced gg→aa，也沒有 photon fragmentation functions。

MLM generic interface 存在，但 `setMad`／LHE header 可覆寫 effective merge、qCut、nQmatch、clFact；必須保存最終生效值。此 j5 family 的 flavour scope 要涵蓋 b/c；nQmatch=4 會把 b 當成 heavy unmatched，不能宣稱 b 已被納入同一 matching。CKKW-L 的 photon core token 或 guess 路徑存在，也不代表精確 aa＋HF histories 已驗證；額外 native mergingWeight 必須與 generator/writer 的 combined weight 語義閉合，不能漏乘或重複作用。

沒有選定 MLM 或 CKKW-L prescription，沒有 xqcut/qCut/TMS 數值，沒有 highest-multiplicity、veto／accepted normalization 或 differential merging-rate closure。QCD/QED ISR/FSR、g→bb/cc、threshold、ME photon／shower photon 分工仍需共同凍結。將歷史 B01/B02/B03 額外加到此 family 不能視為互斥分割；不能用 FxFx 把原 LO 樣本升格成 NLO matched 樣本。

## 5. Direct-photon IR 與 acceptance

[C 報告](phase11c_photon_IR_definition.md)逐行追到 LO `cuts.f`、`setcuts.f` 與 banner：smooth-cone sum 只包含 `is_a_j`，不包含 `is_a_b`。maxjetflavor=4 時 b 另列 `is_a_b`，A 的 bottom 不在同一 smooth-cone sum；有限 MB 可調節特定 collinear limit，但不能自動證明 hybrid drab／smooth-cone acceptance 等同完整 QCD isolation。

positive ptgmin 還會將正的 pta、draj 設為 0；drab 不會因此停用。真正 diphoton mass 欄位是 `mmaa`。程式使用 abs(xn)，xn=0 沒有 r→0 的 smooth suppression。這些來源語義已具體確認，但不是選定 production default 的理由。

所有新 production isolation、pT／eta、photon-parton DeltaR、diphoton mass、jet/bottom cuts 與 hard scale 均未填入數值。未來數值必須有可追蹤的 acceptance 理由並標 `PROPOSED_NOT_PHYSICALLY_VALIDATED`，再以另外授權的敏感度檢查閉合。smooth cone 不單獨解決額外 QCD partons 的 soft/collinear 問題，也不等同 detector fixed cone；沒有 cut-independence 或 fragmentation completeness 的物理結論。

## 6. 選擇結果與具體未解參數

[D 選擇報告](phase11d_generator_selection.md)與 [相容矩陣](../analysis/phase11/evidence/final/phase11_compatibility_matrix.json)對每個候選逐列檢查八個必要領域：model/mass/flavour、installed PDF member、alpha/threshold、photon IR、generation cuts、hard scale、ME/PS interface、shower/weight identity。A/B 均只在第一項具備限定範圍的來源支持，其餘不能由 generic interface 或測試 PASS 跳過。

因此 selected pilot 為 **NONE_READY**。massive-4F「conditional review target」只是聚焦缺件的審查方向，不是已選組件或先行批准。精確缺件不是籠統的「還需更多測試」：A 缺可綁定的 4F member payload／alpha metadata 與 bottom photon-IR 定義；B 缺共同 PDF/alpha、exact history/interface、matching scale 與 weight closure；兩者都缺數值 cuts／scales／shower 與 future executable 身份。
## 7. 既有 B01–B03：來源身份、region migration 與 covariance

[E 詳細報告](phase11e_fake_control_observability.md)對完整 6000 筆 background native／origins persisted records 做一對一身份連接；其中 B01–B03 共 3000 個原始事件進入本次統計。source ordinal、LHE event SHA、HepMC event SHA、階段、權重、eligible native jet flavour 與 BTag bit0 逐一核對。沒有新 ROOT loop，也沒有把凍結的 ancestry 標籤重讀冒稱另一套完整 raw-truth classifier。

| 來源 | input／photon／jet／≥2-tag／final | 含 shower b／c birth 的事件 | 含 direct g→heavy 的事件 | 含 native b／c jet 的事件 |
|---|---:|---:|---:|---:|
| B01 | 1000／446／266／91／28 | 53／170 | 211 | 860／38 |
| B02 | 1000／378／241／7／1 | 36／211 | 240 | 13／902 |
| B03 | 1000／445／277／0／0 | 49／183 | 220 | 18／62 |

這些是**含該旗標的事件數**，不是 quark 總條數；origin 旗標重疊，不能相加。ME outgoing 分別仍是 bottom、charm、light/gluon。多母 hadron endpoint 的 unresolved 狀態保留，不能以無歧義 assignment 計數為零宣稱每條 hadron 都有唯一 partonic origin。

| 來源 | ≥2-tag low sideband | Higgs-like | high sideband | broad mgg window 外 |
|---|---:|---:|---:|---:|
| B01 | 8 | 4 | 16 | 63 |
| B02 | 1 | 0 | 0 | 6 |
| B03 | 0 | 0 | 0 | 0 |

mgg 邊界維持 105≤mgg<120、120≤mgg≤130、130<mgg≤160；所有 0/1/≥2-tag cells、outside 與 undefined 都保存。B01 的 91 個 double-tag events 有 63 個未通過 broad mgg，B02 的 7 個有 6 個未通過；B03 雖 final=0，仍有 native-heavy jets 和單標籤事件。每個 0/1000 proposal acceptance 保存 one-sided 95% upper 0.002991249545095296；這不是物理加權背景上限，也不是零背景證明。

實際輸出為 225 個 origin×stage、675 個 origin×tag×mass、3825 個 covariance 上三角元素。每來源 50 個向量共同使用原始 N=1000、全部失敗事件零貢獻；事件內多 jet／旗標不拆成獨立事件。以 `x_i=w_i I_A` 定義 source-sum covariance，採 `N/(N-1)[Σx_i y_i−Σx_iΣy_i/N]`，保留 nested cuts、shared flags 與互斥 cells 的相關性。跨來源的未知物理 covariance 為 null，不設為零；沒有 B01+B02+B03 物理加總。

[獨立有理數收據](../analysis/phase11/evidence/phase11_independent_event_covariance.json)以 Fraction＋整數事件 bitset、不匯入 production arithmetic，實際驗證全部 3825 個 covariance pairs，完成 3885 次數值比對、132 個非空互斥 region 的負 covariance 檢查，並與 Phase10 五階段計數／rates／variance 一致。此實際審查限定於已驗證等權重的歷史樣本；一般 signed-weight readiness 另以方法 fixture 測試，不能宣稱新 signed generator writer 已閉合。

### Incoming bottom 與 charm 的額外精確來源讀回

舊 combined initial-HF 不直接保存 incoming PDG，且混合 b/c。因此新增 source-only streaming LHE 審查，讀取原始 3000 events 的 exact bytes，連接原 input index、native/origins、原權重與身份。

| 來源 | incoming b | incoming c、無 b | 不含 incoming b/c | p4 initial-PDG domain 可容許 |
|---|---:|---:|---:|---:|
| B01 | 25 | 33 | 942 | 975 |
| B02 | 2 | 67 | 931 | 998 |
| B03 | 0 | 6 | 994 | 1000 |

B03 的 6 個 combined-HF 全是 charm；p4 允許 charm，不能把它們視為 incoming-bottom 違反。B01 incoming b 子集的 input/two-jets/double-tag/final 為 25/7/4/1，charm 子集為 33/8/3/1；B02 的 b/c final 均為 0；B03 的 c final 亦為 0。這些是原樣本診斷，不是新的物理接受率測量。

[初態審查收據](../analysis/phase11/evidence/initial_flavours_01/phase11_initial_flavour_audit.json)保存 3000 個 source-event identity／ordered incoming-PDG rows、400 個 stage rows、1395 個 covariance 上三角元素。975／998／1000 **只代表初態物種 domain**；歷史 massless-b model、5F PDF、alpha_s 與 matrix element 沒有改變，篩掉 incoming b 不會把原事件轉成 massive-b 4F prediction。B03 觀察到零 incoming b 也不能證明其 process definition 排除 b。

## 8. Photon fake controls 與 inactive detector 差異

來源鏈已精確定位：`ECal/eflowPhotons → PhotonEfficiency → PhotonIsolation → UniqueObjectFinder → TreeWriter:Photon`。isolation 對所有輸入 Candidate **先原位寫入六個 isolation 欄位，才拒絕候選**；Efficiency／Isolation 輸出沿用指標，TreeWriter 在最後執行。因此未來增加 PhotonEfficiency 的 branch 可保存隔離篩選前的集合成員、包括 isolation 失敗者及計算好的分量；這不是欄位計算前快照，也不是 pre-efficiency 的 truth photon/jet 分母。

[全註解 inactive diff](../analysis/phase11/config/inactive_detector_diff.txt)提出 PhotonPreIsolation、PhotonPostIsolation、ElectronPreIsolation、ElectronPostIsolation、JetPreOverlap 五條額外 branch，保留舊 selection。沒有套用卡、Tcl parser 或 Delphes run。現有固定 cone R=0.5、PTMin=0.5 GeV、PTRatioMax=0.12 的語義已核對，不改稱 smooth-cone 或官方 ATLAS isolation。

標準 Photon.Particles／Electron.Particle／Jet.Particles／Constituents 提供 native reference，但 TreeWriter 不保留原 Candidate UID 作精確跨 branch 身份，FillParticles 亦不等於完整任意 overlap graph。須另外審查可保存事件鍵、UID／parent edges、排序 ordinal、pre/post 成員與精確 overlap 決策的 writer，再做另行授權的有限 readback。此 gate 仍 BLOCKED_REQUIRES_REVIEWED_WRITER。

沒有新增 ATLAS tight／anti-tight shower-shape ID 或 conversion 分類。Candidate 內部欄位存在不表示 Photon branch 已保存或已校準；多存物件也不會提供 jet→photon／electron→photon 的真實資料 transfer factor。PHOTON_FAKE_RATE 維持 UNKNOWN，calibrated value=null。

## 9. 有界 pilot 合約、權重與資源

[F 審查](phase11f_bounded_pilot_review.md)及 [inactive contract](../analysis/phase11/config/bounded_pilot_contract.json)列出 exact executable revision、MG5／model、Pythia、process、PDF/member/flavour、alpha/reference/threshold、photon IR、cuts/scales、shower、weights／normalization、source IDs、integration diagnostics、accepted/rejected counters、matching、preflight hashes、獨立驗證、停止條件及 fresh output 需求。沒有完整組件的欄位維持 null／BLOCKED；沒有可以跳過 review 的 dispatcher 或 approval flag。

未來須保存 LHE IDWTUP／XWGTUP／SCALUP、signed sumW/sumW2、native／merging weights、每個 multiplicity 的全部接受／拒絕／veto／trial 計數、BR 恰作用一次的證據、grid／survey/refine／seed／PDF／scale 與 integration error。完成 run 不自動建立收斂；候選截斷、counter 無法量測、資源上限或科學 gate 失敗即停止，不補跑失敗 replica、不擴張 scope。

| 未來示例資源 | Phase10 illustrative value | 目前批准 |
|---|---:|---|
| threads | 2 | null；未授權 |
| walltime | 7200 s | null；未授權 |
| RAM | 4 GiB | null；enforcement 未證明 |
| disk | 2 GiB | null；未授權 |
| total new hard events | 1000 | null；未授權 |
| scan points | 3 | null；未授權 |
| ME evaluations | 1000000 | null；native counter enforcement 未證明 |
| integration cycles | 20 | null；未授權 |
| event trials | 100000 | null；未授權 |
| aggregate CPU | null | 尚未凍結，不由 threads×wall 推定批准 |

本次 source／existing-data 計算另以單 job／worker、14400 s aggregate CPU／job-wall、2 GiB 額外 build/results 的保守監控契約執行。這與未來物理 pilot 或 Phase7I 預算無關。process-group CPU/wall/disk 與 TERM/KILL 監控不等於硬性 job RAM containment，也不保證 native ME/trial/cycle caps；存在 cgroup controller 不代表具備 delegated enforcement。

`parser_process_review_request.json` 只是另行待審的狹窄 model/alias/process-code 請求，不含 launch、數值 ME、積分或 event 命令；其 300s CPU/wall 等示例與 executable revision 亦未批准。本階段沒有執行該請求。

## 10. 實際測試與獨立性限制

最終修正後的 Phase11 方法／負測試為 **172/172 PASS**。受控 job wall 約 0.255 s，unittest 本身約 0.060 s；這兩種時計不混用。[最終測試執行收據](../analysis/phase11/evidence/phase11_methods_drift_final_execution.json)與 [最後 raw-source gate 收據](../analysis/phase11/evidence/final_02/phase11_pilot_readiness.json)綁定實際結果；執行來源的 before/after hashes 一致。gate 命令正常完成並正確輸出 BLOCKED，不代表其中失敗的 source identity 已轉為 PASS。

| 實際檢查 | 結果與範圍 |
|---|---|
| Phase11 | 172 source/method/schema/unit/negative tests PASS；不是 MG5 parser 或 physical pilot |
| Phase10 regression | 143 tests PASS；既有來源未變動 |
| Phase9 regression | 165 tests PASS；既有來源未變動 |
| Phase8 regression | 92 tests PASS；既有來源未變動 |
| 五個歷史 validator | signal、new backgrounds、MG5 library、Pythia、Delphes evidence validator 實際 exit 0；沒有新 production |
| 既有事件 readback | D02 6000 joins／3000 HF，零 ROOT loop |
| 獨立 covariance | 3825 pairs、3885 comparisons、132 negative disjoint cells，實際 PASS |
| 精確 incoming PDG | 原始 LHE 3000 筆，actual PASS；零新 events |
| 獨立自動審查 | 68 個負向 probe 有機器收據；屬 synthetic/method，不是外部人工 approval |
| Drift gate 獨立修正審查 | 另有 42 個 method checks 通過，核對 actual 60 records／56 paths／1 mismatch；不解除 runtime drift gate |
| GITHUB_CI | PASS：exact source revision 的 push／PR CI；只檢查來源／方法與 bounded evidence，final delivery closure另記 |

測試覆蓋 model restrictions、4F/5F／PDF／alpha metadata、order operators、LO photon IR、matching flavour/weight、未審 merging scale、混合組件拒絕、missing fake controls、null/zero、signed cancellation、resource 未批准、inactive 卡、來源身份與 zero-production gate。最終 gate 另逐 byte 重讀 60 個 raw identity records、56 個 unique paths，只發現一個 mismatch：installed MG5 configuration。

[Drift gate 獨立審查](../analysis/phase11/evidence/final_02/phase11_drift_gate_peer_review.json)屬方法／來源 gate 的自動審查，沒有外部人類物理批准；42 個 checks 通過不代表已改寫或解除 raw config mismatch。

A01 broken symlink、family source-witness 字串問題、D01 photon stage 簡化錯誤的原始失敗紀錄均保留；修正只發生在新審查程式。沒有修復／重寫歷史樣本或覆蓋先前結果。較早的 161-test 收據由最終 172-test 收據接續，不能把早期結果當成最後版本證明。

## 11. 歷史保全 PASS 與 installed config drift：不同的 gate

[歷史保全收據](../analysis/phase11/evidence/final_02/phase11_input_preservation.json)顯示 **2874 個檔案、2,611,429,240 bytes** 與任務前的逐檔 SHA-256 一致。範圍是原有 970 個受監測 Phase6–9 路徑、全部舊 Phase10 results／receipts／remote snapshots，以及舊 Phase10 checkout 的全部 tracked files。所有被納入的歷史 figures 版本均保留。

Phase7I／8／9／10 的舊 source HEAD／index 亦有精確 identity 控制；不宣稱遞迴驗證每個 stopped workspace 的所有檔案。PR24–27 在保全讀回時仍 OPEN/DRAFT、未合併、head 保持各自原值。後續新 PR 交付仍須保留這些邊界。

**上述 PASS 不包含 installed runtime configuration freeze。** [獨立 drift 收據](../analysis/phase11/evidence/final_02/phase11_runtime_configuration_drift.json)記錄下列三個 raw identities：

| bytes | SHA-256 | 身份證據 |
|---:|---|---|
| 9212 | `83d48923f215d20565931e8e0eb6ee986b34658d0bbe6f2e7a75e0400b4d7f85` | A02 記錄之原身份；後續由記憶體逆轉換重建並確認 exact hash；不是原磁碟備份 |
| 9239 | `9132f5ddcab8eb45ee00830d3ed9b7582bda67058180288d3f93222a96f74506` | 中間觀察身份；記憶體逆轉換 exact hash 確認；不是原磁碟備份 |
| 9266 | `82a6d1943d0acd139704910dfd0510ee2bd86d06f94a410b5f28e68a45bc3f5a` | 本機觀察 bytes 副本 |

差異是 compiler／auto_update 設定後方的註解 padding 與 space-only lines。root 在記憶體進行逆轉換，重建 bytes 命中兩個先前完整 SHA-256；三者有效 fortran/cpp compiler、auto_update=0、mg5_path 相同。這支持「所觀察有效設定未變」的有限結論，**不能正規化後把 raw SHA mismatch 判為成功**，也不能宣稱找到了不存在的原始磁碟備份。

`caller=UNKNOWN`。已讀取的 serializer 原始碼只是可能的行為機制，不是程序歸因；instantaneous process snapshot 不是整段主機執行史。新 incoming audit 的 import chain 為 repository 的標準函式庫 LHE parser，未發現 installed madgraph import 或 config 寫入入口；這仍不足以確定實際修改者。本次審查沒有修改／還原 installed file，沒有為通過 gate 編輯 receipt，也沒有 bypass raw identity。

故最終 `source_integrity_status=BLOCKED_EXTERNAL_RUNTIME_CONFIGURATION_DRIFT`。Phase11 不可宣稱全部 installed sources 原樣凍結；未來必須另外審查、重新綁定要使用的確切 runtime bytes／revision，仍不得自動啟動 parser 或物理 pilot。
## 12. 科學、來源與交付 gates

### GATES_PASS

- 有效模型 restriction／mass／flavour 與 order operator 的靜態來源語義，均有版本、行號與 SHA witness。
- 明確限定搜尋範圍的 PDF 清查；沒有把 catalogue 或公開 metadata 冒充已安裝 member。
- LO photon isolation 的 is_a_j／is_a_b、ptgmin override、drab、mmaa 語義；未輸入實體 cross section。
- Delphes collection sequence／原位 isolation 更新位置，以及 inactive diff 的限定可保存內容。
- 凍結 persisted records 的 6000 identity joins、3000 HF event-unit migration，全部 covariance 的獨立有理數比對。
- 原始 LHE 3000 筆 incoming b/c 分拆，保留 source-event IDs、原始 N 與權重；未重標成 4F sample。
- 最終 172 個 Phase11 方法／負測試，143／165／92 個既有回歸及五個歷史 validator。
- 受監測的 2874 個歷史檔案 exact bytes 保存；舊 HEAD／index 與保全時的 PR24–27 狀態保持。
- 任務的已登錄來源／既有資料 jobs 沒有 generator dispatcher 或新物理 production。

### GATES_FAIL

- **INSTALLED_MG5_CONFIGURATION_RAW_FREEZE**：A02 的 9212-byte identity 與目前 9266-byte identity 不同；最後的精確 raw comparison 有一個 mismatch。這是已觀察到的身份比較失敗，並未歸因為本任務改寫；較高層狀態為 BLOCKED_EXTERNAL_RUNTIME_CONFIGURATION_DRIFT。

### GATES_BLOCKED

- A：相容 4F member payload／grid/info/hash／alpha/reference/threshold/backend 綁定。
- A：massive-bottom 與 LO smooth-cone／drab 的明確 target observable；A/B 的 generation cuts、scales、shower 設定。
- B：共同 0/1/2 family 的精確 parser/process、matching/history／flavour、最高 multiplicity、native merging weight／writer normalization。
- 所有未審 numerical merging scale、cut sensitivity／fragmentation／detector acceptance closure。
- installed runtime raw source freeze；不能以 effective settings 相同解除。
- 精確 Candidate overlap provenance writer 與相容 fake-control 分母／校準。
- future executable revision、獨立人類審核、明確物理授權、approved ceilings、hard RAM／native counter enforcement、fresh execution workspace。
- MATCHED_SIGNAL_NORMALIZATION=BLOCKED_PHASE7I；PHYSICAL_TOTAL_BACKGROUND=BLOCKED。
- Source payload 的 GitHub CI／125 remote blobs 已通過；report-only HEAD 的最終 closure 不提升任何物理 gate。

### GATES_UNKNOWN

- PHOTON_FAKE_RATE；calibrated jet/electron→photon transfer value 為 null。
- HEAVY_FLAVOUR_GENERATOR_EXCLUSIVITY=UNVERIFIED；沒有已驗證 matching prescription。
- installed configuration drift 的 caller；無法由目前 snapshot 推定整段主機歷史。
- 未測的真實 cut/matching convergence、native generator/shower writer closure、未知物理 normalization 與跨來源 covariance。

PHYSICAL_SIGNIFICANCE、PHYSICAL_CLs、PHYSICAL_KAPPA_INTERVAL 都是 **NOT_EVALUATED**，不是零、失敗的 fit 或上限結果。source/method PASS 沒有自動提升這些狀態。

## 13. 實際計數與未執行事項

| 欄位 | 本任務已登錄 jobs |
|---|---:|
| NEW_ME_CALLS | 0 |
| NEW_INTEGRALS | 0 |
| NEW_HARD_EVENTS | 0 |
| NEW_PYTHIA_EVENTS | 0 |
| NEW_DELPHES_EVENTS | 0 |
| PILOT_EXECUTED | NO |
| 新 ROOT loops | 0 |
| 新 PDF／PNG figures | 0 |

沒有跑 MG5 parser、launch 或 process generation；沒有新積分與 hard events，沒有 Pythia／Delphes production，沒有 Phase7I build／restart，沒有 likelihood、CLs、κ interval 或物理 B01+B02+B03 總和。合成 fixtures 與既有 raw events 的讀回有各自 evidence class，沒有合成數字進入物理結果。對 installed config drift 不作整台主機零執行的推論。

## 14. 檔案、可重現操作與 GitHub 交付驗收

[README](../analysis/phase11/README_ZH_TW.md)提供 source-only 與既有資料命令；輸出必須是新的不存在路徑，不指向任何 Phase6–10 目錄。這些 CLI 不執行 MG5／Pythia／Delphes；不能用未批准旗標把 inactive card 轉成 production。

| 交付類別 | 內容 |
|---|---|
| analysis/phase11 | 來源審查 scripts、validated schemas/policies、candidate matrix、全註解 inactive cards/detector diff、方法／負測試、繁體中文 README |
| reports A–F | [4F](phase11a_4f_massive_bottom.md)、[5F](phase11b_5f_merged_family.md)、[IR](phase11c_photon_IR_definition.md)、[選擇](phase11d_generator_selection.md)、[fake controls／events](phase11e_fake_control_observability.md)、[pilot contract](phase11f_bounded_pilot_review.md) |
| metadata | phase11_candidate_configurations.json、phase11_scientific_source_identity.json、phase11_quality_gates.json；最終 Git source binding 由交付階段填入 |
| bounded evidence | model/PDF 與 family/IR inventories、source witnesses、event-unit counts/covariance、incoming PDGs、獨立驗證、保全、drift、受控執行收據；不包含新 physical samples |
| 本機最終 receipt | FINAL_REPORT.json：於最終 commit／PR／CI／遠端查核後寫入真實交付身份 |

**NEW_SOURCE_REVISION=`3652fea6f2dc8bce255cbe8cce49fe8241ba27d4`；DRAFT_PR_URL=[PR28](https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1/pull/28)。** GitHub [push CI](https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1/actions/runs/39227435025) 與 [PR CI](https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1/actions/runs/39227487824) 均成功。REMOTE_BLOB_VERIFICATION=PASS_EXACT_IMMUTABLE_REMOTE_BLOBS：125檔、2,939,322bytes，與該 source commit 的 Git bytes/SHA256 完全相同。執行來源與 report-only delivery HEAD 分列；後者實際 CI 與全部 blobs 最終核對在本機 FINAL_REPORT.json 閉合。

GitHub 只發布 source、tests、reports 與有界 numerical evidence。每次 push 前都要檢查 staged files 及所有 outgoing commits，包含中間版本；不帶未批准 PDF／PNG，不動舊 PR24–27、不 merge、不 force-push。既有 Phase9 圖件的狀態仍為 **AWAITING_USER_APPROVAL**，不因歷史發布或測試通過而取得新版本批准。本次沒有新圖可供自動發布。

## 15. 最終結論與下一個具體步驟

**FINAL_VERDICT：BLOCKED_PHASE11_NO_VALIDATED_COMPONENT。**

此結果已減少實際設定不確定性：預設 sm 的有效 MC／MB、PDF payload 與 catalogue 的差異、alpha reference-scale 語意、amplitude 上限與精確等階、LO bottom isolation coverage、MLM header/flavour 與 CKKW-L weight、pre-isolation 持久化機制，以及 incoming b/c 的精確歷史數目都已具體確認。仍沒有足以被凍結並授權的完整第一組件，故不製造 selected scheme。

**NEXT_RECOMMENDED_STEP：** 保留已完成的 Draft source/evidence 交付與精確遠端驗證，同時維持 runtime drift 為未解 gate。未來如要聚焦 massive-4F review target，須先取得另行允許的精確相容 4F member payload 與 metadata，定義 alpha/reference/threshold、bottom photon-IR／cuts／scales／shower，並重新審查確切 runtime bytes 與 executable revision。只有缺件有了具體證據，才提出狹窄 parser/process review；任何真正 ME、積分或新事件仍須另行明確人類授權。不得從本次 source-only 任務、先前 Phase7I 授權或 illustrative resource envelope 推定物理 pilot 已獲批准。
