# Phase6G 固定探索性 cutflow

選擇維持 Phase6C：≥2 photons，各 pT>25 GeV、|eta|<2.37、排除1.37<|eta|<1.52、leading pT>35；≥2 jets pT>25 GeV、|eta|<2.5；≥2 native bit0 tags；105≤mγγ≤160 GeV。沒有以 pilot 最佳化 cuts，缺少 photon/tagged pair時 mass/DeltaR為null。

## B04

| Stage | Raw /1000 | Acceptance | Wilson95 interval | Source sum (pb) | Source sum2 (pb²) | MC sampling SE (pb) | MODEL_BR_ONLY sum (pb) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 00_input | 1000 | 1 | [0.996173241514, 1] | 0.089538 | 8.017053444e-06 | 0 | 0.00020562682086 |
| 01_photons | 370 | 0.37 | [0.340626675334, 0.400368281872] | 0.03312906 | 2.96630977428e-06 | 0.00136771554192 | 7.60819237183e-05 |
| 02_jets | 220 | 0.22 | [0.195423493389, 0.246719491363] | 0.01969836 | 1.76375175768e-06 | 0.00117350052171 | 4.52379005892e-05 |
| 03_two_btags | 77 | 0.077 | [0.0620479070606, 0.0951895306182] | 0.006894426 | 6.17313115188e-07 | 0.000755215436597 | 1.58332652062e-05 |
| 04_mgg_105_160 | 75 | 0.075 | [0.0602518049735, 0.0930009397393] | 0.00671535 | 6.012790083e-07 | 0.00074615 | 1.54220115645e-05 |

## B05

| Stage | Raw /1000 | Acceptance | Wilson95 interval | Source sum (pb) | Source sum2 (pb²) | MC sampling SE (pb) | MODEL_BR_ONLY sum (pb) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 00_input | 1000 | 1 | [0.996173241514, 1] | 0.399182 | 0.000159346269124 | 0 | 0.000917139320454 |
| 01_photons | 327 | 0.327 | [0.298634510389, 0.356689548047] | 0.130532514 | 5.21062300035e-05 | 0.005924744331 | 0.000299904557788 |
| 02_jets | 322 | 0.322 | [0.293769113817, 0.351593212204] | 0.128536604 | 5.13094986579e-05 | 0.00590107301707 | 0.000295318861186 |
| 03_two_btags | 131 | 0.131 | [0.111492506202, 0.15333164156] | 0.052292842 | 2.08743612552e-05 | 0.00426121789031 | 0.000120145250979 |
| 04_mgg_105_160 | 131 | 0.131 | [0.111492506202, 0.15333164156] | 0.052292842 | 2.08743612552e-05 | 0.00426121789031 | 0.000120145250979 |

## B06

| Stage | Raw /1000 | Acceptance | Wilson95 interval | Source sum (pb) | Source sum2 (pb²) | MC sampling SE (pb) | MODEL_BR_ONLY sum (pb) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 00_input | 1000 | 1 | [0.996173241514, 1] | 65.883086 | 4.34058102088 | 0 | NOT_APPLICABLE |
| 01_photons | 2 | 0.002 | [0.000548643588121, 0.00726280786349] | 0.131766172 | 0.00868116204177 | 0.0931261090665 | NOT_APPLICABLE |
| 02_jets | 2 | 0.002 | [0.000548643588121, 0.00726280786349] | 0.131766172 | 0.00868116204177 | 0.0931261090665 | NOT_APPLICABLE |
| 03_two_btags | 2 | 0.002 | [0.000548643588121, 0.00726280786349] | 0.131766172 | 0.00868116204177 | 0.0931261090665 | NOT_APPLICABLE |
| 04_mgg_105_160 | 0 | 0 | [0, 0.00382675848556] | 0 | 0 | 0 | NOT_APPLICABLE |
| control_00_input | 1000 | 1 | [0.996173241514, 1] | 65.883086 | 4.34058102088 | 0 | NOT_APPLICABLE |
| control_01_one_photon | 450 | 0.45 | [0.419415384074, 0.480967291774] | 29.6473887 | 1.9532614594 | 1.03700008285 | NOT_APPLICABLE |
| control_02_jets | 410 | 0.41 | [0.379917257646, 0.440771558881] | 27.01206526 | 1.77963821856 | 1.02520124197 | NOT_APPLICABLE |
| control_03_two_btags | 147 | 0.147 | [0.126403958552, 0.170297732939] | 9.684813642 | 0.63806541007 | 0.738115579973 | NOT_APPLICABLE |

Generator integration uncertainty 單獨列示。Sampling SE 用原始1000含 rejected events 的零 contributions，variance = N/(N−1) [Σcᵢ²−(Σcᵢ)²/N]；包含本次已實現的 detector/tag stream。Tag-sampling variance 未獨立量測，沒有額外 tag redraw；nested stages共享同source event，其不確定性不能當成獨立相加。

零 survivor 的 plugin SE=0 不是零背景證據；另外記錄 Wilson95與 exact one-sided95 upper =1−0.05^(1/1000)。

B06 04_mgg_105_160 zero-survivor upper95 = `0.0029912495451`。

對實測等權且非負 source，另外提供條件式 source-weight upper，固定此 pilot source weight、integration error另列，不建立 calibrated physical fake/background上限：

| Process | Zero-survivor stage | Acceptance upper95 | Conditional source upper (pb) | Conditional MODEL_BR_ONLY upper (pb) |
| --- | --- | --- | --- | --- |
| B06 | 04_mgg_105_160 | 0.002991249545095296 | 0.197072751026974264563456 | NOT_APPLICABLE |

B06 one-photon control各stage與diphoton結果都保留；其 diphoton yield 的 jet fake interpretation為BLOCKED。無官方 detector/BR/PDF/scale systematics、luminosity、combined background或discovery significance。
