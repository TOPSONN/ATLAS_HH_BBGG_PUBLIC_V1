# Phase7C：獨立1000事件完整鏈

本次新生成並驗證1000個獨立 full-mass SM ggF HH硬來源，有效seed20261122，與保留pilot的實際seed21不同。沒有把B100或10/100前綴計入C1000，總獨立硬來源為1100，沒有再開新來源。

來源LHE截面=0.019069 ± 0.00011745 pb，誤差是MG5所報積分誤差。gzip SHA256=`b13e5010f80b734495598492c97f5a7f73da72568c296134b2fb15b302a69eac`。SOURCE、物理混合衰變、Pythia、通用與訊號專用native ReaderAscii、Delphes3.5.1、ROOT6.40.04/C++20均實際通過完整1000記錄檢查。使用1個生成核心，沿用既有安裝，不修改歷史來源。

完整1000 HepMC與ROOT保存在本機。公開選定資料為原始1000 LHE、同來源物理衰變LHE、經逐事件比對一致的100事件HepMC/ROOT前綴，以及卡片與收據。所有表示與前綴的額外獨立統計都是0。

絕對正規化仍為INCONCLUSIVE_ABSOLUTE_NORMALIZATION_CROSS_RUN_TENSION；不能把完整事件鏈PASS解讀成精密截面已通過獨立收斂驗證。
