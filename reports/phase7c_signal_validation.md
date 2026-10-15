# Phase7C：來源、全鏈與限制

1000來源的LHE、原始Higgs四動量、物理兩體衰變、Pythia、獨立ReaderAscii、Delphes與native ROOT的事件身分、權重與計數通過。0替代來源，0忽略事件。10、100、1000階段均來自同一C來源；精確前綴身分另由公開prefix_identity.json核對。

Pythia seed710102、衰變指派seed710202、detector seed710302。原Phase6C物理卡保持不變，只在執行副本更換detector seed。完整來源與完整ROOT/HepMC留本機，公開樣本的原始統計分母仍是1000。

B/C實際參數卡位元一致，23個原生模型來源檔一致，工作run card除事件數外一致。B/C最終截面差=0.001793 pb，相對B差=10.37856%，為兩個所報積分誤差quadrature的8.1813倍。這是收斂可靠性診斷，不是已校準Gaussian顯著性。

保留兩個真實結果，不把C重縮放到B，也不捏造額外官方系統誤差。絕對率在獨立零保留事件的積分/收斂與weighted候選截斷稽核前維持INCONCLUSIVE；新大樣本不在本次授權內。
