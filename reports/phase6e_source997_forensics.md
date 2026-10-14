# Phase 6E：light-jjgg source997 實體事件鑑識

**結論：這個既有事件的兩個原生 Flavor=5 jets，有明確的 final-state-shower `g → b bbar` 產生鏈。** 這項結論來自原始 Pythia 母女粒子關係、官方 status 定義、HepMC 圖與原生 ROOT 的交叉讀回，並非由 `Jet.Flavor=5` 推定。事件與所有歷史樣本保持原樣；未產生新 Monte Carlo、未重新執行 Delphes、未更換 tagging working point。

`source_event_index=997` 是 **one-based**：它是 LHE 第 997 個 `<event>`、ledger/source snapshot 第 997 個來源事件、HepMC event number 997，以及 pilot ordinal 997。ROOT `TTree::GetEntry` 對應 **zero-based entry 996**；實際 `Event.Number` 仍為 997。Pythia 粒子 index、HepMC particle ID、ROOT Particle 陣列 index 是不同識別空間。

| 項目 | 精確既有記錄 |
|---|---|
| LHE event SHA256 | `322457dfbd206b7cbd2c243f7b437970b82bb03c38fafe7721e40709f77127b8` |
| HepMC event-block SHA256 | `157928b854ffa4be208b4460338afea8d857446a595a56016c7e8cb994fec31f` |
| Generator / shower / detector seed | `20261022 / 610203 / 610303` |
| 原始 LHE/Pythia nominal weight | `9.4365561 pb` |
| 原始 event contribution | `0.0094365561 pb = XWGTUP / 1000` |
| 原始 hard incoming partons | `u(2), g(21)`；此事件沒有 incoming b/c |
| 原始 hard outgoing partons | `g(21), u(2)`；另有兩個 photon |
| 原始 eligible jets / observed bit0 tags | `5 / 1` |
| 原始 `m_gamma_gamma / m_jj` | `135.55650162670545 / 229.79333891363382 GeV` |
| 原始 cut flags | photons PASS、jets PASS、two-btags FAIL、tagged mgg FAIL |

原始 generator model 是 `sm-no_b_mass` 的既有 light-jjgg LO 樣本；proton definition 是 5F，final `jl` 排除 b/c。一般樣本的 5F initial state 可以包含 heavy flavours，但 **這個事件**的實際 incoming IDs 是 u/g。原始 printed generator cross section 與 event weight 保持各自的原始精度，沒有重設 normalization。

實際讀回驗證完整 ROOT 檔仍有 1000 entries，entry996 的 Event.Number、571 個 Particle 的 multiplicity-preserving `Float_t PID/status/p4/mass/XYZmm/Tseconds` tuples、所有 Jet/Photon persisted fields 與來源相符。讀回前後所有原始 ROOT/LHE/HepMC/ledger/cards/manifests，以及本次程式、設定、依賴檔 SHA256 均保持一致。這是讀取既有資料，新增獨立 hard statistics 為零。

Pythia 與 HepMC 各有 571 nodes、1149 mother edges；兩者都沒有缺失、重複或不互惠 edges，Kahn traversal 完整走訪。571 個粒子的 PDG、官方 converted status、binary64 p4、generated mass tuples 都唯一匹配；所有 mapped mother edges 一致。Pythia beam roots 是 `[1,2]`，HepMC roots 是 `[1,5]`，清楚顯示不能把兩種 ID 直接視為相同。

| Pythia index / signed status / PDG | 唯一 HepMC ID / status | 原始關係與 production vertex |
|---|---|---|
| `7 / -23 / 21` | `121 / 23` | hard outgoing gluon；production `explicit:-63` |
| `13 / -44 / 21` | `123 / 44` | mother `[7]`；production `implicit:121` |
| `17 / -51 / 21` | `125 / 51` | mother `[13]`、daughters `[19,20]`；production `implicit:123` |
| `19 / -51 / +5` | `126 / 51` | mother `[17]`；production `implicit:125` |
| `20 / -51 / -5` | `127 / 51` | mother `[17]`；production `implicit:125` |
| terminal B `276 / -83 / -511` | `343 / 2` | 原始 mother list `[266..275]`；production `explicit:-208` |
| terminal B `488 / -91 / +521` | `243 / 2` | mother `[363]`；production `implicit:150` |

上述 production vertices 沒有寫出 ASCII `@ x y z ct`，因此這些原始座標記為 **UNKNOWN / NOT_WRITTEN**。Pythia 原始 diagnostic 沒有保存 `xProd/yProd/zProd/tProd`，不可填上推測座標。原生 Delphes reader 對未記錄 vertex position 初始化零；這是已驗證的 reader 儲存行為，並不證明缺失的 Pythia 原始物理座標等於零。其他實際寫出的 HepMC vertex coordinates 保留在完整衍生 evidence 中。

官方 Pythia 8.317 `ParticleProperties.xml` 將 51 定義為 FSR branching 的 outgoing particle；44 是 outgoing particle 被 branching 移動的記錄。`Event.cc::statusHepMC()` 保留非末態 parton 的正 absolute status，normal decaying hadron 則可轉成 2。這些定義來自已驗證的 [8.317 官方 release](https://pythia.org/releases/pythia83/pythia8317.tgz) 內 `src/Event.cc:383`、`share/Pythia8/xmldoc/ParticleProperties.xml:82–103`，及官方 `include/Pythia8Plugins/HepMC3.h` 的轉換器。

所以 `7 → 13 → 17 → {19,20}` 是本事件的單一直接 perturbative b/bbar birth。後續 status44、62、71 記錄是既有 bottom line 的 shifted/remnant-treatment/hadronization-preparation descendants，不能重複計為多次 b-pair production。所有 bottom parton 記錄的完整 p4、mothers、daughters 均保留；原始 shower intermediate vertices 不套用天真的兩體 p4 相加條件，因為 recoil bookkeeping 會改變記錄關係。

| Native jet index | PT [GeV] | eta | phi | Mass [GeV] | Flavor | BTag bit0 |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 121.91602325439453 | -0.8472098708152771 | 0.7968314290046692 | 8.60512638092041 | 5 | 1 |
| 1 | 102.26307678222656 | -0.4084344506263733 | -2.3827178478240967 | 12.4693603515625 | 2 | 0 |
| 2 | 51.618804931640625 | -0.16746409237384796 | 1.1668105125427246 | 6.361476898193359 | 21 | 0 |
| 3 | 49.05119323730469 | -1.5705726146697998 | -2.33537220954895 | 4.892856597900391 | 21 | 0 |
| 4 | 48.46134948730469 | -0.8677039742469788 | 0.19525806605815887 | 6.8712849617004395 | 5 | 0 |

Birth b19 與 jet0 的 ΔR 是 `0.06648569284409198`，birth anti-b20 與 jet4 是 `0.03201336950131877`。terminal B276 與 jet0 是 `0.049242267764080416`，terminal B488 與 jet4 是 `0.059414855780454745`。另外三個 terminal charm hadrons 436(-411)、526(421)、555(-421) 是 B-decay descendants；本事件沒有新 perturbative charm-quark pair birth。

B276/其 charm descendants 的兩個 fresh-bottom birth 候選集合是 `[19]`；B488/其 charm descendant 的集合是 `[20]`。這是精確 ancestor 集合的結果。B276 的 immediate mothers 是十個 string partons，B488 也經由 excited-hadron/string ancestry；幾何近鄰及單一 bottom-birth ancestor 仍不證明 hadron 的 **sole parton endpoint attribution**。該歸屬保留 `UNKNOWN`，不刪減多母粒子關係。

Frozen conditional model 給出 `q997=P(tags>=2)=0.49391027578627762994629311428239633751900699125665`。mgg 已通過固定 `105..160 GeV` 區間，所以本事件兩個分析 stage 的 q 相同。這不把原始 one-tag outcome 改成 two tags；原始 `m_bb=null` 保持不變。完整十個 possible leading-tagged pairs 的 probability、mass 與 four-object mass 都在 evidence 中；其中 native b-b pair `(0,4)` 的 probability 是 `0.48710495861906741241975046002351283216993189822867`，mass 為 `48.42472461954615 GeV`。leading-jj 的 `229.793...` 不是這個 b-b mass。沒有新增 mbb cut。

[完整影響分析](../simulation/heavy_flavour_forensics/evidence/influence.json) 保留全部1000事件：light-jjgg final expected count 為 `0.501324516614085034274969784089164284211567398991701894`，source997 佔 `98.52106957028898%`，其 source-weighted expected contribution 是 `0.004660812025823680465163234959969544281432644289285587223065 pb`。剩餘999事件的 fixed-original-denominator count 為 `0.007414240827807404328676669806767946692560407735051894`。Leave-one-out 只是 influence diagnostic，並非 corrected prediction，原始事件沒有被移除。

實際執行的 read-only command 是 `python3 -B simulation/heavy_flavour_forensics/scripts/source997.py --output .local/phase6e/source997-v4`。最後版本 source SHA256 為 `2ae413af8edfa1d61a6c1bf911272f09b9cffe7b7d427cce1d83e9b318e6642a`；[source997.json](../simulation/heavy_flavour_forensics/evidence/source997.json) 為 1,062,918 bytes、SHA256 `7bd155040ef95dec6a3423d38a1e312e7499d6683c4644853b26c8c312bbad9c`，由 [manifest](../metadata/phase6e_source997_manifest.json) 綁定。`--verify-evidence` 已在 Ubuntu/WSL 與 Windows 實際執行，結果是 `PASS_OFFLINE_REPLAY`；它不重新開啟 ROOT，也不取代已執行的 native readback。

**本事件 origin verdict：`DIRECT_FSR_G_TO_B_BBAR_CONFIRMED`。** 這不建立 inclusive heavy-flavour rate、樣本互斥性、官方 ATLAS background、calibrated btagging、photon fake rate 或 HH sensitivity。
