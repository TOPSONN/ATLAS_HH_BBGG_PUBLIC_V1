# Phase 6B HepMC3 validation

驗證分為 portable ASCII/source-integrity parser 與真正安裝 library 的獨立 physical readback。Python report 明示 `physical_library_readback=NOT_EVALUATED_BY_PYTHON`；只有 C++ `HepMC3::ReaderAscii` 配合實際 Pythia `ParticleData` 完成的 readback 才屬於 library physics evidence。安裝為 Pythia8.317、HepMC3 release3.3.1；HepMC3 API 顯示字串 `3.03.01`，保留原值並以 numeric components 正規化版本，沒有把不同 release 混為同一版本。

portable validator 支援 plain ASCII 與 gzip，stream 一個 raw event block，驗證完整 envelope/newlines、gzip CRC、GeV/mm、events/counts、finite fields/weights、statuses、明示與 implicit vertices、endpoints、acyclic beam-reachable graph、完整 beam→stable p4 closure、無 stable free quark/gluon/diquark、source identities、ledger→original indexed LHE/hash/weight 對應。event hash 使用 E line 至下一個 E line/footer 前的 exact bytes，不重寫四向量或重新序列化 reference。公開 gzip 要求 deterministic mtime0/no filename，並核對 compressed、decompressed 與 event-content SHA256。

獨立 C++ validator 使用官方 `ReaderAscii` 讀回實際 output，從真正安裝的 ParticleData 識別 PDGs、charge、hadron/quark/gluon/diquark/color type；只讀 particle database，不呼叫 Pythia event generation。檢查每個 particle/vertex owner、互相一致 endpoints、finite p4/mass/positions、status、完整2個6500 GeV proton beams、reachable DAG、stable endpoint、全事件 electric charge 與 p4 conservation。global sum 是 full proton beams 對所有 status1 stable particles，包含 beam remnants、neutrinos，排除 intermediate records。

| Strict numerical gate | Definition |
|---|---|
| Beam→stable p4 | 每 component `abs(delta) <= 1e-5 GeV + 1e-9*E_beams`，13 TeV 為2.3e-5 GeV |
| Stable mass shell | `abs(E^2-px^2-py^2-pz^2-m_generated^2) <= 1e-7 GeV^2 + 1e-9*max(E^2,1 GeV^2)` |
| Charge | 使用 installed ParticleData integer charge×3；full stable sum 必須等於 full proton beam sum6 |
| Hadronization completion | 無任何 stable `ParticleData.colType!=0` object；另外列出 stable free quark/gluon/diquark counts，不過濾這些粒子 |

intermediate shower/hadron records 可以 off shell，stable mass-shell gate不套用所有 intermediates。WriterAscii::set_precision(17) 與雙精度 cancellation 用明確 absolute/relative bound 處理；超出此 bound 不會因 Pythia `next()` 回傳true而獲准。

C++ report 即使失敗仍保存 input SHA、`N_readback`、`N_passed_validation`、`N_failed_validation`（events）、`N_not_assessed`、complete-assessment count、actual maxima、bounded per-event failure details 和 total failure counters。mass-shell failure 會檢查該 event 的全部 stable particles，繼續讀其他 immutable records，最後回傳nonzero。詳細內容最多64筆，truncation旗標及總數另存；不會以截斷 detail list 改變 failure count。graph/metadata check中止單一event時，partial distributions排除，已觀察的 residual maxima保存且report scope明示。

heavy-hadron counts 為 inclusive `nQuarksInCode(pid,5/4)>0`，particle/antiparticle 對稱，B_c可同時進入b/c類別；all-record與stable分開。這些不是 reconstructed b tags 或「每個 B hadron皆直接來自hard b」的判斷。小型 actual ParticleData API test 覆蓋 ±511、±521、±411、±421、±541。photon origin另由raw mother graph診斷，排除beam hadron、包含hard photon self root、explicit hadron→decay-photon status/edge證據，保留 ambiguous ancestry，與 HepMC physics gate分開。

## Preserved actual collinear-OFF failure

舊診斷 card `diagnostic_collinear_disabled.cmnd` SHA256 `a1e62fdaf6a6b487a1d9c696b87fa4ce9edec31c0b3b00dca5e985cba4ab7dd5`：bbgg100、seed610201、實際Pythia written100、next failures0；strict ReaderAscii 結果為 **FAIL**，readback100/pass99/failed1/not_assessed0。全部15324個stable particles中，event54有3個超界；input、output與ledger皆保留，沒有重寫、刪除或替換任何event。

| Source/output event | HepMC particle ID / raw Pythia index | PDG | Residual [GeV²] | Strict tolerance [GeV²] | E−sqrt(p²+m²) [GeV] |
|---|---|---:|---:|---:|---:|
| 54 | 244 / 491 | 22 | 0.00154298339839 | 0.0000165428916094 | 0.00000601647576559 |
| 54 | 245 / 492 | 22 | 0.0285564315855 | 0.000304659181776 | 0.0000258724826381 |
| 54 | 246 / 436 | 310 | 0.0433752719673 | 0.00983071310330 | 0.00000691706600264 |

worst residual/tolerance 為93.7324，beam→stable max residual仍為9.33478198e-7 GeV。photons 來自高度 boosted beam-remnant mini-string π0，K_S繼承同 string K0 的p4。raw Pythia p4與HepMC p4一致，50-digit decimal computation確認失配存在於generator record，不是ASCII列印造成。

Pinned Pythia source `StringRegion::setUp` 在兩個完全collinear remnant partons的double precision計算得到負的 light-cone energy，提前以 empty region返回，尚未建立transverse basis；`MiniStringFragmentation::ministring2two`後續仍由該region建立hadrons。重現 numerical branch 的API test使用已觀察的parton vectors，不生成physics events。來源為官方8.317 commit `83a5c9986f30746cfb390435a9b10ac55a758fca` 的 `FragmentationSystems.cc:578–585`、`MiniStringFragmentation.cc:456–490`。

官方 `Pythia::check` 使用另一個metric `abs(mCalc-m)/max(1 GeV,E)`，預設warn1e-4/error1e-3。兩個photons為約3.063e-4、π0 parent亦達warning，故Pythia log有3個「not quite matched」警告而 `next()`仍成功；K_S為1.334e-5。這個native非fatal門檻只記錄為診斷，**不取代 strict QA、不放寬 tolerance**。原始10-eventprefix的獨立readback PASS，不能推出100-eventextension PASS。

批准的v2使用stock primordial-kT remnant/recoil模型ON，card SHA256 `53ab239a091b179abce8db5d6905a279884c47a0286a422c059265460ec33389`。它是新的physical設定，需用原始相同inputs/seeds重新完成staged testing；不修補上述failed records。publication gate literal-pin v2 card，拒絕舊diagnostic card。

## Actual final v2 execution

已實際執行完整Phase6B portable suite **56/56 PASS、zero skips**，含9 streaming-LHE tests、20 portable-HepMC tests，使用真實公開prefix與full1000 source ledgers；adversarial copies僅供拒絕／signed serialization API測試。compiled CTests **5/5 PASS**。新版v2 Stage A bbgg10、Stage B每process100、Stage C每process1000均實際PASS，consumed/written/readback一致，全部shower/source/physical failures0。post-freeze portable readback再次實際讀完全部Stage C3000個events，逐event source/ledger與全部weights/accounting PASS。舊10prefixPASS、舊100FAIL的診斷結果仍保留，strict tolerances未改。

| Actual full1000 profile / seed | Max beam→stable component residual [GeV] | Max stable shell residual [GeV²] | Max shell/tolerance | Stable colored / failed physics events |
|---|---:|---:|---:|---|
| bbgg / 610201 | 7.69606823195e-6 | 2.39746020814e-8 | 0.000118799121 | 0 / 0 |
| ccgg / 610202 | 8.37606175619e-6 | 2.35910915247e-8 | 0.00420630642644 | 0 / 0 |
| light-jjgg / 610203 | 9.68320252624e-6 | 2.66545195915e-8 | 0.000640338401568 | 0 / 0 |

數字來自各process實際 `physical_validation.json`，由original source hash/run ID/seed/full decompressed file hash绑定，不把partial或其他run的report當成final evidence。所有intermediate vertices/particles保留，無事件修補或過濾。

公開reference必須由valid full1000 run取exact raw100-eventprefix，保留selected ledger與完整1000 ledger的原始行，sourcehash/cardhash/full-file C++report也須對應。若full output因size budget留在local，portable CI可以驗證selected物理bytes、exact full-ledger prefix membership與source correspondence，不能自行重新讀取未公開的full1000 physics bytes；full1000物理證據由file-bound真正ReaderAscii report提供，這項限制明示於manifest。Delphes actual runtime尚未評估，HepMC3 library-format readiness不等於detector simulation驗證。
