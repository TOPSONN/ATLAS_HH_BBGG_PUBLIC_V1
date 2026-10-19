# Phase8J RooFit / RooStats synthetic likelihood 方法

## 目標與實際輸入

本次實際執行native RooFit/RooStats likelihood tests。所有數據是明確定義的人工正yield toy，標記SYNTHETIC_METHOD_ONLY；沒有用HH或背景資料做inference。typed template要求dataset/process/region/observable、edges、expected bins、sumw2、signed status、normalization、overlap、systematics、source identity與validation state。

## 選擇與算法

counting Poisson用signal10、background20、Asimov count30驗證mu MLE、log likelihood、analytic likelihood ratio、curvature variance及boundary。RooStats實際建立Asimov count並計算profile-likelihood interval。

人工Gaussian peak總signal20覆蓋smooth positive background；各bin由Gaussian積分決定。extended binned model以Poisson product驗證total-Poisson乘multinomial等價。模型包含mu>=0、Gaussian auxiliary nuisance、正log-normal rate、背景normalization、保持總量的exponential shape morph與scaled-Poisson effective-count MC-stat auxiliary。effective-count僅為toy方法，不是signed MC一般解法。

## 實際數值測試

| Test | result | evidence |
|---|---|---|
| count_parameter_recovery | PASS | SYNTHETIC_METHOD_TEST |
| count_covariance | PASS | SYNTHETIC_METHOD_TEST |
| count_likelihood_ratio | PASS | SYNTHETIC_METHOD_TEST |
| expected_log_likelihood | PASS | SYNTHETIC_METHOD_TEST |
| zero_count_zero_expectation | PASS | SYNTHETIC_METHOD_TEST |
| positive_count_zero_expectation | PASS | SYNTHETIC_METHOD_TEST |
| small_positive_expectation | PASS | SYNTHETIC_METHOD_TEST |
| RooStats_Asimov | PASS | SYNTHETIC_METHOD_TEST |
| RooStats_profile_likelihood_interval | PASS | SYNTHETIC_METHOD_TEST |
| signal_strength_boundary | PASS | SYNTHETIC_METHOD_TEST |
| template_bin_integration | PASS | SYNTHETIC_METHOD_TEST |
| extended_binned_Asimov_recovery | PASS | SYNTHETIC_METHOD_TEST |
| binned_covariance_matrix | PASS | SYNTHETIC_METHOD_TEST |
| Gaussian_constraint_normalization | PASS | SYNTHETIC_METHOD_TEST |
| lognormal_constraint_normalization | PASS | SYNTHETIC_METHOD_TEST |
| Gaussian_analytic_density | PASS | SYNTHETIC_METHOD_TEST |
| lognormal_analytic_density | PASS | SYNTHETIC_METHOD_TEST |
| extended_binned_likelihood_identity | PASS | SYNTHETIC_METHOD_TEST |
| shape_nuisance_normalized_integral | PASS | SYNTHETIC_METHOD_TEST |
| deterministic_toy_seed | PASS | SYNTHETIC_METHOD_TEST |
| negative_expectation_rejected | PASS | SYNTHETIC_METHOD_TEST |
| nonfinite_expectation_rejected | PASS | SYNTHETIC_METHOD_TEST |
| signed_weight_model_rejected | PASS | SYNTHETIC_METHOD_TEST |
| missing_provenance_rejected | PASS | SYNTHETIC_METHOD_TEST |
| synthetic_cannot_unlock_physical_fit | PASS | SYNTHETIC_METHOD_TEST |
| unknown_overlap_and_nuisance_rejected | PASS | SYNTHETIC_METHOD_TEST |

Binned Asimov實測 mu=0.999999806946、Gaussian normalization pull=-1.91163939131e-08、shape pull=-3.03874650841e-08、positive rate beta=0.999999941865、max|gamma_MC-1|=6.98230948615e-08、EDM=1.72300104745e-12。使用strategy=2、tolerance=1e-07及有限call/iteration上限；同時檢查pull closure，fit status0本身不替代Asimov closure。

Counting toy 的外部 Hessian covariance=0.30000077659，analytic variance=0.3；沿用absolute0.005測試容差。bounded RooRealVar的Minuit symmetric error平方=0.292575387717，受有界參數內部座標變換影響，分開記錄。covariance gate比較實際Hessian矩陣元素；不把bounded error平方誤當該矩陣。

共26項synthetic checks，狀態`PASS_SYNTHETIC_METHOD_ONLY`，deterministic toy seed=820019；方法收據SHA256 `66c3dca5222c17bcb5f51a43e28f4fc5d86a0b2359317b8bf8caaca1ffdafc58`。

## Zero / negative policy與統計限制

n=0、lambda=0的log likelihood為0；n>0、lambda=0為負無限，不換成假小正數。small-positive expectation走log domain。negative/nonfinite expected bin、未建立signed-weight Poisson model、缺provenance、unknown overlap/systematics均拒絕；不把負bin剪成0，不把unknown nuisance改成零寬。

## 驗證、未解問題與下一步

成功只表示方法驗證：PHYSICAL_COMBINED_LIKELIHOOD=BLOCKED_OVERLAP_AND_CALIBRATION；PHYSICAL_SIGNIFICANCE、PHYSICAL_CLs_LIMIT與PHYSICAL_KAPPA_INTERVAL均NOT_EVALUATED，禁止discovery claim。未來實際templates須補overlap、fake、物理normalization、official calibration與nuisance correlations後另審physical gate；本次不解除gate。
