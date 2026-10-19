# Phase8H 六個 kappa_lambda benchmark 的共同來源診斷

## 目標、實際輸入與方法

讀取原已產生的6000列actual full-mass ME reweights，沒有呼叫MG5或MadLoop。六個benchmark共用1000個C1000 source events；source ordinal與hard-event SHA256逐筆join本次native ROOT summaries。每來源恰六個不同label，duplicate/missing/hash mismatch/nonfinite/normalization不符均拒絕。

來源是歷史NNPDF23 LO、two-loop alpha_s、seed20261122，不重標CTEQ6L1，不引入corrected SM1000。RAW_PRODUCTION weight已含sigma/N與ME ratio；MODEL_BR_ONLY欄已乘一次mixed HH factor。immutable CSV SHA256：`c76dd54b9236ee8110385fe746eb465125c70f1f30e0d580ac95acacc03a9e0f`。

## 實際 weighted support

| kappa_lambda | input ESS | final ESS | max ratio | top1 fraction | top5 fraction | top10 fraction | status |
|---|---:|---:|---:|---:|---:|---:|---|
| -1 | 235.494846185 | 43.7733314173 | 188.932646582 | 0.0464997609513 | 0.0944872534627 | 0.132596862518 | VALID_DESCRIPTIVE_ONLY |
| 0 | 503.655334264 | 78.309715798 | 54.1985302534 | 0.0247361543453 | 0.0537682079717 | 0.0783365466644 | VALID_DESCRIPTIVE_ONLY |
| 1 | 1000 | 143 | 1 | 0.001 | 0.005 | 0.01 | VALID_DESCRIPTIVE_ONLY |
| 2 | 204.589404636 | 71.9809431525 | 29.3370558223 | 0.0598846734206 | 0.0928389461056 | 0.10988393019 | VALID_DESCRIPTIVE_ONLY |
| 2.5 | 36.6942995242 | 16.0735705156 | 74.0814285119 | 0.151125507789 | 0.251338619724 | 0.311708522912 | INCONCLUSIVE_REWEIGHTING |
| 5 | 19.5442226883 | 7.65012406875 | 603.561739744 | 0.19819336581 | 0.356832744207 | 0.465684156812 | INCONCLUSIVE_REWEIGHTING |

## 共用事件 covariance 與 per-bin 品質

每原始來源建立六維contribution vector，未通過者保留零。Cov(S_k,S_l)=N/(N-1) sum_i(x_i,k-mean_k)(x_i,l-mean_l)。各stage完整6x6 covariance與correlation維持pairing；marginal variance=0時correlation=null。6000 rows不視為6000獨立事件。

| Stage | minimum eigenvalue | arithmetic PSD tolerance | result |
|---|---:|---:|---|
| INPUT | 4.1478434544e-43 | 4.06646512645e-22 | PASS_WITH_ARITHMETIC_TOLERANCE |
| PHOTONS | -2.73983943203e-27 | 5.62403993144e-23 | PASS_WITH_ARITHMETIC_TOLERANCE |
| JETS | -1.43160021069e-27 | 4.6755076719e-23 | PASS_WITH_ARITHMETIC_TOLERANCE |
| TWO_BTAGS | -1.27727890324e-27 | 3.63499179852e-23 | PASS_WITH_ARITHMETIC_TOLERANCE |
| FINAL_MGG | -1.27727890324e-27 | 3.63499179852e-23 | PASS_WITH_ARITHMETIC_TOLERANCE |

實際10770個bin/kappa/stage診斷含flows、source count、moments、ESS、最大來源比例與missing。EMPTY_BIN、LOW_ESS_LT10/LT20、HIGH_SINGLE_EVENT_DOMINANCE、CANCELLATION_DOMINATED保留具體數據；不能以全樣本ESS代替bin precision。

## Dominant source、統計限制與驗證

kappa=2.5最大來源ordinal 213，ratio=74.0814285119，hard-event SHA256 `95a65504cea7007eaac423839d6b87986eedd8742dd3cfaf2d9899c55fc423cc`。
kappa=5.0最大來源ordinal 213，ratio=603.561739744，hard-event SHA256 `95a65504cea7007eaac423839d6b87986eedd8742dd3cfaf2d9899c55fc423cc`。

kappa=2.5與5維持INCONCLUSIVE_REWEIGHTING。shared-event covariance只描述此proposal的MC sampling，不替代target-benchmark獨立integrals，也不修復歷史絕對normalization。無physical kappa interval。獨立Decimal70重算全部stage covariance/correlation、所有bin ESS與tail fractions；PSD容差綁定matrix norm及binary64 epsilon，沒有剪裁eigenvalues。

## 未解問題與下一步

未來須分別審查獨立kappa proposals或multiple-importance-sampling設計，保留proposal probabilities、各來源N、組合權重與correlations；不能複製rows假增事件。本次不執行production。
