# Phase8K Systematics readiness

## 目標與實際輸入

以本次八個完整既有樣本、固定selection、source provenance、MC variance及shared-source κ covariance盤點模型缺口。這份表只記錄readiness，沒有把toy或未知數值設為ATLAS官方不確定度。

## 方法與數值政策

未知physical value、constraint與correlation model皆為null，不以0取代。finite-MC採actual original-N事件統計，conditional tag variance單列；兩者不相加到已實現的observed outcome variance。historical generator integration error另列，未與未知相關的量做總quadrature。RooFit Gaussian/lognormal/shape/MC-stat nuisance只使用synthetic fixtures，不能填補physical calibration。

## 實際22個類別

| Nuisance | Method type | Availability | Readiness |
|---|---|---|---|
| luminosity | LOGNORMAL | UNKNOWN | UNKNOWN_EXTERNAL_CALIBRATION_REQUIRED |
| photon_ID | LOGNORMAL | UNKNOWN | UNKNOWN_EXTERNAL_CALIBRATION_REQUIRED |
| photon_trigger | LOGNORMAL | UNKNOWN | UNKNOWN_EXTERNAL_CALIBRATION_REQUIRED |
| photon_energy_scale | SHAPE | UNKNOWN | UNKNOWN_EXTERNAL_CALIBRATION_REQUIRED |
| photon_energy_resolution | SHAPE | UNKNOWN | UNKNOWN_EXTERNAL_CALIBRATION_REQUIRED |
| JES | SHAPE | UNKNOWN | UNKNOWN_EXTERNAL_CALIBRATION_REQUIRED |
| JER | SHAPE | UNKNOWN | UNKNOWN_EXTERNAL_CALIBRATION_REQUIRED |
| b_tag_efficiency | SHAPE_AND_RATE | UNKNOWN | UNKNOWN_EXTERNAL_CALIBRATION_REQUIRED |
| light_mistag | SHAPE_AND_RATE | UNKNOWN | UNKNOWN_EXTERNAL_CALIBRATION_REQUIRED |
| charm_mistag | SHAPE_AND_RATE | UNKNOWN | UNKNOWN_EXTERNAL_CALIBRATION_REQUIRED |
| pileup | SHAPE_AND_RATE | UNKNOWN | UNKNOWN_EXTERNAL_CALIBRATION_REQUIRED |
| PDF | CORRELATED_VARIATION | UNKNOWN | UNKNOWN_EXTERNAL_CALIBRATION_REQUIRED |
| muR | SCALE_VARIATION | UNKNOWN | UNKNOWN_EXTERNAL_CALIBRATION_REQUIRED |
| muF | SCALE_VARIATION | UNKNOWN | UNKNOWN_EXTERNAL_CALIBRATION_REQUIRED |
| generator_model | ALTERNATIVE_MODEL | UNKNOWN | UNKNOWN_EXTERNAL_CALIBRATION_REQUIRED |
| parton_shower | ALTERNATIVE_MODEL | UNKNOWN | UNKNOWN_EXTERNAL_CALIBRATION_REQUIRED |
| Higgs_BR | CORRELATED_RATE | UNKNOWN | UNKNOWN_EXTERNAL_CALIBRATION_REQUIRED |
| background_normalization | CONSTRAINED_RATE | UNKNOWN | UNKNOWN_EXTERNAL_CALIBRATION_REQUIRED |
| heavy_flavour_overlap | DEFINITION_GATE | UNKNOWN | BLOCKED_OVERLAP_DEFINITION |
| photon_fake | CALIBRATED_TRANSFER_MODEL | UNKNOWN | BLOCKED_MISSING_FAKE_CALIBRATION |
| finite_MC_statistics | EVENT_COVARIANCE | METHOD_ONLY | COMPUTED_EVENT_DIAGNOSTICS_NOT_OFFICIAL_NUISANCE |
| kappa_support | SOURCE_SUPPORT_GATE | METHOD_ONLY | BLOCKED_LOW_SUPPORT_2_5_5 |

所有physical uncertainty數值目前均未提供；這不表示所有來源物理量未知。歷史Higgs model BR數值已綁定並套用一次，但其校準uncertainty與correlations尚未驗證。PDF與alpha_s有效設定、現有MC moments及κ權重來源均已驗證；它們不能直接代替跨模型系統學。

## 驗證與統計限制

Source contract與負測試要求unknown維持null，禁止用method-only nuisance通過physical template gate。template manifest保存dataset、source SHA、region、observable、edges、flow-inclusive bin contents/Sumw2、normalization與validation scopes；signed或negative expectation不被剪成可擬合的正值。

## 未解決項目與下一步

lumi/photon/jet/tag/pileup calibration、PDF/scale/generator/shower variations、BR correlations、background normalization與fake control data均需要獨立校準來源。B01/B02/B03的ME/PS heavy-flavour overlap定義仍未解決；B06缺少calibrated fake transfer；κλ=2.5、5支持不足。這些gate持續阻止physical combined likelihood、significance、CLs及κλ limit。
