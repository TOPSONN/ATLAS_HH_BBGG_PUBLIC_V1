# Phase 6B external LHE interface

本階段直接重用三份 Phase 6A 的真實 MG5 3.5.16 LO LHEF 3.0，各有1000 events。沒有重新生成、替換或重寫任何 LHE event。`validate_lhe_stream.py` 已實際讀完三份原始 gzip，counts、cards、截面與 SHA256 均與既有 Phase 6A validator 相同。

| Profile | Original file under `reference_samples/mg5/` | Original gzip SHA256 |
|---|---|---|
| bbgg | `pp_bbgg_sm_lo_13tev/reference_1000.lhe.gz` | `bc8f0c4a48a1db512013552afe3ec8091dddaae8b47daf7aae808d7cb767a343` |
| ccgg | `pp_ccgg_sm_lo_13tev/reference_1000.lhe.gz` | `3042fb08802e66e1582466a59e6d4dd3deabbd6fd64f91748830a09b76bae7ef` |
| light-jjgg | `pp_jjgg_light_sm_lo_13tev/reference_1000.lhe.gz` | `606b092b3c3751bfe7a900e52a3928580a7ee015a1884f7ca6e03ac260260030` |

原始 hard process 為 `sm-no_b_mass`、massless five-flavour scheme、CTEQ6L1 (`lhaid=10042`)、固定125 GeV scales、6500 GeV proton beams、`IDWTUP=-4`。bbgg/ccgg 為對應 flavour pair 加兩個 photons；light-jjgg 的兩個 final partons 只允許 gluon 或 u/d/s 及其 antiparticles。輸入 cuts 是 hard-generation definitions，不會再次套用為 shower final-state selection。

streaming preflight 檢查完整 XML/gzip CRC、generator/model/card identity、beam/PDF/scale、事件數、finite signed weights、incoming/final PDGs、ancestry、color flow、charge、逐味道 quark-number conservation、mass shell、four-momentum closure 與原始 cuts。保留 header 與單一 event；預設 decompressed budget100 GiB 可依明確資源設定改變，單一 XML element 上限16 MiB，distinct numerical diagnostics 只保留 bounded sets。這項 API 容量準備不代表已執行1M events。

真正的 Pythia8.317 使用 `Beams:frameType=4` 和外部 `Beams:LHEF`。`TrackedLHA` 內部呼叫官方 `LHAupLHEF::setInit/setEvent`，並回傳 `useExternal()=true`，將實際讀到的 beam/process/particle records 傳入 Pythia；不是自己生成 hard process。native gzip capability 在獨立安裝中有測試，controller 為 sidecar indexing 解壓原始輸入時另檢查 decompressed SHA，解壓不改變 LHE bytes。

每次官方 reader 成功讀取事件，cursor 即增加；之後比對原始 indexed LHE 的 event header、PDGs、statuses、mothers、colors、p4、mass、lifetime、spin、SCALUP 與 couplings。若 Pythia 在 `next()` 內部讀入多個事件，ledger 同時保存各 consumed input；先前被拒絕的 input 標為 `INTERNAL_REJECTION`，不隱藏為未讀取。外部 reader 已消耗但 source identity 比對失敗時，counters 保存 consumed 與 verified 的差異，狀態為 PARTIAL/BLOCKED。

source index 為原始 LHE 的1-based index。`source_event_content_hash` 是 exact `<event>` 至 `</event>` bytes 的 SHA256；event element 後的換行不在該 hash 內。輸出另保存 sample/file/event identities、Pythia run ID、seed、dense output index 與 exact raw HepMC3 event-block hash。原始 p4 另存 sidecar；HepMC barcode 與 Pythia index 不能當作原始 LHE particle barcode 等價。

`Beams:strictLHEFscale=on`、ISR/FSR `pTmaxMatch=1`，external SCALUP 作 shower 上限；沒有 ME/PS matching/merging。Pythia shower/fragmentation 使用其 massive heavy-flavour table (`m_c=1.5 GeV`, `m_b=4.8 GeV`)。官方 hard-process mass restoration/recoil 與後續 shower 可改變 hard-record momenta，因此驗證要求原始 LHE immutable、讀取身份正確與完整 beam→stable conservation，並記錄 hard-photon unordered p4 差異；不宣稱 hard p4 不變。

批准的 baseline v2 為 `baseline_shower.cmnd`，SHA256 `53ab239a091b179abce8db5d6905a279884c47a0286a422c059265460ec33389`，stock Gaussian primordial-kT remnant/recoil model ON、additional MPI OFF。這是明確的新 physical model choice，不能視為修補舊 output。舊 collinear-OFF card 與其 failed100 output 保留為 diagnostic，不能通過 reference publication gate。

新 baseline v2 已實際完成 Stage A bbgg10、Stage B每process100、Stage C每process1000，所有 requested/consumed/written/readback counts相同，shower/source-identity/physical-validation failures均0。seeds分別為bbgg610201、ccgg610202、light-jjgg610203。post-freeze portable validator再次實際讀完Stage C全部3000 outputs及其原始source/ledger，每event完整weight vector/accounting PASS。公開300 events只抽取各valid full1000的raw100prefix，不增加獨立hard-event statistics。此前舊card的真實10prefix PASS，但其100extension在event54失敗，詳見HepMC3 validation report；該結果保留且不納入v2 reference。
