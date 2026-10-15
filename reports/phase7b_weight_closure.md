# Phase7B：權重閉合

原始來源 IDWTUP=-4、event_norm=average，未包含H衰變BR。每個事件原始 XWGTUP=0.017276 pb，貢獻為 XWGTUP/100。完整100事件原始權重和=0.017276 pb。

實際追蹤 LHE、Pythia Info、官方 converter 與 HepMC 四個具名欄；原始值和分母保持一致。native ROOT另驗證 Event欄與來源float轉移，後續獨立回歸還會逐一重讀所有具名Weight欄。不能把原始Info再當作已含BR的物理權重。

缺少的BR因子=0.0026534459067208711，只乘一次。MODEL_BR_ONLY輸入權重和=4.5840931484509766e-05 pb，最終18事件和=8.2513676672117591e-06 pb。REFERENCE_BR_WEIGHT與ADOPTED_PHYSICAL_WEIGHT保持null。

最終選擇的來源抽樣標準誤=1.7700234304979053e-06 pb，與原始積分誤差分開。單次detector/tag結果無法獨立測得完整detector抽樣變異；不得捏造BR、PDF/scale或官方ATLAS系統誤差，也不合成未知總誤差帶。
