# Phase6G 權重與 Higgs BR closure

每筆 raw source contribution = 原始 signed XWGTUP / 完整原始1000。原始 LHE、Pythia Info 與 HepMC converter nominal columns 實際逐筆 closure 通過後，missing initialized H→γγ model factor 才能乘一次。No sigma/N twice、No Z BR twice、No HH factor2、No implicit luminosity。

| Process | Raw source sum (pb) | Raw source sum2 (pb²) | Observed Info/LHE min/max | H factor / applications | MODEL_BR_ONLY sum (pb) |
| --- | --- | --- | --- | --- | --- |
| B04 | 0.08953800000000001000 | 0.000008017053444000001790760000000 | 1.000000000000000223368848980/1.000000000000000223368848980 | 0.0022965313147512443/1 | 0.0002056268208601969350987131475 |
| B05 | 0.399182000 | 0.000159346269124000 | 1.000000000000000100204919059/1.000000000000000100204919059 | 0.002297546784308979/1 | 0.000917139320454026855178000 |
| B06 | 65.88308600000001000 | 4.340581020883397317661720000 | 1.000000000000000303568050835/1.000000000000000303568050835 | NOT_APPLICABLE/0 | NOT_APPLICABLE |

LHE init integration result 與 preserved raw XWGTUP average 分別保存，不將較精確 raw token 強制改成 init 的 printed value：

| Process | Init sigma (pb) | Original raw XWGTUP sum (pb) | Actual raw XWGTUP mean (pb) | Mean minus init (pb) |
| --- | --- | --- | --- | --- |
| B04 | 0.08953800 | 89.538000000 | 0.089538000 | 0E-9 |
| B05 | 0.3991820 | 399.18200000 | 0.39918200 | 0E-8 |
| B06 | 65.88309 | 65883.086000 | 65.883086 | -0.000004 |

B06 init sigma 的7位有效數字與 raw weights 的8位數精度不同，4e-6 pb 差異小於合併 printed half-unit 5.5e-6 pb；native binary64 serialization 的其餘微小差異另由逐筆 closure 判斷。沒有 source reweighting或第二次sigma/N。

實測 initialized inclusive / forced Higgs tables、total/partial widths 與 exact table hashes 在 machine-readable ledger 分開保存。B04/B05使用各自實際 initialized factor，不能假設相等。Pythia reference 0.0022965313147512443 與 YR4 comparison 0.002270 是不同慣例，未混用。MODEL_BR_ONLY 是模型一致 pilot normalization，precision physical BR uncertainty/adoption 為 BLOCKED。B06 無 Higgs BR factor。

[各 process 完整 weight accounting](../metadata/phase6g_weight_accounting.json)。

實際 B04/B05 的 Mt=173、MZ=91.188、MH=125相同，Pythia MW 分別80.385/80.419 GeV；兩個initialized H total/partial widths及BR確實不同。Pinned ResonanceWidths.cc source inspection顯示mW進入Higgs width prefactor與charged-W γγ loop。差異與此mass dependence一致是 `CAUSAL_INFERENCE_ONLY`，未以controlled reinitialization隔離唯一原因，也未重跑事件或強制BR等於reference。

[Actual process-table comparison and source inspection](../simulation/new_backgrounds/evidence/Higgs_model_BR_process_comparison.json)。
