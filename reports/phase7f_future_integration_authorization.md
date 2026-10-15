# Phase7F：下一階段積分契約

目前 **NOT_AUTHORIZED**。四個 replicas 已準備並建置，seeds=910001/910019/910037/910061；沒有 integral 或新硬事件。具體使用入口與 refusal 行為見 [繁體中文指南](../simulation/hh_signal/config_lock/USER_GUIDE_ZH_TW.md)。

後續需先審查精確 Git revision、configuration lock SHA、writer patch/native gate、資源上限及 [authorization_contract.json](../simulation/hh_signal/config_lock/authorization_contract.json)，再由使用者另行明確授權。填寫契約不是授權；本版 Python deny 與 native STOP80 都不會因檔案或環境變數而解除。

每 replica 以獨立 workspace、新 adaptation grid 起始，不匯入 B/C grids。survey 與 measurement 分開保存；measurement 只可使用本 replica 的已綁定 survey grid，固定 grid input=0，預先指定新 moffset=1。stage 轉換的完整 grid receipt、native seed trace、ME counters、逐 iteration mean/error/χ、模型穩定性與終止原因必須保留；目前尚未實際走過此轉換。

行政上限：1 concurrent job、1 worker、aggregate wall/CPU各4h、額外磁碟5GiB。它們是 ceiling，不是成本或精度保證。具體 points、warmup/measurement iteration endpoints 與 budget checkpoints 尚須在下階段授權中明列；不自動沿用會提前停止的原 survey 設定，不自動加 budget。

誤差方法以固定 budget 的獨立 replica endpoints 為主：均值、replica dispersion/√4 與 t3 的95%區間（係數3.1824463）；run 內所報 error 的均值誤差另列 sqrt(Σerror²)/4。兩者不盲目相加。四個 replicas 的自由度只有3，不能保證精度或 empirical coverage。重複觀察 adaptive stages 後停止，不能繼續宣稱固定樣本 CI。

增加 budget 的比較須預先指定 endpoints；共用樣本/grid 的結果具相關性，使用 paired differences 或真正獨立 budget arms，不能充當獨立 replicas 套 χ²。若結果、tail/loop stability、grid drift 或 between-run dispersion 不足，停止並報 INCONCLUSIVE，另行審核預算。

writer suppression 可能改變候選狀態／RNG 消耗，需明確驗證其對 native stopping/reporting 的影響；不得以相同 matrix-element source 或初始化 PASS 取代此驗證。真實 zero-retention runtime audit、全程 counters 與 metadata一致性也是獨立 gate。

歷史 B/C 的 integrand 仍不同，舊 8.18128 所報誤差單位不是同 integrand seed pull；絕對截面仍 INCONCLUSIVE，κ2.5/5 仍 INCONCLUSIVE_REWEIGHTING。本次沒有宣稱 integration convergence，也沒有修正任何舊數值。
