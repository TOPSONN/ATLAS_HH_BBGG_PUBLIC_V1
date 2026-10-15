# B06 實際 1000-event 鏈

目前狀態：`PASS_FULL_CHAIN_MODEL_SCOPE`。實際 source / validated HepMC / validated ROOT 為 1000 / 1000 / 1000；完整物理資料鏈 PASS = `True`。

| 項目 | 實測或凍結設定 |
| --- | --- |
| Hard process | `generate p p > b b~ a j4 QCD=3 QED=1` |
| 模型/PDF | sm-no_b_mass；5F massless b/c；內建 CTEQ6L1 LO |
| 碰撞能量 | 13000 GeV；兩束各6500 GeV |
| muR=muF (GeV) | 125.0 |
| Source cross section (pb) | 65.88309 |
| MG5 integration uncertainty (pb) | 0.3918004 |
| Seeds MG5/Pythia/Delphes | 20261106/610403/610503 |
| 完整原始 denominator | 1000 |
| Unique independent source streams | 1 |

Fixed muR=muF=125 GeV retained continuum-study pilot convention. Selected finite LO component; no precision physical prediction or scale uncertainty claimed.

實際 amplitude/card gate：`{"receipt_sha256": "9bbc04ee75b1d5ec7f205c77aca954bb2ae3900d14eca1710bb6aa4e3f41c9c4", "records": 14, "production_records": 14, "Z_decay_records": 0, "diagram_sum": 386, "orders_by_scope": {"production": [{"QCD": 3, "QED": 1}]}, "actual_parameters": {"mdl_MZ": 91.188, "mdl_MH": 125.0, "mdl_MT": 173.0, "mdl_WZ": 2.441404, "mdl_WH": 0.00638233934, "mdl_WT": 1.4915, "mdl_WW": 2.0476, "mdl_ymt": 173.0, "aEWM1": 132.507, "mdl_Gf": 1.16639e-05, "aS": 0.129783}}`。Initial/header/post-working-card/final internal seeds分開記錄：`{"initial_request": 20261106, "effective_header": 20261106, "post_run_working_card_iseed": 0, "final_internal_randinit": "r=20261112", "scope": "Different stages: MG5 working-card reset after reading seed and internal integration increments are administrative, not additional source streams"}`。

[Independent actual full1000 source proof](../simulation/new_backgrounds/evidence/bbgj_actual_lhe_independent.json)（SHA256 `bd02907891a8702106e9083dfe411dd6b80e97199061d3433a8fc6744aca9088`）另外以Decimal檢查完整source kinematics、mothers、colour/charge、Born topology、weights/cards与seed stages，0新MC。

實測cut extrema：`{"maximum_absolute_eta": {"b": 2.498276770800646, "j4": 2.496320976693997, "photon": 2.4982570601144856}, "minimum_all_final_pair_dr": 0.4000174621260225, "minimum_pt_gev": {"b": 25.015080434118282, "j4": 25.054968626689057, "photon": 25.030875791478955}}`；original final j4 PDG counts：`{"-1": 31, "-2": 67, "-3": 21, "-4": 38, "1": 60, "2": 214, "21": 493, "3": 19, "4": 57}`；event alpha_s tokens：`{"1.23806200e-01": 1000}`。

Born topology 只有一顆 prompt photon、兩個 b partons、一個允許 j4。所有 b/bbar/j4/a pT≥25 GeV、|eta|≤2.5、所有 relevant pair DeltaR≥0.4；ptgmin=0、maxjetflavor=4 是 b/ordinary-jet cut classification，proton/PDF 仍是5F。第二個 reconstructed Photon 不建立 calibrated jet fake rate；沒有人工 jet→photon 替換。

實際完整驗證 receipts 與樣本 hashes：

| Role | Events/Scope | SHA256 | Bytes |
| --- | --- | --- | --- |
| genuine_source_LHE_GZ_1000 | 1000 | `4203eb46258973ffc3870802b4d58c27d3275845309b28c7cda600ea343e52f5` | 171154 |
| full1000_HepMC3_ASCII | 1000 | `511eb6ea2bbdd053024b900b716cd433144d9e8f9f2d4677712cba88728d562a` | 146589922 |
| full1000_HepMC3_GZ | 1000 | `424889d88526b7c421514b479e9ab497443a899ff9b4c594f6a81945afe5ab29` | 39966986 |
| full1000_Delphes_ROOT | 1000 | `eb989481afb06c500b8c0144e2a32fe68aa39f14c1000edd347d4d6897e1e6de` | 36916961 |
| closed_run_manifest | complete bound receipt | `8933bca3b2a821d4f679382d81a27db5fa55b5aebcd5f197db290042175c35ff` | 258832 |
| complete_LHE_validation | complete bound receipt | `64347f5a161f95824aae7f87ee2e657fa3049c9ae4ce442f1b56fc99fb8dbae1` | 4456324 |
| actual_MG5_banner | complete bound receipt | `c43262c143f76547ba807a993147dc7f2bf62dbe6a2ab2207f27cdf1dd92bc14` | 26539 |
| actual_MG5_run_log | complete bound receipt | `bcbcbbf665c162ccc40ddad4da4af11293daeac80b768d2382a34c7833b45463` | 12183 |
| independent_actual_full1000_source_kinematics_cards | complete bound receipt | `bd02907891a8702106e9083dfe411dd6b80e97199061d3433a8fc6744aca9088` | 12076 |
| native_full_HepMC_reader | complete bound receipt | `e07d804e2e164ca4ffea49cddd719e49e5311a80e8ad7d78badabf0d35898fc0` | 2139 |
| actual_full_shower_summary | complete bound receipt | `b5f1f69a66638bff357aed3eabdaafa8d8087565c9f9a5b188be1a4505957242` | 3880 |
| full1000_input_index | complete bound receipt | `07561c639b9328df58c1c2efe54d848c14b16444f14a8d0b8f1278690a2f7056` | 72148612 |
| full1000_truth_index | complete bound receipt | `0963ac1a6d22a523773940d8c425b6e7683af08981f7147de09581e83a118090` | 426189 |
| all_event_BR_weight_closure | complete bound receipt | `e474e93c741e837f74cbd8d349ea360a04fd7c4c247d5d01cc0dd919a02bc161` | 4053 |
| full1000_reco_events | complete bound receipt | `b894f1a5ff2c6e2e6424f8db232e936fdf8b72b598df69bc5adfe1b94f0ab410` | 1242668 |
| full1000_native_cutflow | complete bound receipt | `d06b38c51fd0e92b461652b20e870ba3a59a9f9d2732ce29ae144a5854b5d11c` | 549 |
| independent_full1000_statistics | complete bound receipt | `bf60d1a0e78cd1806502908a54abf802dcf5c70208055eee3e7567c5c2363679` | 7765 |
| independent_actual_ROOT_and_statistics | complete bound receipt | `79511c684afa7216a8762fa096a0c05754b4a259249212852f55602a521f54f3` | 7859 |
| independent_all1000_raw_and_model_weight_closure | complete bound receipt | `2f8f1caae9e873cecdf5fc223d7c4bc57cd23d22cc834991a95ac675b507dafd` | 2080 |

實際 ancestry 計數：

```json
{
  "higgs_two_photon_birth_events": 0,
  "source_Z_bottom_birth_events": 0,
  "top_W_model_decay_events": 0,
  "one_Born_photon_identity_events": 1000,
  "stable_photon_origin_counts": {
    "born_prompt": 1000,
    "shower_radiation": 55,
    "hadron_decay": 91080,
    "other": 0
  },
  "top_decay_quark_pdg_counts": {},
  "W_birth_product_pdg_counts": {},
  "H_final_photon_multiplicity_histogram": {
    "0": 1000
  },
  "top_W_decay_scope": "inclusive supported Pythia model; production-decay spin correlations unvalidated"
}
```

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

實際重建變數診斷（有定義事件的線性插值 quantiles；PT/mass為GeV）：

| Variable | Defined/null | q16 | q50 | q84 |
| --- | --- | --- | --- | --- |
| photon_multiplicity | 1000/0 | 0 | 1 | 1 |
| jet_multiplicity | 1000/0 | 2 | 3 | 5 |
| tagged_bit0 | 1000/0 | 0 | 1 | 2 |
| pT_gamma1 | 699/301 | 30.0548552704 | 43.5316925049 | 77.7872302246 |
| pT_gamma2 | 4/996 | 15.0513054657 | 23.5574197769 | 34.258561554 |
| pT_jet1 | 997/3 | 45.8570553589 | 77.8146286011 | 134.989529419 |
| pT_jet2 | 955/45 | 34.3599783325 | 53.3104820251 | 92.5129345703 |
| m_gamma_gamma | 2/998 | 47.7956565633 | 57.7912336683 | 67.7868107732 |
| m_jj | 930/70 | 81.9242323209 | 152.016487354 | 303.95622183 |
| m_bb | 335/665 | 50.5157341499 | 102.453620102 | 221.7005952 |
| m_bb_gamma_gamma | 2/998 | 211.385114546 | 230.47229033 | 249.559466114 |
| DeltaR_gamma_gamma | 2/998 | 1.19787535307 | 1.62683337753 | 2.05579140199 |
| DeltaR_bb | 335/665 | 0.925060989895 | 2.44385252166 | 3.18784995454 |

H-origin reconstructed match multiplicity histogram：`{"0": 1000}`；與 inclusive selected diphoton pair 分開，不把geometricmatch當作calibrated效率。

Raw/source 與 MODEL_BR_ONLY sums 分別保存在 [weight accounting](../metadata/phase6g_weight_accounting.json)。無 implicit luminosity、無 HH factor2、無第二次 sigma/N。未取得官方 calibration 或 validated overlap，不能把這些 streams 相加解釋成完整物理背景。
