# Phase12 完整驗收報告：runtime provenance 與隔離 4F PDF recovery

本報告綁定已完成的 canonical readback_04、167項Phase12方法／負測試、172項Phase11單元回歸，以及4764歷史檔案／24 installed files的after-preservation。來源commit、Draft PR、GitHub CI與遠端逐byte驗證將在交付步驟填入實際身份；不以本機成功替代GitHub證據。

最終科學結論為 **PASS_PHASE12_PARTIAL_RECOVERY**。本次實際補齊了唯一選定 4F central member 的外部 payload 與有限 native interface 讀回，也建立三個 PID 的 exact runtime observations；沒有批准新 runtime baseline、辨識歷史 writer，或選出已驗證的 generator component。`NONE_READY`、MG5 parser 未執行、physical pilot 未授權均保留。

## 1. 指定最終欄位

```text
PROJECT: ATLAS_HH_BBGG_PUBLIC_V1
TASK: PHASE12_RUNTIME_PROVENANCE_AND_4F_PDF_RECOVERY_V1
BASE_REVISION: 988c5a8b23f0ae3edf536bbabd17eef291717335
NEW_SOURCE_REVISION: PENDING_DELIVERY
DRAFT_PR_URL: PENDING_DELIVERY

RUNTIME_CURRENT_SHA256: e4567fd50d47a317407eb10cca76387053cdf06631949773296314702f77dca1
RUNTIME_CURRENT_BYTES: 9302
RUNTIME_SNAPSHOT_STATUS: THREE_SEQUENTIAL_SNAPSHOTS_STABLE_WITH_LIMITS
RUNTIME_WRITER_IDENTIFIED: NO — ACTUAL_WRITER=UNKNOWN
PROPOSED_BASELINE: phase12-proposed-runtime-v1 / PROPOSED_UNAPPROVED
BASELINE_APPROVED: NO

PHASE7I_DEPENDENCY_IMPACT: NOT_BOUND_BY_REVIEWED_CONTRACT

OFFICIAL_4F_PDF_CANDIDATE: NNPDF30_lo_as_0130_nf_4 / DataVersion=2 / member=0 / LHAPDF_ID=263400
PDF_DOWNLOAD_STATUS: PASS_COMPLETE_SELECTED_MEMBER_ACQUISITION
PDF_MEMBER_SHA256: e3055763f3a3154c2a2c6811d35e1f319a0bb38ff1c645c8db5cdc8bd210005e
PDF_INFO_SHA256: 85f3b2626de0896f45f5cfef53d90abd8d7b5ae784800b18d652e3f817431162
PDF_FLAVOUR_COMPATIBILITY: PROPOSED_WITH_EVIDENCE — variable maximum4 / no bottom PDF; actual native flavours checked
PDF_ALPHA_S_REFERENCE: declared Q=4.1799998 GeV, alpha=0.2544023564420006; native=0.254403024565842; physical ME/shower binding UNVERIFIED
ISOLATED_PDF_READBACK: canonical readback_04 PASS_ISOLATED_NATIVE_PDF_INTERFACE_WITH_LIMITS; 36 xfx /5 alpha /5 wrapper guards; exact03/04same-point regression

MG5_PARSER_EXECUTED: NO
MATCHING_VALIDATED: NO

NEW_ME_CALLS: 0
NEW_INTEGRALS: 0
NEW_HARD_EVENTS: 0
NEW_PYTHIA_EVENTS: 0
NEW_DELPHES_EVENTS: 0

HISTORICAL_PRESERVATION: PASS — 4764 historical files/2778583870bytes and24 installed files exact before/after; PR24–28 HEAD/Draft unchanged
TESTS: PASS — 167 Phase12 +172 Phase11 unit regression; no full historical analysis rerun
GITHUB_CI: PENDING_DELIVERY
REMOTE_BLOB_VERIFICATION: PENDING_DELIVERY

GATES_PASS: actual runtime snapshots; exact serializer transformation reproduction; official isolated info/member acquisition; 4F metadata/native flavour readback; finite interface points; explicit domain rejection guards; Phase7I contract dependency audit
GATES_FAIL: alpha reference strict1e-6 diagnostic=false; relative difference2.626248635282933e-6; this is not a publisher accuracy bound
GATES_BLOCKED: old Phase11 raw-source gate; new baseline approval; MG5 PDF/alpha binding; photon IR/cuts/scales/shower/weights; parser; matching; physical pilot; total background and physical inference
GATES_UNKNOWN: actual historical writer; publisher checksum authenticity; standalone grid formal license identifier; official interpolation-accuracy bound; future runtime immutability; unobserved Phase7I implicit runtime behavior

FINAL_VERDICT: PASS_PHASE12_PARTIAL_RECOVERY
NEXT_RECOMMENDED_STEP: independently review the proposed exact runtime baseline and PDF alpha/reference contract, close remaining source settings, then request separately scoped parser-only authorization if justified; no automatic physical execution
```

## 2. Runtime：三次直接觀察，沒有 normalization 或自動 rebaseline

實際讀取 `/home/btu/opt/mg5amcnlo/input/mg5_configuration.txt`，解析位置為 `/home/btu/.local/share/atlas-hh-phase6a/mg5-release-v3.5.16/input/mg5_configuration.txt`。三個循序子程序 PID 為 **129230、129231、129232**，控制 PID=129229；UTC 觀察區間為 2026-10-19 09:37:28.868331–09:37:28.976165，約 0.108 秒。raw bytes、SHA256、device、inode、mtime／ctime 與解析路徑一致。

Filesystem 為 ext4／`/dev/sdd`；device=2096（8:48），inode=243763。讀取採 O_RDONLY 及 descriptor 前後身分比對；這些是同主機共享快取的三次觀察，不是三個獨立 cold-cache 實驗，也不證明未來不會改變。

歷史 A／B／C 分別為 9212／9239／9266 bytes，其 SHA 保留原值。目前 9302 bytes 相對多出 90／63／36 bytes。有限、記憶體內的逆推候選只有在完整 bytes 的長度與已知 SHA 同時相符才被接受，標記為**精確 hash 重建，不是原始備份或過去時間的現場讀回**。每份比較都有三個 whitespace-only 改動區段；有效 setting 改變數為 0，完整 semantic hash 為 `63ffabb654213dac4909bb3c9b6d64780976629620a83970f06c17658b927004`。

對安裝 serializer 原始碼的檢查與獨立字串運算，精確得到 A→第3輪B→第6輪C→第10輪目前值，因此 `SERIALIZER_BEHAVIOR_REPRODUCED`。這沒有提供實際 caller 的直接證據；23 份已授權 task execution receipts 亦不足以辨識歷史 writer，故維持 UNKNOWN。未讀取私人 histories、credentials、無關程序，未掛侵入式 tracing。

新的 `phase12-proposed-runtime-v1` private copy 只存在獨立 Phase12 結果工作區，SHA 與目前 snapshot 相同。baseline approval=false、physical authorization=false、dispatcher=null。沒有回復或覆寫 installed config、修改舊 A02 receipt、用 semantic equality 取代 raw SHA，或把舊 Phase11 gate 改為 PASS。詳見 [Phase12A](phase12a_runtime_drift.md) 與 [runtime metadata](../metadata/phase12_runtime_identity.json)。

## 3. Phase7I：精確 contract 的依賴影響

在 exact `b80e16775bf141e45f4048c7197a8a99befaed51`，選定 25 份 critical source／descriptor 的實際 bytes 與 Git blobs 相符；審查涵蓋 7 份明列 inventory、正向 callchain 與 path alias。結果是目標 global configuration **NOT_BOUND_BY_REVIEWED_CONTRACT**，不能由 Phase11 drift 自動推定 Phase7I 所有 frozen process、model、toolchain 或 binary 失效。

這項工作沒有重新 hash 全部 frozen payload、執行 loader／native preflight、prepare-review、HumanReview、Route-A build 或 Stage A。未執行 runtime 的隱含依賴保留 UNKNOWN；沒有給舊 build 新 PASS 或沿用已 consumed 的 BUILD_ONLY 授權。詳見 [Phase12B](phase12b_phase7i_dependency.md) 與 [dependency evidence](../analysis/phase12/evidence/phase7i_dependency_impact.json)。

## 4. 唯一官方 PDF：實際取得，沒有放入 live MG5／conda

唯一候選為 **NNPDF30_lo_as_0130_nf_4／member 0／LHAPDF ID 263400／DataVersion 2**。中央 member 0 是 replica average；本次沒有取得其餘 100 個 replicas，不建立 PDF uncertainty band。

| 原始 payload | bytes | SHA256 |
|---|---:|---|
| [.info 官方 HTTPS](https://lhapdfsets.web.cern.ch/current/NNPDF30_lo_as_0130_nf_4/NNPDF30_lo_as_0130_nf_4.info) | 2345 | `85f3b2626de0896f45f5cfef53d90abd8d7b5ae784800b18d652e3f817431162` |
| [member 0 官方 HTTPS](https://lhapdfsets.web.cern.ch/current/NNPDF30_lo_as_0130_nf_4/NNPDF30_lo_as_0130_nf_4_0000.dat) | 683592 | `e3055763f3a3154c2a2c6811d35e1f319a0bb38ff1c645c8db5cdc8bd210005e` |

Acquisition 記帳的 response-body 合計 **685937 bytes**，低於 128 MiB aggregate 與 80 MiB single-payload 上限。兩個檔案的 advertised／received 長度一致，TLS verification 開啟，沒有 redirect、archive、第二候選或 installed-path write。保存於新的 ext4 外部資料夾 `hh_phase12/run_01/public_pdf_01`。

未找到 publisher checksum／signature，因此本次 SHA 固定收到的 bytes，**不等於獨立的 publisher cryptographic authenticity proof**。官方頁提供公開下載與科學使用方向；未查得此 grid 的獨立 formal license identifier，保持 UNSPECIFIED，不推成任意再散布授權。

實際 acquisition 早於 output-parent guard hardening；後來的 guard 用負向 fixtures 與實際 parent chain 的唯讀檢查驗證，沒有重抓 payload。不得把已成功的舊 acquisition 說成較新 guard 版本已重新端到端網路執行。參見 [Phase12C](phase12c_4f_pdf_candidate.md) 與 [acquisition receipt](../analysis/phase12/evidence/acquisition_receipt.json)。

## 5. Native interface：有限點有效，但 alpha diagnostic 沒有強行 PASS

已實際以現有 **LHAPDF 6.5.6** 讀取外部 member 0。native flavour list 為 `[-4,-3,-2,-1,1,2,3,4,21]`；bottom 不 active。metadata 為 variable scheme、最高4 flavour、LO／ipol；未由 set 名稱猜成 5F 或 analytic running。

readback_03 實際檢查了 4 個 x/Q 組合、9 flavours，共 **36 個有限 xfx 值**，另讀 **5 個 alpha 值**；沒有 nonfinite 或 interpolation exception。5 個 domain／NaN 負向點在 native interpolation **之前**由 wrapper guard 拒絕。這不能被改寫成「native default 本身不會 extrapolate」。

member 的解析路徑與 SHA 綁定外部 payload；reader 同時觀測到既有 built-in metadata 搜尋路徑，相關 config/index 與 reader/library hashes 都記錄。結論為外部 member 的隔離 interface 檢查，不能宣稱完全沒有 built-in metadata fallback，更不能宣稱 member 已綁入 MG5。

| alpha quantity | 實際值／狀態 |
|---|---|
| metadata reference Q | 4.1799998 GeV，不能自動解成物理 Z 質量 |
| metadata reference alpha | 0.2544023564420006 |
| native alpha 於上述 Q | 0.254403024565842 |
| absolute／relative 差 | 6.681238414185664×10⁻⁷／2.626248635282933×10⁻⁶ |
| strict relative diagnostic | 1×10⁻⁶；**false，保留失敗旗標** |
| native alpha(91.1876 GeV) | 0.12470053368074485，不能由名稱 `0130` 改填 0.130 |

declared reference 位於 ipol nodes 3.7262747 與 4.23139 GeV 之間，不是 exact table knot。publisher 的 interpolation accuracy bound 未知；1e-6 是本工作診斷條件，不是官方物理精度標準。沒有為了通過而放寬 tolerance 或修改 metadata／grid；實際 ME／ISR／FSR alpha 與 scale／threshold binding 保持 UNVERIFIED。

readback_04 已實際執行新output guards與相同有限點；五個executed-source hashes及10個raw input/backend identities前後相同。03/04的36xfx與5alpha數值完全一致。最後的 [member readback](../analysis/phase12/evidence/pdf_readback_04/pdf_member_readback.json) 與 [alpha checks](../analysis/phase12/evidence/pdf_readback_04/pdf_alpha_reference_checks.json) 綁定實際04 revision，沒有用較早結果冒充。

## 6. Generator readiness 與物理界線

Candidate A 的 model/default restriction 與既有 MB=4.7、MC=0 來源定義保留；新資料只補上來源明確、已讀回的外部 4F member。這沒有自動解決 PDF-native alpha 與硬過程／shower binding、4F bottom 的 photon isolation coverage、數值 cuts／scale、shower settings、weight writer closure 或 exact-process parser。

Candidate B 的 common 5F aa+0/1/2 family 不會拿這個 4F member 靜默替代；此次未產生新的 5F matching 或 multiplicity closure 證據。兩者均無 source gaps 的歷史 defaults 自動填值，選定 pilot 仍為 **NONE_READY**。

保持：PHYSICAL_TOTAL_BACKGROUND=BLOCKED、PHYSICAL_SIGNIFICANCE=NOT_EVALUATED、PHYSICAL_CLs=NOT_EVALUATED、PHOTON_FAKE_RATE=UNKNOWN。沒有新 MG5 process、ME、integral、hard event、Pythia、Delphes、Route-A build、Stage A 或 likelihood。PDF interpolation 不構成 parser 或物理執行授權。

## 7. 測試、保存與出版封帳

本報告目前可以確認的 focused method evidence 包括 runtime 26、Phase7I dependency 22、PDF metadata 30，以及 acquisition 獨立負向檢查 15 項。這些 scope 分開，不相加冒稱正式物理驗證；最終 Phase12 suite 與相關 Phase11 method regression 的實際總數／結果待 root 封帳，未重跑完整 Phase8–11 分析。

起始保存manifest的 **4764個歷史檔案、2778583870bytes** 與 **24個installed input/PDF/LHAPDF files** 已完成after逐檔SHA／bytes比對，全部相同。PR24–28仍OPEN/DRAFT、HEAD不變，舊source HEAD/index控制符合原記錄；Phase11 tracked工作區與index乾淨。這個有界保存範圍不等於整台host任意檔案或每個stopped workspace所有內容的完整稽核。source commit、Draft PR、CI與immutable remote blobs在交付時另填實際結果。

GitHub 僅發布 source、tests、bounded JSON metadata／reports。下載 grid、private configuration bytes、原生 binaries 不進 Git；沒有未核准 PDF／PNG 出版。原始失敗收據、各次版本、A02 與 Phase7I stopped workspace 不覆寫。自動 method tests／子代理 review 不冒稱外部人類 approval。