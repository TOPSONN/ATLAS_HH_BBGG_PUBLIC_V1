# Phase7D：獨立實際矩陣元素與數值回歸

原生模型包含有限MT與MB的box/triangle及干涉，未用HEFT。每個來源使用原始p4、ALPS、尺度、MH125、MT173、MB4.7與實際H寬度。每點重複SM閉合最大相對殘差=0；0/1/2重建二次式對保留−1/2.5/5最大殘差=3.46446536867e-09。κλ=0的實際HHH耦合為0，DP/MP coupling均顯式重設。

14個真實C來源點（含QP rescue案例）先以獨立fresh process對照慢批次與快批次，兩者全部差0；驗證時間283.71479秒累計入D上限。保留最初30個完整fresh事件及原部分第31點失敗/停止log；其餘970個事件採已綁定來源/driver/binary SHA的13次原生函數批次。所有批次SM校準與7個結果回傳碼均實際重新稽核，RC主類僅200/300。

獨立60位Decimal/Lagrange回歸不呼叫production quadratic，檢查6000真實列的來源hash、尺度/ALPS、ME比、BR一次、原始N、Cauchy干涉界、sumw/sumw2/ESS及6×6輸入covariance；狀態 `PASS_INDEPENDENT_DECIMAL_LAGRANGE_WEIGHT_AND_INTERFERENCE_REGRESSION`。以插值項絕對值和正規化的最大殘差=1.34754032113e-09，門檻仍為1e−7。

以取消後結果正規化的最大殘差=1.44578790578e-07，有一個1e−7旗標：來源212、κλ=2.5、ratio0.000381786093063。其插值條件縮放殘差2.20759e−11。另對此點額外執行六benchmark及SM重複的獨立fresh-process原生計算，全部與保留batch數值完全相同，RC211/329。數值敏感旗標保留於JSON；沒有修改原始表、捨棄事件或放寬native穩定門檻。獨立fresh-process真實來源點合計15個。

獨立native ROOT extractor實際讀取C1000、六背景各1000與額外B100，共7100筆；核對所有命名Weight的float32值、Event權重、來源ID、有限成員及原固定cutflow。B100不併入C統計。數值ROOT由實際ROOT寫入並重新讀回，逐bin內容與誤差對照CSV；原始來源、卡與歷史物理檔不改動。

絕對率維持 INCONCLUSIVE_ABSOLUTE_NORMALIZATION_CROSS_RUN_TENSION：B/C實際卡一致，但截面差為所報積分誤差quadrature的8.18128倍；這不是已校準Gaussian顯著性。未執行獨立κ benchmark積分，不重縮放來源，不採用NLO K factor。
