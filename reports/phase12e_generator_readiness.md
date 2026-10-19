# Phase12E：精確依賴變化與 generator pre-flight

本階段結論為 **PASS_PHASE12_PARTIAL_RECOVERY**，selected pilot 仍為 **NONE_READY**。改善的是可觀察的 runtime 身分與實際可讀取的 isolated 4F member；沒有解除舊 Phase11 raw gate，沒有執行 MG5 parser。

## 哪些具體缺件有了新證據

目前 config 為 9302 bytes、SHA256 `e4567fd50d47a317407eb10cca76387053cdf06631949773296314702f77dca1`。三個順序啟動的 PID 得到相同 bytes／inode／device，並有 private versioned copy。但約0.108秒的同主機觀察不是 cold-cache 獨立試驗，更不是未來不能改變的保證。writer 仍 UNKNOWN，proposal 未經人類審核，baseline approved=false。

官方 NNPDF30_lo_as_0130_nf_4 member0／ID263400／DataVersion2 的 .info 和 grid 實際取得，共685937bytes。現有 LHAPDF6.5.6 從 external selected member 讀取，9種native flavours不含±5；36 xfx與5 alpha有限，5域外輸入由wrapper先行拒絕。builtin metadata fallback 仍可見，但 selected info/member/conf/index 的 native findFile 均解析至 isolated folder，且沒有同名installedset。沒有把外部資料安裝至 MG5／conda。

`AlphaS_Type=ipol` 使用50個 table nodes。宣告 MZ=4.1799998 GeV、AlphaS_MZ=0.2544023564420006；該點不是table knot。native值0.254403024565842，relative difference2.626248635282933e-6，因此原strict1e-6 diagnostic仍為false。沒有放寬容差。AlphaS.h 將setMZ/setAlphaSMZ註為ODE solver使用；ipol不保證在非knot精確命中metadata欄位。這是保留的數值差異，尚無publisher interpolation accuracy bound，也不是ME/shower alpha綁定通過。native alpha(91.1876)=0.12470053368074485，不能由名稱0130推成0.130。

## A/B十三個領域

[candidate matrix](../analysis/phase12/evidence/candidate_scientific_matrix.json)每案列 Model、Restriction、PDF member、AlphaS、Threshold、Photon IR、Cuts、Scale、Shower、Matching、Weights、Runtime identity、Exact-process parser，共26列。只用 VALIDATED_EXACT_SOURCE、PROPOSED_WITH_EVIDENCE、UNVERIFIED、BLOCKED、NOT_APPLICABLE；數值缺件保持null。

| 領域 | Massive 4F A | Common 5F B |
|---|---|---|
| Model/restriction | 現行raw model witnesses；sm/default MB4.7 MC0 | 現行raw model witnesses；sm-no_b_mass MB=MC=0 |
| PDF | PROPOSED_WITH_EVIDENCE：實際native4F外部member；MG5 binding未驗證 | BLOCKED：nf4的新證據不能替5F選member |
| Alpha/threshold | native ipol與metadata有確切量測；ME/ISR/FSR綁定UNVERIFIED | 未因4F測試改變 |
| Photon IR/cuts/scale | BLOCKED，沒有填新數值 | BLOCKED，沒有填新數值 |
| Shower/weights | UNVERIFIED；沒有新events/native event weight closure | UNVERIFIED |
| Matching | 此孤立LO review target未引入merging；NOT_APPLICABLE不表示互斥性通過 | BLOCKED：MLM/CKKW-L精確family與scale仍未驗證 |
| Runtime/parser | BLOCKED：新baseline未核准；parser未執行 | 同左 |

模型pole mass、PDF evolution mass／threshold及ipol knots屬不同定義；本次沒有以數字不同就宣告普遍不相容，也沒有假設相同就足以通過。massive-b photon isolation、generation cuts、hard scale、QCD/QED shower、merging weight與物理source normalization仍須逐一凍結。

## 未啟用的 parser review request

[parser-only request](../analysis/phase12/config/parser_only_review_request.json)和[全註解卡](../analysis/phase12/config/parser_only.inactive.txt)僅包含 import model、define p4、generate 的未執行提案；output、launch、check、compile、ME、integral、events均禁止。dispatcher=null、execution_authorized=false、approved_limits=null。示例300s CPU/wall、1 job/worker、1GiB RAM與256MiB disk沒有被批准。精確source payload commit由交付manifest綁定，future execution revision仍null，不能以本PR或舊BUILD_ONLY授權啟動。

PHYSICAL_TOTAL_BACKGROUND=BLOCKED；PHYSICAL_SIGNIFICANCE/CLs=NOT_EVALUATED；PHOTON_FAKE_RATE=UNKNOWN；matched signal normalization仍BLOCKED_PHASE7I；heavy-flavour exclusivity仍UNVERIFIED。
