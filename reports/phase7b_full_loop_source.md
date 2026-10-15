# Phase7B：完整有限質量迴圈來源

使用既有 MG5 3.5.16 的 `loop_sm`，製程為 `g g > h h [noborn=QCD]`，原生 MadEvent 匯出含 16 個迴圈圖：top 與 bottom 各 6 box、2 triangle，含模型 R2 項。這是 LO loop-induced full-mass；不使用 HEFT、K factor 或 NLO+PS 標籤。

沿用的 Phase7A 模型證據加上本次實際 21 組生產提案參數固定點測試，核對有限 top/bottom 質量、box/triangle/interference、SM/κ 慣例、交換與數值穩定性。另實際執行 native gluon1 Ward 替換，最大平方矩陣元素比值低於 2.1×10⁻³¹。Ward 收據的參數作用域與新固定點網格分別保存在 `simulation/hh_signal/evidence/campaign/`，不混稱為積分截面驗證。

MH=125、MT=173、MB=4.7 GeV，YUKAWA[6]=173、[5]=4.7；自耦合對應 GC_30，top Yukawa 對應 GC_37。PDF 為既有 CTEQ6L1；原生 dynamic choice4、factor0.5 給出 μR=μF=mHH/2。實際來源卡的 SMINPUTS[3]=0.129783；LHE 的每事件 ALPS 與尺度另外保留。全程沿用既有軟體，私有目錄編譯，不修改安裝來源。
