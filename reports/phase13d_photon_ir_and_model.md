# Phase13D：massive-bottom 模型、process bounds 與 photon IR 前置審查

本分工只唯讀核對既有 MG5 3.5.16 的九個模型／parser／LO-template source，以及新的 inactive process 與 candidate JSON；**沒有匯入或啟動 MG5，也沒有 actual parser、diagram enumeration、ME 或物理 generation**。source 可確認 sm/default 的 MASS restriction 為 MB=4.7 GeV、MC=0；process 中 QCD=2／QED=2 是 amplitude-order 上界。maxjetflavor=4 時，Frixione hadronic sum 的 inspected branch 不含分類為 is_a_b 的 bottom。這些來源事實不等於已驗證的 diagram set、4F prediction 或完整 photon IR prescription。

## 模型來源與 restriction 身分

審查的原始來源根目錄是 `/home/btu/.local/share/atlas-hh-phase6a/mg5-release-v3.5.16`。本 auditor 只讀指定文字；不讀取或改寫 installed input/mg5_configuration.txt，不 import UFO module，也不改變 Phase7I–12 checkout。所列 source 必須與下列 raw bytes／SHA 完全相同；不做 whitespace normalization。

| 精確來源 | bytes | SHA-256 |
|---|---:|---|
| models/sm/restrict_default.dat | 1437 | cc9e735d3dea306b31dcf3ef179719fceeefb505406bd163308324dc9aebda53 |
| models/sm/parameters.py | 15693 | 2e4046c3566f1fb62fad92ffa705eef66a0124cc2a1cf4cc0d0ff2dc7f94c8fc |
| models/sm/particles.py | 10444 | 5a18af7aadba847f6b70749dcd2a787f95f9075c4c8de4406b2138314defe414 |
| models/sm/coupling_orders.py | 443 | c89fc6f38d118a50a1e562da8653a2ccc96a9e00be22696bf5fb771a4df313b4 |
| models/import_ufo.py | 127324 | d030835ea14a700ab40c29e4e2fb73df4d7f4fd846cf4ba22db3589a14549a38 |
| madgraph/interface/madgraph_interface.py | 458046 | be96f305974bfee0108089af04d12dac55fccbdcd7791787fc8976ce8f930bc3 |
| Template/LO/SubProcesses/cuts.f | 55278 | c077cc390dc052a8526ddb187c98005e08bab7e5d999c8c879b66a1500b65c2c |
| Template/LO/SubProcesses/setcuts.f | 35393 | f0e3e5e3ad3f5599fa56aa7baef614112e383ee51701caa38d16c977185cab18 |
| madgraph/various/banner.py | 279713 | 9877e00f80da4ef8a23d6a11377238e5b31c91c346b2aa73307ab52f64d9cc2a |

`models/import_ufo.py` 第 225–230 行在正常 default restriction 情形選用 restrict_default.dat。該 card 的 MASS block 第 17–18 行將 charm 設為 0、bottom 設為 4.7。另一方面 raw parameters.py 第 133–155 行的 UFO defaults 是 MC=1.27、MB=4.7；因此不能只讀 parameters.py 就宣稱 default restricted MC=1.27，也不能說本階段已經在實際 import 中觀察 restriction 生效。particles.py 的 c／b mass reference 分別是 Param.MC／Param.MB，純 AST 審查不執行參數或 coupling expression。

結論為 **EXACT_SOURCE_DEFAULT_RESTRICTION_REVIEWED；ACTUAL_MODEL_IMPORT=NOT_EXECUTED**。這裡 MB／MC 是 ME 模型 restriction，與 PDF evolution masses／thresholds 是不同定義；不要求字面相等，也不以差異已被列出就推論 ME／PDF／ISR／FSR 的一致性已成立。PDF backend 與 alpha_s 綁定的獨立結論見 [Phase13B](phase13b_pdf_backend_binding.md)、[Phase13C](phase13c_alpha_s_semantics.md)。

## Process 文字與真正允許的未來 scope

[model_process_ir.json](../analysis/phase13/config/model_process_ir.json)僅提出以下精確三命令：

```text
import model sm
define p4 = g u u~ d d~ s s~ c c~
generate p4 p4 > b b~ a a QCD=2 QED=2
```

[inactive 文字檔](../analysis/phase13/config/process.inactive.txt)每一行都保持註解，並非可直接餵給 MG5 的 command card。p4 不含 b／反 b，包含 massless restricted charm；此 alias 與 PDF flavours、maxjetflavor cut category 各有不同角色，不得混為同一個「4F 已驗證」標記。

madgraph_interface.py 第 4847–4851 行將 amplitude-order 的 `=` 與 `<=` 放入相同 bounds 分支；`==` 是另一種 constraint。coupling_orders.py 定義 QCD／QED order，但 expansion_order=99 不是本 proposed process 的 diagram count。故這個 process 是 **QCD≤2、QED≤2 的 source-level syntax proposal**，不是已經核對「exact QCD²QED² 唯一 diagram set」或干涉結構。process syntax、diagram identities／counts、cross section 都尚未由 actual MG5 確認。

`generate` 並不只是字串拆解：do_generate 第 4712–4721 行呼叫 do_add；standard tree 分支第 3269–3277 行建立 symbolic diagram_generation.MultiProcess／amplitude list。因此 future parser contract 明確 **包含 in-memory symbolic process／diagram enumeration**，同時 **排除 output process、code generation／compile、numerical check process、numerical ME、integration、launch、events、Pythia、Delphes 與 Stage A**。這是未來請求的範圍，不是本階段執行證據。exact-source human approval、isolated runtime、write confinement 及 resources 由 [Phase13E](phase13e_parser_execution_contract.md)單獨約束；本分工沒有建立 HumanReview 或消耗舊 BUILD_ONLY 授權。

## Inspected LO-template photon IR 分支

1. `setcuts.f` 第 216–224 行以 PDG 與 maxjetflavor 分類，並非以實際 mass 判斷。maxjetflavor=4 時，±1…±4 及 gluon 為 is_a_j，±5 為 is_a_b。將 maxjetflavor 改成 5 會改變這個 category；此 source counterexample 只用來解釋差異，沒有把 5F 值作為本候選。
2. `cuts.f` 第 1090 行在 ptgmin≠0 時進入 photon isolation 分支；第 1098–1106 行填充 hadronic pQCD array 時只選 is_a_j，沒有「或 is_a_b」。故在本 proposed LO b b~ a a final state，兩個 coloured final legs 都在 is_a_b，source-derived hadronic array entry count=0；這是模板邏輯推導，不是實際執行／acceptance measurement。
3. 第 1156–1166 行按 photon–parton 距離排序，在 R0gamma 內累加 eligible parton pT，要求各子錐滿足 E_T,sum(r)≤χ(r)。第 1341–1353 行的 χ=epsgamma·pTγ·[(1−cos r)/(1−cos R0)]^abs(xn)。正 exponent 使小錐上界趨零，但只對被放入 array 的對象有效；不能據此宣稱 massive b 已受到 smooth-cone hadronic isolation。
4. 距離 helper 第 1287–1312 行使用 pseudorapidity difference 與 azimuth difference；這是 parton-level template 的度量與數值 branch。若 isoEM=True，第 1119–1134 行另外收集 photons／charged leptons 作 EM isolation，不會因此補入 massive b。
5. `banner.py` 第 4244–4251 行在 ptgmin>0 時把正 pta 與正 draj 置零。`setcuts.f` 第 299 行 photon et minimum 為 max(pta,ptgmin)。不能把提交的 card pta／draj 與 effective card 當成相同；本候選明列 pta=draj=0，避免假稱它們仍是另加的正 cuts。
6. `setcuts.f` 第 350–357 行區分 photon–is_a_j 的 draj 與 photon–is_a_b 的 drab。上述 inspected ptgmin normalization branch 不把 drab 置零；因此 maxjetflavor=4 下，drab 是另外必須審查的 b–photon separation。第 393 行把 mmaa 轉成 photon-pair s_min；它是獨立 invariant-mass cut，不能由 Frixione 開啟而默默取消。

[S. Frixione 的原始論文](https://arxiv.org/abs/hep-ph/9801442)提出 smooth isolation 來定義 direct isolated photons 並處理 fragmentation 依賴；本報告以實際 installed template 的 eligible-object 分支約束其覆蓋範圍，不把論文的一般性質無條件套到 excluded bottom。這也不是 ATLAS reconstructed-photon fixed-cone isolation，沒有 detector calibration、fragmentation／fake model 或官方 systematic 等價聲明。

## 未使用的候選 generation cuts

以下每個已選 numerical／boolean 值均為 **PROPOSED_NOT_PHYSICALLY_VALIDATED**。它們只保存可審查提案，**沒有產生 active run card、沒有傳給 MG5，也不是完整可執行物理設定**。不是從 historical 5F card 默用 default。每欄的詳細 rationale／required_acceptance_evidence 保存在 JSON，任何 silent 替值都被 source-engineering validator 拒絕。

| 欄位 | 候選值 | 證據等級 | 提案理由／仍需的證據 |
|---|---:|---|---|
| maxjetflavor | 4 | PROPOSED_NOT_PHYSICALLY_VALIDATED | 明列 b 在 is_a_b；需逐一核對 future generated cut source、ME／PDF scheme，不能單靠此值證明 physical 4F。 |
| ptgmin / GeV | 20 | PROPOSED_NOT_PHYSICALLY_VALIDATED | 有限正 photon soft 門檻的探索值；需要低／高門檻 acceptance 與 efficiency 穩定性。 |
| r0gamma | 0.4 | PROPOSED_NOT_PHYSICALLY_VALIDATED | parton smooth-cone 探索半徑；需 cone 變動與 detector migration 審查。 |
| xn | 1 | PROPOSED_NOT_PHYSICALLY_VALIDATED | 正 exponent 的 small-cone limit；不修補 excluded b sum。 |
| epsgamma | 1 | PROPOSED_NOT_PHYSICALLY_VALIDATED | cone-edge fraction 探索值；需獨立 isolation sensitivity，非校準。 |
| isoem | false | PROPOSED_NOT_PHYSICALLY_VALIDATED | 明列停用額外 EM smooth cone，以 draa 定義 photon-pair separation；需比較 acceptance。 |
| pta / GeV | 0 | PROPOSED_NOT_PHYSICALLY_VALIDATED | 與 positive-ptgmin effective normalization 一致；實際門檻由 ptgmin 提案承擔。 |
| draj | 0 | PROPOSED_NOT_PHYSICALLY_VALIDATED | 與 normalization 一致；不拿 light-parton draj 代替 b separation。 |
| drab | 0.4 | PROPOSED_NOT_PHYSICALLY_VALIDATED | 明列 massive-b/photon separation；需其 radiation／acceptance sensitivity。 |
| draa | 0.4 | PROPOSED_NOT_PHYSICALLY_VALIDATED | 明列 photon-pair geometry，避免 isoem/default 混用；需 overlap／migration 審查。 |
| mmaa | null | UNRESOLVED_BLOCKS_PHYSICAL_EVALUATION | 先定 signal/control mgg 範圍與 resolution migration，再審查正值或停用值；沒有默填 0。 |
| ptb | null | UNRESOLVED_BLOCKS_PHYSICAL_EVALUATION | 先定 b-jet fiducial region 與 b→jet／低 pT acceptance；沒有默用 ptj／ptb。 |
| etab | null | UNRESOLVED_BLOCKS_PHYSICAL_EVALUATION | 需 jet eta、forward migration 與 generation phase-space 外延。 |
| etaa | null | UNRESOLVED_BLOCKS_PHYSICAL_EVALUATION | 需 photon acceptance、crack／overlap 與 migration；不等同 detector cut。 |

ickkw、xqcut、kt_durham、dynamical_scale_choice、mu_R_definition、mu_F_definition 均保持 null／UNRESOLVED_BLOCKS_PHYSICAL_EVALUATION，要求另行審查 LO／matching scope 與接受測試。即使未來決定 pure LO unmatched，也必須明列經審查的停用設定；本階段不替未選值填 0 或套 global defaults。PDF 4F 的 standalone PASS 亦不會補足這些欄位。

因此 **PHOTON_IR_READINESS=SOURCE_BRANCHES_CHARACTERIZED; CANDIDATE_ONLY; PHYSICAL_EVALUATION_BLOCKED**。這個 physical block 不代表必須先做新物理積分才能提出獨立的 syntax／diagram-only review，但不允許 parser 通過後自動 launch。

## 靜態 auditor 與回歸介面

[source/model_ir.py](../analysis/phase13/source/model_ir.py)只使用 stdlib 文字、SHA 與 AST；不 import 或 dispatch 任何 MG5／model／LHAPDF。所有九個 selected sources 檢查 raw bytes／SHA／resolved regular paths，保留 before／after；18 個 bounded source witnesses 保存 exact line numbers。pure static PDG-category reconstruction 只解釋來源分支，並非執行 Fortran cuts 或重建 event observables。

[scripts/audit_model_ir.py](../analysis/phase13/scripts/audit_model_ir.py)要求 fresh task-local JSON、regular resolved output parent，保留 CLI／module／JSON／inactive text 的 before／after identities。它不建立 output process，不建立 run card，不寫 installed runtime。離線 tests 涵蓋 MB／MC、raw UFO versus restriction、三命令 exactness、order bounds、無 approval／codegen、cut evidence labels、unknown defaults、hash drift、symlink／traversal 拒絕，以及 AST 不執行模型 fixture。

[model_ir_01 controlled execution](../analysis/phase13/evidence/model_ir_01_execution.json)已實際完成：exit=0、wall=0.293359154 s、CPU=0.047330 s，resource_failure=null。[實際 source-audit JSON](../analysis/phase13/evidence/model_photon_ir_review.json)記錄 PASS_MODEL_AND_PHOTON_IR_SOURCE_AUDIT_WITH_PHYSICAL_CUTS_BLOCKED；九個外部 source before=after、四個 audit input before=after、18 個 witnesses、restricted MC0／MB4.7、actual_import_status=NOT_EXECUTED。這是實際執行 static auditor，不是啟動 MG5。

[第一次 controlled unit log](../analysis/phase13/evidence/phase13_unit_01.log)中，model/IR 的 **37 個離線方法皆為 ok**。該完整跨模組 suite 的 186 項結果同時包含 2 failures／1 error，並未整體通過；publication expected-message 與 parser fixture 的後續修正及最新完整 suite 判定，以總驗收報告為準。不能把 model 子集通過當成全專案綠燈。另一 agent 唯讀檢查這組 source/config/tests 未見提升物理結論的 material gap，但它未執行 CLI／Fortran／MG5，也不是外部人工核准。

future root contract 另含安全的 `quit` terminator，意義是三項 model／alias／process semantic commands 加上終止命令，不是新增第四項物理操作；仍沒有本階段 parser 執行。Synthetic source-engineering tests 無論通過多少，都不是 MG5 parser／diagram enumeration 或物理 validation。

## 最終 source-method 驗收補記

首次 suite 的 fixture 問題已修正，原始失敗 log 保留。[phase13_unit_02](../analysis/phase13/evidence/phase13_unit_02.log)實際 **188 tests PASS**（unittest 0.786 s；controlled monitor wall=0.899009905 s、exit=0）；[Phase12 offline regression](../analysis/phase13/evidence/phase12_regression_01.log) **167 PASS**、[Phase11 offline regression](../analysis/phase13/evidence/phase11_regression_01.log) **172 PASS**，合計 **527 offline tests PASS**。這不重跑舊資料分析，也不是 parser／ME／物理執行證據。

[最終獨立 parser-contract peer review](../analysis/phase13/evidence/parser_contract_peer_review.json)完成 46 個 source／AST／identity 檢查，確認目前 source 的 FULL_LAUNCH_ENVELOPE_IMPLEMENTED=False 會在 launcher authorization 與 child main 的任何 activation／MG5 dispatch 前阻擋；prepared package eligibility／READY label 亦與此 constant 及 full-envelope receipt 相與。因此本次 child fixture 成功不能提升為完整 launch job 已受限：supervisor CPU／RAM、total-launch wall 與 parent pre/postflight disk boundary 仍未證明，**full parser dispatch 保持 BLOCKED_PHASE13_RESOURCE_ENFORCEMENT**。FIFO／PID／token 只稱 handoff consistency，並非 human identity proof。peer review 沒有 import 或執行受審程式、沒有建立人工授權，也沒有新的 MG5／ME／integral／event 呼叫。

後續只允許在新的明確任務中補齊完整 job containment、負面 tests 與 exact source review；目前即使另外提供 approval file 也不能用這份 source 啟動 parser。model／photon IR source 仍保留本報告上述 static PASS 與 physical cuts BLOCKED 的界線。
