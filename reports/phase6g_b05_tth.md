# B05 實際 1000-event 鏈

目前狀態：`PASS_FULL_CHAIN_MODEL_SCOPE`。實際 source / validated HepMC / validated ROOT 為 1000 / 1000 / 1000；完整物理資料鏈 PASS = `True`。

| 項目 | 實測或凍結設定 |
| --- | --- |
| Hard process | `generate p p > t t~ h QCD=2 QED=1` |
| 模型/PDF | sm-no_b_mass；5F massless b/c；內建 CTEQ6L1 LO |
| 碰撞能量 | 13000 GeV；兩束各6500 GeV |
| muR=muF (GeV) | 235.5 |
| Source cross section (pb) | 0.3991820 |
| MG5 integration uncertainty (pb) | 0.001975393 |
| Seeds MG5/Pythia/Delphes | 20261105/610402/610502 |
| 完整原始 denominator | 1000 |
| Unique independent source streams | 1 |

Fixed muR=muF=(2*MT+MH)/2=MT+MH/2=235.5 GeV. A process-specific heavy associated-production threshold-half convention, not optimized and without scale-uncertainty claim.

實際 amplitude/card gate：`{"receipt_sha256": "32b95a0cabb8228790776d2b3502939d836369380c98412d57f8360125afa3bc", "records": 6, "production_records": 6, "Z_decay_records": 0, "diagram_sum": 18, "orders_by_scope": {"production": [{"QCD": 2, "QED": 1}]}, "actual_parameters": {"mdl_MZ": 91.188, "mdl_MH": 125.0, "mdl_MT": 173.0, "mdl_WZ": 2.441404, "mdl_WH": 0.00638233934, "mdl_WT": 1.4915, "mdl_WW": 2.0476, "mdl_ymt": 173.0, "aEWM1": 132.507, "mdl_Gf": 1.16639e-05, "aS": 0.129783}}`。Initial/header/post-working-card/final internal seeds分開記錄：`{"initial_request": 20261105, "effective_header": 20261105, "post_run_working_card_iseed": 0, "final_internal_randinit": "r=20261111", "scope": "Different stages: MG5 working-card reset after reading seed and internal integration increments are administrative, not additional source streams"}`。

[Independent actual full1000 source proof](../simulation/new_backgrounds/evidence/tth_actual_lhe_independent.json)（SHA256 `a546f1f2c7e1c861ceec7d4e1460f4b510d4bf906ddda59812f308317ca5873a`）另外以Decimal檢查完整source kinematics、mothers、colour/charge、Born topology、weights/cards与seed stages，0新MC。

實測cut extrema：`{"maximum_absolute_eta": {}, "minimum_all_final_pair_dr": null, "minimum_pt_gev": {}}`；original final j4 PDG counts：`{}`；event alpha_s tokens：`{"1.12994300e-01": 1000}`。

Source tops/H 皆穩定，MT=173 GeV、GammaT=1.4915 GeV、YUKAWA6=173 GeV；muR=muF=MT+MH/2=235.5 GeV。Installed MadSpin source 存在，但相容的 end-to-end inclusive route 尚未驗證，bounded pilot 採用已記錄的 Pythia supported inclusive top/W 衰變。Production-decay spin correlations 為 NOT_VALIDATED；CKM sW/dW channels 保留，不強制所有 top→bW，也不限制 W channels。

實際完整驗證 receipts 與樣本 hashes：

| Role | Events/Scope | SHA256 | Bytes |
| --- | --- | --- | --- |
| genuine_source_LHE_GZ_1000 | 1000 | `b4344e7ad8bd923460e936f728d3e3dd3a919d3ee0a3752b7b6ad6a7ed27aaa6` | 134068 |
| full1000_HepMC3_ASCII | 1000 | `524a47c8a87516c30ff01cf03e9097e68d0eff9aa74b39a3a1d502a9ec6f90e4` | 177575532 |
| full1000_HepMC3_GZ | 1000 | `ec42b1e1214d66e57ce6cc81dfd24749f52dbddc325b8a2aec0c8ce59f2b0cee` | 47253763 |
| full1000_Delphes_ROOT | 1000 | `388680cfd9901ae4c219654a47c4a720a988963ded8c3896b066d74a089b1f6e` | 45839687 |
| closed_run_manifest | complete bound receipt | `601490546cf98e4ab2551c48c4c75fa308b4dd9bf24666c71aa639d5ebe5387c` | 259903 |
| complete_LHE_validation | complete bound receipt | `0d745d50d1a5251c03d08cf7d3bee93bc987dce58b11ac74b9688937b922e889` | 3807816 |
| actual_MG5_banner | complete bound receipt | `16b6e049e06710795baee5b19c753320ac966f884c3c2a36f569c935a9b02c2b` | 26507 |
| actual_MG5_run_log | complete bound receipt | `d3f88a3dbac26a7cd5bdce4c9e0f282f6ad0b15e3cc6889ac7d4bfdb170f6f96` | 11780 |
| independent_actual_full1000_source_kinematics_cards | complete bound receipt | `a546f1f2c7e1c861ceec7d4e1460f4b510d4bf906ddda59812f308317ca5873a` | 7848 |
| native_full_HepMC_reader | complete bound receipt | `0ab7c2776d3bf04180c09a7d549e6bb8da02cf58087db244419d37b2caf5d70a` | 2350 |
| actual_full_shower_summary | complete bound receipt | `ea3355649a27a6133d0e3e243ea030d8aa6c18db04c24cbb6aa700bf5e991b64` | 3994 |
| full1000_input_index | complete bound receipt | `e26190118105cb664aa2f91279e997a9b1f939b56bf47d2cd2d4884b297922c0` | 93166637 |
| full1000_truth_index | complete bound receipt | `5ce457f2d210ae3ba5ffcd40744363323fb59f2796fff53c258b8645fbcfac8b` | 536626 |
| all_event_BR_weight_closure | complete bound receipt | `8ef615bb14bf15d19bd999df930b14f2c30f83bd6fd41c319ce26dae0c30ac87` | 4240 |
| full1000_reco_events | complete bound receipt | `f20484e45630450bb020fb118e3a96241f2ff7e80694046f9078e50e37e7b6e0` | 1436065 |
| full1000_native_cutflow | complete bound receipt | `062ab7653e30a13b7b44ada128ac8f33ca944916214f029a13fecc982b92bb5a` | 346 |
| independent_full1000_statistics | complete bound receipt | `08733f6776ff812052c14b58a1245b5ec13fd8330d784e557c86e1917990857d` | 6045 |
| independent_actual_ROOT_and_statistics | complete bound receipt | `0377079f50d42cde94076413a6cc1b486b8b8d4bfed1a5aa482d1dd329c7df14` | 5882 |
| independent_all1000_raw_and_model_weight_closure | complete bound receipt | `df439e10f5d851d1ff63afddcedc59a264d117ff5b5153a7092c21b74d8a34c4` | 7152 |

實際 ancestry 計數：

```json
{
  "higgs_two_photon_birth_events": 1000,
  "source_Z_bottom_birth_events": 0,
  "top_W_model_decay_events": 1000,
  "one_Born_photon_identity_events": 0,
  "stable_photon_origin_counts": {
    "born_prompt": 0,
    "shower_radiation": 677,
    "hadron_decay": 110676,
    "other": 2000
  },
  "top_decay_quark_pdg_counts": {
    "-5": 1000,
    "5": 1000
  },
  "W_birth_product_pdg_counts": {
    "-16": 108,
    "-15": 114,
    "-14": 97,
    "-13": 106,
    "-12": 116,
    "-11": 122,
    "-4": 326,
    "-3": 328,
    "-2": 353,
    "-1": 330,
    "1": 347,
    "2": 326,
    "3": 329,
    "4": 332,
    "5": 3,
    "11": 116,
    "12": 122,
    "13": 97,
    "14": 106,
    "15": 108,
    "16": 114
  },
  "H_final_photon_multiplicity_histogram": {
    "2": 1000
  },
  "top_W_decay_scope": "inclusive supported Pythia model; production-decay spin correlations unvalidated"
}
```

| Stage | Raw /1000 | Acceptance | Wilson95 interval | Source sum (pb) | Source sum2 (pb²) | MC sampling SE (pb) | MODEL_BR_ONLY sum (pb) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 00_input | 1000 | 1 | [0.996173241514, 1] | 0.399182 | 0.000159346269124 | 0 | 0.000917139320454 |
| 01_photons | 327 | 0.327 | [0.298634510389, 0.356689548047] | 0.130532514 | 5.21062300035e-05 | 0.005924744331 | 0.000299904557788 |
| 02_jets | 322 | 0.322 | [0.293769113817, 0.351593212204] | 0.128536604 | 5.13094986579e-05 | 0.00590107301707 | 0.000295318861186 |
| 03_two_btags | 131 | 0.131 | [0.111492506202, 0.15333164156] | 0.052292842 | 2.08743612552e-05 | 0.00426121789031 | 0.000120145250979 |
| 04_mgg_105_160 | 131 | 0.131 | [0.111492506202, 0.15333164156] | 0.052292842 | 2.08743612552e-05 | 0.00426121789031 | 0.000120145250979 |

實際重建變數診斷（有定義事件的線性插值 quantiles；PT/mass為GeV）：

| Variable | Defined/null | q16 | q50 | q84 |
| --- | --- | --- | --- | --- |
| photon_multiplicity | 1000/0 | 1 | 1 | 2 |
| jet_multiplicity | 1000/0 | 4 | 5 | 7 |
| tagged_bit0 | 1000/0 | 0 | 1 | 2 |
| pT_gamma1 | 889/111 | 53.2498959351 | 93.1514053345 | 170.733468018 |
| pT_gamma2 | 439/561 | 25.6620295715 | 49.1042671204 | 75.9193548584 |
| pT_jet1 | 1000/0 | 88.3752114868 | 140.261787415 | 222.107129517 |
| pT_jet2 | 997/3 | 62.0641094971 | 94.7817382812 | 153.579846191 |
| m_gamma_gamma | 328/672 | 123.691122786 | 125.002987625 | 126.171404596 |
| m_jj | 989/11 | 105.932604171 | 212.705870775 | 398.832584013 |
| m_bb | 386/614 | 94.2277548428 | 153.966464897 | 298.19498426 |
| m_bb_gamma_gamma | 131/869 | 273.377626637 | 410.555322926 | 615.723369417 |
| DeltaR_gamma_gamma | 328/672 | 1.13503636565 | 1.85956551782 | 2.78125489877 |
| DeltaR_bb | 386/614 | 1.35304985867 | 2.36754326131 | 3.09236827305 |

H-origin reconstructed match multiplicity histogram：`{"0": 114, "1": 459, "2": 427}`；與 inclusive selected diphoton pair 分開，不把geometricmatch當作calibrated效率。

Raw/source 與 MODEL_BR_ONLY sums 分別保存在 [weight accounting](../metadata/phase6g_weight_accounting.json)。無 implicit luminosity、無 HH factor2、無第二次 sigma/N。未取得官方 calibration 或 validated overlap，不能把這些 streams 相加解釋成完整物理背景。
