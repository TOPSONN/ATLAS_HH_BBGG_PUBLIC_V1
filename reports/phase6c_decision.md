# Phase 6C decision and acceptance

實際 Delphes → ROOT 自助流程已完成 10、100 與 1000-event 驗收；全部最終工作沒有遺失或跳過事件。三個 1000-event 程序各有自己的 LO 正規化，統計僅使用 Stage C，未把重複的 A/B/重現測試相加。

這是 FAST_SIM_ATLAS_LIKE / NOT_OFFICIAL_ATLAS 方法研究；不提供官方 detector/b-tag 校正、完整背景、HH 敏感度或 NLO matched 生成結論。

## Required final fields

| Field | Result |
|---|---|
| PROJECT | ATLAS_HH_BBGG_PUBLIC_V1 |
| TASK | PHASE6C_DELPHES_FAST_SIM_AND_ROOT_ANALYSIS_V1 |
| STATUS | LOCAL_PASS_REMOTE_NOT_EVALUATED |
| DELPHES_INSTALLED | YES; isolated user-owned WSL prefix |
| DELPHES_VERSION | 3.5.1 |
| DELPHES_SOURCE | official tag3.5.1 /28658365abeb71ee36dfc739f9670c1514c0cb10; archiveb60d26d2ee2c84b58fbf2cf397fabd0ef3e89d3a0546d843c4ada82cc802d787 |
| ROOT_VERSION | 6.40.04 |
| CPP_STANDARD | 20 |
| DETECTOR_CARD | simulation/delphes/cards/atlas_like_bbgg_baseline.tcl |
| DETECTOR_CARD_SHA256 | cd91fc7982365af23e4002c6295418fbbc0077ffe381e992e7e6070052eb1f47 |
| BBGG_INPUT | existing Phase6B1000 HepMC3, checksum/ReaderAscii/sourceledger PASS |
| BBGG_OUTPUT | 1000 ROOTentries local; 100 actual input/referenceentries selected |
| CCGG_INPUT | existing Phase6B1000 HepMC3, checksum/ReaderAscii/sourceledger PASS |
| CCGG_OUTPUT | 1000 ROOTentries local; 100 actual input/referenceentries selected |
| JJGG_INPUT | existing Phase6B1000 HepMC3, checksum/ReaderAscii/sourceledger PASS |
| JJGG_OUTPUT | 1000 ROOTentries local; 100 actual input/referenceentries selected |
| ROOT_SCHEMA | PASS; Delphes TTree,16 actualTClonesArray branches, real compatible dictionaries/streamers; separate adapter |
| PHOTON_RECONSTRUCTION | PASS methods; explicit reconstruction acceptance/unique match/energy-residual diagnostics, not calibrated efficiency |
| JET_RECONSTRUCTION | PASS methods; independent stable-visible FastJet anti-kT R0.4 vs nativeGenJet, unique reco matching |
| BTAG_MODEL | PASS exact study Flavor/cone/bit0/probability semantics; insufficient-category flags retained; no calibratedATLAS claim |
| TRUTH_MATCHING | PASS explicit one-to-one photonDR<0.2/jetDR<0.3; ancestry source sidecars; distinct terminal heavy-hadron diagnostics |
| BBGG_CUTFLOW | 1000 →446 →266 →91 →28 |
| CCGG_CUTFLOW | 1000 →378 →241 →7 →1 |
| JJGG_CUTFLOW | 1000 →445 →277 →0 →0 |
| BTAG_EFFICIENCY | bbgg Flavor5:894/1373=65.11%; Wilson95 62.55–67.59%, descriptive |
| CHARM_MISTAG | ccgg Flavor4:189/1514=12.48%; Wilson95 10.91–14.24%, descriptive |
| LIGHT_MISTAG | jjgg light:10/2130=0.4695%; Wilson95 0.2552–0.8621%, descriptive; expected5.3686tags, standardizedresidual+2.0015 |
| M_GAMMAGAMMA | PASS stable Cartesian pair; selected fiducial photons; no peak fit |
| M_JJ | PASS selected leading inclusive jet pair, independently distinct from taggedpair |
| M_BB | PASS selected leading two bit0-tagged jets; null when unavailable |
| M_BBGAMMAGAMMA | PASS summed selected taggedjet+photonpairs; null when unavailable |
| WEIGHT_ACCOUNTING | PASS raw signed source contributions/full original1000denominator, named highprecision sidecar; separateσ .06624666/.6274417/9.436556pb, raw sums retain generator digits; no luminosity |
| LOCAL_TESTS | 59MG5+56PythiaPython+5PythiaCPP+31HepMC+27DelphesPython+8nativefailure+1analyticCTest PASS;7 independentPyROOT readbacks; guide recheck and activatedshell dryrun PASS; CI25Python/10explicitSKIP distinct local35discovered/8SKIP |
| GITHUB_CI | NOT_EVALUATED pending actual GitHub runs |
| GITHUB_SAMPLES | 3 localprepared100-entry ROOTreferences; remote NOT_EVALUATED |
| GATES_PASS | A,B,C,D,E,F,G,H,I,J |
| GATES_FAIL | NONE |
| GATES_BLOCKED | NONE |
| GATES_UNKNOWN | NONE; remote NOT_EVALUATED if notsealed |
| COMMIT_HASH | PENDING; remote evidence commit is a bounded snapshot; subsequent finalhead verified separately |
| PR_URL | PENDING stackedDraftPR base codex/phase6b-pythia8-shower-1k |
| FINAL_VERDICT | LOCAL_METHODS_PASS_REMOTE_PENDING |
| NEXT_RECOMMENDED_STEP | Review the DraftPR/card/uncertainties, then design an independently justified larger-statistics/systematics study; no automatic merge or generation expansion |

## Evidence and scientific limits

首次 A10 的 ROOT 含 10 筆有效輸出，但早期分析器於第3筆事件遇到第一個極小負 signed mass而停止：讀回3、成功評估2、invalid1、尚未評估7。後續完整讀回找到兩個 double 捨入造成的負 mass物件（1 reco Jet及1 GenJet）。原始失敗 ROOT/計數保持本機不變；新分析器保留 native Mass 與 ROOT 的 signed convention，僅在明確 `16*double epsilon*p²` 界線內接受，並拒絕真正 material spacelike 值。對同一檔案重新原生分析通過，更新後的完整命令也實際通過。

最終命令重複 10 筆的科學內容 SHA 完全一致；三個 Stage B100 的科學內容也等於各自 C1000 前100筆。ROOT UUID/時間使二進位 hashes 不同，沒有宣稱 binary ROOT bitwise reproduction。

jjgg light tag 的觀察值約高於條件預期 2.0015 個模型標準差，保留這項 fluctuation；小樣本、同事件相關性與 detector/card 系統誤差沒有被當作已校準性能。低統計 flavour/bin 以 INSUFFICIENT_STATISTICS 註明。零個最終 jjgg 事件不代表物理背景為零。

公開 reference ROOT 合計9,086,356bytes；三個逐粒子 input index 合計22,100,897bytes，為核對 native Float_t與完整來源而保留，採明確10MiB/檔、30MiB合計的獨立sidecar cap；其他metadata仍5MiB/檔。沒有 full1000ROOT、generatorbinary/sourcevendor或新PDF/PNG。

來源／原生證據：[inputmanifest](../metadata/phase6c_input_manifest.json)、[detector manifest](../metadata/phase6c_detector_manifest.json)、[qualitygates](../metadata/phase6c_quality_gates.json)、[native runs](../simulation/delphes/evidence/native_runs.json)、[independent readback](../simulation/delphes/evidence/independent_readback.json)、[reproducibility](../simulation/delphes/evidence/reproducibility.json)、[initialfailure](../simulation/delphes/evidence/stage_a_initial_failure.json)。

操作入口：[run_delphes.sh](../simulation/delphes/scripts/run_delphes.sh)；[繁體中文指南](../simulation/delphes/USER_GUIDE_ZH_TW.md)。既有 ROOT readers、MG5/Pythia source/references及歷史報告保持原本 Git blob 身分；PR9保持OPEN/ready，PR11/12保持OPEN/DRAFT，未merge或forcepush。

## Available-pair mass diagnostics

| Process | Observable | Available pairs | Mean (GeV) | Range (GeV) |
|---|---|---:|---:|---|
| bbgg | m_gamma_gamma | 484 | 127.963 | 17.8381–880.847 |
| bbgg | m_jj | 684 | 182.63 | 14.1256–1450.45 |
| bbgg | m_bb | 215 | 156.886 | 17.9875–756.736 |
| bbgg | m_bb_gamma_gamma | 98 | 389.183 | 140.086–1164.7 |
| ccgg | m_gamma_gamma | 417 | 111.732 | 19.6134–466.706 |
| ccgg | m_jj | 756 | 181.753 | 15.3215–1172.33 |
| ccgg | m_bb | 13 | 169.216 | 34.8818–613.703 |
| ccgg | m_bb_gamma_gamma | 7 | 448.603 | 342.668–770.83 |
| jjgg | m_gamma_gamma | 473 | 136.464 | 19.9051–873.344 |
| jjgg | m_jj | 716 | 204.511 | 17.4697–1606.9 |
| jjgg | m_bb | 4 | 206.723 | 54.1769–561.331 |
| jjgg | m_bb_gamma_gamma | 0 | N/A | N/A; insufficient eligible pairs |

Pairs use the documented object eligibility, before imposing the final event selection; these broad distributions are not resonance peak measurements.
