# Phase7E：κλ 支持度與未來 proposal

所有結果重新讀取原 6000 筆 native ME rows、原 C1000 事件 SHA、原 full1000 最終 selection（143 surviving）；沒有新 ME evaluation 或新事件。獨立 `math.fsum` 重算與既有 Decimal/Lagrange 回歸分開。

| κλ | input ESS | final ESS | 最大單點份額 | top5 | top10 |
|---|---|---|---|---|---|
| 2.5 | 36.6942995 | 16.0735705 | 15.11255% | 25.13386% | 31.17085% |
| 5 | 19.5442227 | 7.65012407 | 19.81934% | 35.68327% | 46.56842% |

兩者均 **INCONCLUSIVE_REWEIGHTING**。共同 top10 source indices 為 213、502、914、697、39、181、942、761、271、698；每個原始 event SHA、mHH、scale、ALPS、ratio 與是否通過 selection 見 [kappa_support.json](../simulation/hh_signal/integration_audit/evidence/kappa_support.json)。大的權重來自 SM proposal 在目標重要區域支持不足；有限樣本不能證明所有尾部已被找到。

定義 input ESS=(Σu)²/Σu²；final 對原選擇權重 uI 同算。對固定 N=1000 的 selected estimator，事件抽樣相對變異為 N/(N−1)·(1/ESS_final−1/N)，包含本次 source、衰變、shower、detector/tag 結果，不是已隔離的純 generator 變異；跨 κ 共用原事件，需保留完整 covariance。原積分誤差另列；不重複加 tag 波動，不把 source 宏觀配置失配當作統計誤差帶。

只在 proposal 不變、有限二階矩、目前 pilot 可代表未來的假設下，final relative MC error 10% 的粗略 **總 N** 需求約 κ2.5=6122、κ5=12972。這是規劃數，沒有計算入未知尾部、積分／PDF／BR／detector 系統誤差；不是授權事件數，也不保證達標。該 scaling 的 proposal 是**實際 C NNPDF／兩圈**，不能拿來保證修正 CTEQ6L1 後的結果。bootstrap、複製事件、重 shower 或套共同 scale 都不能增加獨立硬點支持。

建議在另行授權後，先以已修正、compiled/runtime 驗證一致的物理契約，為 κλ=2.5、5 直接生成獨立 bounded pilot，保存獨立 seed、積分與 normalization；以目標自身 proposal 驗證目前 dominant/empty regions，而非單純放大 SM pilot。先審核硬點與每 bin ESS、最大貢獻、mHH/cosθ 與 selection/tail 支持，再決定完整樣本量。不得在這次任務執行。

若要共用多 proposal：以正的已正規化 LO 密度 p_j、固定分配 α_j>0 組 q=Σα_j p_j，balance weight 用 f_target/q，而不是各樣本的任意 raw σ 比率。每個 component 的獨立 integral／normalization、相同相空間與 PDF/running 約定須先驗證；若 normalization 用估計值，需傳播其誤差與可能相關性。若包含目標 p_t 且 α_t>0，理想已知 normalized densities 下 p_t/q≤1/α_t，能控制 proposal 比值；這個 bound 不涵蓋未驗證 normalization 或帶負權重情況。此方法需要 evaluator 能算所有 component 密度，現有 D CSV 本身不足以直接實施。

可採 fixed allocation stratified estimator，獨立 component 的 sample variance 依 strata 相加；同一事件對多 κ 的估計保留 event-level covariance。proposal allocation 可先用獨立 pilot 的變異／成本決定，再 freeze 到後續 production，不能用同批觀察到的極端權重調到好看後仍當固定設計 CI。所有新 generation、積分、預算及 reference publication 均另案審核；目前沒有任何新事件。
