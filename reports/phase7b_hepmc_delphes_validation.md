# Phase7B：真實 shower、HepMC、Delphes 與 ROOT

同一批100來源先跑10前綴，再跑完整100。兩階段的Pythia next/寫出/獨立ReaderAscii/ROOT計數分別為10/10/10/10及100/100/100/100；總110次shower呼叫包含重用前綴，獨立硬來源仍是100。沒有外部重試、替代來源或忽略失敗事件。

通用native ReaderAscii核對PDG/status、穩定粒子質量殼、頂點及全域四動量、有限權重及來源屬性。訊號專用Reader獨立重建兩顆Higgs譜系與bb/γγ衰變，並建立實際HepMC粒子索引。Delphes3.5.1使用同一份HepMC，原Phase6C物理卡只更換並記錄seed710301。native ROOT6.40.04/C++20核對字典、schema、逐粒子float32四動量/質量/位置多重集合與來源身分。

Phase6C原始cuts不變：photon pT>25、leading>35、|η|<2.37且排除開區間1.37<|η|<1.52；jet pT>25、|η|<2.5；至少兩個bit0 tag；105≤mγγ≤160 GeV。不加mbb最佳化cut。實測cutflow：100 → 45 → 38 → 18 → 18。

缺少配對的質量保持null。Hγγ雙光子幾何重建匹配2/1/0為61/30/9，b到jet匹配2/1/0為61/38/1；這只是幾何診斷，不能當校準效率。模型與選擇驗證不等於官方ATLAS detector接受。
