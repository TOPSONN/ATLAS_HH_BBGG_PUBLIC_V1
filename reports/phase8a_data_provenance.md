# Phase8A 資料來源與保全

## 目標與證據範圍

從精確基底 `b80e16775bf141e45f4048c7197a8a99befaed51` 的既有 manifests，解析真正 local full-run inputs，排除只讀取 reference prefix 卻宣稱完整資料的情況。來源hash audit屬於 `HISTORICAL_EVIDENCE_AUDIT`：113個來源與cards檔案、共1,658,781,807 bytes相符。其後實際C++20/ROOT 6.40.04 native loop已讀取全部7100筆；八組皆為 `PASS_FULL_DATA`、duplicate/invalid/skipped皆0，full cutflow每個stage difference=0。此 `ACTUAL_FULL_DATA_READBACK` 與前述hash證據分開保存，不以檔名或舊manifest宣稱成功。

## 實際輸入與方法

Signal B100 與 C1000 分開處理；六個背景各1000筆來源事件。八組 input index 均用獨立 Python parser 實讀，驗證 ordinal/source index 連續、dataset內 native event number 無重複、source/HepMC event hashes 格式、W向量與原始 denominator、每個P列的有限數值、完整集合長度。再實讀原始 LHE，核對 event count、結尾完整性、逐事件 XWGTUP 與 input-index raw weight 一致。合計7100筆原始事件；來源index、LHE與這次native ROOT readback三者皆為7100筆，原始N保持不變。

| Dataset | 原始N | 實讀index | 實讀ROOT | source σ [pb] | 有效PDF / αs running |
|---|---:|---:|---:|---:|---|
| S01_B100 | 100 | 100 | 100 | 0.017276 | `cteq6l1` / ONE_LOOP |
| S01_C1000 | 1000 | 1000 | 1000 | 0.019069 | `NNPDF23_lo_as_0130_qed_mem0` / TWO_LOOP |
| B01 | 1000 | 1000 | 1000 | 0.06624666 | `cteq6l1` / ONE_LOOP |
| B02 | 1000 | 1000 | 1000 | 0.6274417 | `cteq6l1` / ONE_LOOP |
| B03 | 1000 | 1000 | 1000 | 9.436556 | `cteq6l1` / ONE_LOOP |
| B04 | 1000 | 1000 | 1000 | 0.08953800 | `cteq6l1` / ONE_LOOP |
| B05 | 1000 | 1000 | 1000 | 0.3991820 | `cteq6l1` / ONE_LOOP |
| B06 | 1000 | 1000 | 1000 | 65.88309 | `cteq6l1` / ONE_LOOP |

所有 source contribution 使用 `XWGTUP_pb / N_original`，不再乘 σ/N。Signal HH factor `2 BR(H→bb) BR(H→γγ)=0.002653445906720871` 僅在 model-weight mode 乘一次。ZH的 Z→bb 已在source中，僅乘自己的 H→γγ model factor；ttH依其獨立初始化的model BR。B06沒有Higgs BR，也沒有可用 calibrated fake-photon model。

## 設定與來源身分

`metadata/phase7e_audit.json` 的實際 runtime 結論優先於歷史 run_card 宣告：B100是 CTEQ6L1、one-loop、effective seed21；C1000是 NNPDF23 LO、two-loop、seed20261122。B100不可與C1000合併成同質1100-event sample。6000列κλ reweights對應同一組1000筆C來源，不能當成6000獨立事件。

Portable manifest保留 `REPOSITORY/` 與 `LOCAL_HOME/` logical aliases；真正 absolute local paths 僅在本機 `phase8_local_manifest.json` 中，不發布。C1000公開 `detector_100.root` 只是100筆prefix，完整1000ROOT從原manifest指向的本機來源選取。所有dataset都同時保留預期完整entries、原始N與prefix狀態；nativeROOT schema、event-number與particle-tuple closure已由這次原生loop驗證；共比較3502715筆native particle tuples，未把Particle array次序當成barcode。實際required/optional branches、dictionary版本/checksum與ordered event digest保存在公開dataset manifest。

## Tagging model 可用性

八張凍結 detector card 的 `BTagging` module bit0完整片段SHA256均為 `633c524097f4eb51634ddfbc769f15bc70b212d1b6812cf8b73288d0e0aea9ad`。實際pT模型：light `0.002+7.3e-06*pt`；charm `0.20*tanh(0.02*pt)/(1+0.0034*pt)`；bottom `0.80*tanh(0.003*pt)*30/(1+0.086*pt)`。此為固定reconstructed event上的 conditional model，非官方ATLAS calibrated tagger。Observed native bit0與conditional expectation分開，不重加一次已realized tag variance。

## 驗證與重現

```bash
python3 -B analysis/phase8/tests/test_phase8_provenance.py
python3 -B analysis/phase8/scripts/audit_inputs.py --output "$HOME/simulations/hh_phase8/FRESH_RESULT_DIRECTORY"
```

21項 `SYNTHETIC_METHOD_TEST`涵蓋duplicate/missing/reordered source、truncated particle、nonfinite weight、錯hash、缺檔、未知dataset、錯sample version、path traversal、nominal/denominator closure、LHE raw-weight closure、保全失敗、禁止覆寫及background/fake blocker；不能取代actualROOTreadback。實際audit已通過8組LHE/index與113個hash綁定檔案。輸出目錄必須全新，既有同名audit收據會拒絕覆寫。

完成所有分析後，以原before snapshot重新讀取同一113檔案：

```bash
python3 -B analysis/phase8/scripts/audit_inputs.py --verify-snapshot "$RESULT/phase8_input_preservation_before.json" --output "$RESULT/phase8_input_preservation_after.json"
```

## 未解決物理問題與下一步

保持 B01/B02/B03 heavy-flavour overlap、B06 fake calibration、B05 spin model、C1000有效PDF/αs mismatch、κλ2.5/5 low-ESS限制。Hash成功只確認來源位元一致，不能解除這些物理閘門。八組已完成native entries/classes/particles與全量historical cutflow closure；另8組100-event reference-prefix已完成原生readback，共800次重讀；每個輸出事件summary都與對應full資料的first100 events完全相等，additional independent sources=0。後續以region/weight/kappa獨立數值驗證與after-hash保全作最終技術閉合。此流程不呼叫MG5、MadLoop、Pythia或Delphes，新增ME/integral/event均為0。

## 本次原生數值產物

實際ROOT histogram readback通過：TH1D=4052、TH2D=616，共4668個defined histograms；empty/ill-conditioned unit-area shapes維持undefined，不建立假的nonzero shape。Canonical histogram-content SHA256：`4a8899dfde5b484d49e30438b704f81e77b648cb07d643e7360b0c181a2a9ed2`。這是numerical ROOT內容驗證，不解除physical overlap、calibration或rate gates。

## 公開Reference Prefix的實際讀取

`REFERENCE_PREFIX_TEST`已完成八組各100筆，真實TTree entries均為100；總共800次原生事件重讀，不增加7100筆independent originals。獨立Python驗證逐事件summary對應full來源exactly equal。完整histogram CSV另由獨立數值程式檢查180989個cells的content與sumw2，不以source-only CI冒充這次native readback。
