# Phase13 完整驗收報告

PROJECT: ATLAS_HH_BBGG_PUBLIC_V1  
TASK: PHASE13_ISOLATED_MG5_RUNTIME_AND_PARSER_READINESS_V1  
BASE_REVISION: d95ca4c98352f460af955a1bad5372f63cfcee4a

**FINAL_VERDICT: BLOCKED_PHASE13_RESOURCE_ENFORCEMENT**

已完成獨立 runtime、來源與模型/PDF 稽核、13 個實際無害 kernel fixtures、527 個 offline unit regressions 及2個實際 CLI 拒絕案例。完整 supervisor/job 的資源限制仍未證明，因此目前不接受正向 parser 派發。這不是 MG5 parser 或物理產出的驗收通過。

NEW_SOURCE_REVISION: PENDING_SOURCE_COMMIT  
DRAFT_PR_URL: PENDING_ONE_STACKED_DRAFT_ON_PR29  
GITHUB_CI: PENDING_NEW_DRAFT_PR  
SOURCE_HASH_CLOSURE: SOURCE_MANIFEST_PREPARED; FINAL_COMMIT_AND_REMOTE_PENDING

| 驗收欄位 | 結果與範圍 |
|---|---|
| RUNTIME_ISOLATION | 新 ext4 checkout、實際私有來源複本；4733 regular files／133901130 bytes；45 internal symlinks，其中2個原 broken internal links 保留；無共享 inode。 |
| RUNTIME_RAW_IDENTITY | 原／複本 config 均9302 bytes，SHA256 e4567fd50d47a317407eb10cca76387053cdf06631949773296314702f77dca1。whole-tree content manifest d1d4976a39c5fbd08e3a7fa4db7e42c525c40c84f7be701c1dead3f81afb9e61。 |
| ORIGINAL_RUNTIME_PRESERVATION | 全 tree byte/layout/stat identities 前後相同。mg5_path-only9305-byte提案6451b6a7ebdc7bb396b3608a73ba7e7f4f01d4d0584f9acab6ff0d7a6666172f另存且未啟用。writer仍UNKNOWN，Phase11舊gate仍BLOCKED。 |
| PDF_MEMBER | NNPDF30_lo_as_0130_nf_4／member0／LHAPDF ID263400／DataVersion2。沿用P12bytes，無新下載。 |
| PDF_SOURCE_IDENTITY | info SHA85f3b2626de0896f45f5cfef53d90abd8d7b5ae784800b18d652e3f817431162；member SHAe3055763f3a3154c2a2c6811d35e1f319a0bb38ff1c645c8db5cdc8bd210005e。既有native04、10dependencies、11MG5 source/isolatedcopy與5header/tool identities核對。 |
| PDF_BACKEND | 現有LHAPDF6.5.6；MG5>=6.2分支pdf_lhapdf62.cc；make variable lhapdf決定alpha delegate；static libLHAPDF.a缺件阻擋未來數值link。P12standalone native證據保留，本次native PDF calls=0。 |
| PDF_ALPHA_S_REFERENCE | Qref4.1799998，declared.2544023564420006，native.254403024565842；rel2.626248635282933e-6>1e-6，strict diagnostic仍FALSE。ipol非knot插值／metadata參考不等同exact-equality保證；外部accuracy bound UNKNOWN。alpha(91.1876)=.12470053368074485是P12量測，不從set name填.130。MG5 wrapper用91.188，未量測該值。ME/PDF/ISR/FSR不得混為一談。 |
| PDF_MG5_BINDING_STATUS | UNVERIFIED_NOT_EXECUTED；symbolic parser無數值PDF依賴，不代表數值backend可用。 |
| MODEL_RESTRICTION | sm/default restriction：MB4.7 GeV、MC0 GeV；raw UFO MC1.27與restricted值分開。僅來源核對，沒有model import。 |
| PROCESS_TEXT | import model sm；define p4 = g u u~ d d~ s s~ c c~；generate p4 p4 > b b~ a a QCD=2 QED=2。QCD/QED為amplitude上界，process未解析。 |
| PHOTON_IR_READINESS | SOURCE_SEMANTICS_REVIEWED；PHYSICAL_READINESS_BLOCKED。maxjetflavor4下b不屬is_a_j，Frixione不能自動視為包含b；所有數值候選均PROPOSED_NOT_PHYSICALLY_VALIDATED，未定cuts/scales/matching保留null。無ATLAS fixed-cone等價宣稱。 |
| PARSER_CONTRACT | 三個semantic commands包含symbolic diagram enumeration，接quit終止；禁止codegen、output、check、數值ME、積分、launch及各種event production。具體本機proposal綁定來源／runtime／config／model／freshoutput，但execution_eligible=false。 |
| PARSER_APPROVAL | NOT_AUTHORIZED。不能重用Phase7I消耗過的BUILD_ONLY。 |
| PARSER_EXECUTED | NO |
| RESOURCE_ENFORCEMENT | 13 child fixtures實測PASS；Landlock ABI3、seccomp defaultKILL、CPU2s／wall3s watchdog／RLIMIT_AS512MiB／每log64KiB、禁止filecreate/descendants/network。完整parent CPU/RAM、totalwall及parentdisk硬界線未證明。source常數同時阻擋launcher/direct child，不能以approval JSON越過。 |
| HUMAN_CONFIRMATION | 沒有新human approval或HumanReview；未代輸入正式確認。future TTY/file機械核對不是human identity的密碼學證明，pipe只是handoff consistency。 |
| PHASE7I_DEPENDENCY_STATUS | NOT_BOUND_BY_REVIEWED_CONTRACT僅限exact Route-A b80靜態結論；本次獨立copy不改Phase7I checkout，沒有build/native/StageA。沒有提升未執行行為為PASS。 |
| HISTORICAL_PRESERVATION | 6756 monitored files／2946918057 bytes與24installed targets零變更或遺失；原MG5及獨立copytree相同。PR24–29 exactheads維持OPEN/Draft且未merge。不是全主機遞迴保證。 |
| TESTS | 最後source變動後unit03再次188 PASS；最終P13 188、P12 167、P11 172，共527全部PASS；13實際kernel fixtures、2個實際negativeCLI PASS。首次source witness失敗與unit01 186tests／2fail1error均保留，修正後才重跑；沒有把synthetic當parser validation。 |

NEW_ME_CALLS: 0  
NEW_INTEGRALS: 0  
NEW_HARD_EVENTS: 0  
NEW_PYTHIA_EVENTS: 0  
NEW_DELPHES_EVENTS: 0

PHYSICAL_TOTAL_BACKGROUND: BLOCKED  
PHYSICAL_SIGNIFICANCE: NOT_EVALUATED  
PHYSICAL_CLs: NOT_EVALUATED

GATES_PASS: exact private runtime/source/config copy；symlink/hardlink isolation；raw historical preservation；PDF/member/backend static closure；model/cut source semantics；13 child resource fixtures；527 offline regressions；negative approval/direct-child rejection；bounded source publication guard。  
GATES_FAIL: complete-launch resource acceptance not met。  
GATES_BLOCKED: MG5/parser execution；numeric MG5 PDF link/binding；physical IR/cut readiness；physical pilot／total background／significance／CLs。  
GATES_UNKNOWN: historical config writer；MG5 startup implicit-write compatibility；publisher alpha interpolation accuracy bound；unexecuted ME/ISR/FSR mappings。

NEXT_RECOMMENDED_STEP: 最小化補齊並實測從preflight到postflight的supervisor CPU/RAM、totalwall與parentdisk envelope；重新公布exact source並獨立審查。通過後才可另請使用者授權symbolic parser；不自動開始physical pilot。

## 證據與限制

來源與 bounded receipts 在 `analysis/phase13/`；詳細 runtime、PDF backend、alpha、model/IR、parser contract 分別見 phase13a–e reports。full private source/config/PDFgrid/binary/test LHE不進Git，沒有未核准PDF/PNG。所有staged paths及每個outgoing commit的中間payload都要在push前稽核；Draft PR不merge、不forcepush。

本機 evidence 根目錄：`/home/btu/simulations/hh_phase13/run_01`。source-job ledger的1800s CPU/wall、1GiB disk是本次來源工程監控設定，不是future parser的完整硬限制證明；資源帳本不包括Git/network、文字編輯與唯讀hash inventories。
