# Phase 6A background reference decision

Local verdict：LOCAL_VERIFIED_AWAITING_REMOTE。A–H PASS；I/J UNKNOWN，不能把尚未檢查的遠端出版或 CI 報成 PASS。

ccgg 與 light-jjgg 真正生成各 1000 events，seed 20261021/20261022。bbgg 1000 events 原樣沿用；reference total3000，smoke100 不計。完整 59 項 portable tests 與實際 LHE validation PASS。

兩個截面分別 0.6274417±0.005190692 pb 與 9.436556±0.0547472 pb；原 bbgg 為 0.06624666±0.0005940933 pb。每個值有自己的實際 generator output、cuts、PDF/scales、weight 與 SHA provenance，不能互換或當完整背景組成。

These are three separate LO parton-level reference categories. No shower/hadronization, detector response, charm/light-to-b mistags, shower flavour migration, photon fake background, or fragmentation contribution is modeled. Their cross sections are not summed and their event counts are not equal expected yields.

下一步：完成選定 refs 的 GitHub remote verification 與真正 CI，保持 stacked Draft PR 供審查。之後可先審查這些 hard-process categories/cuts/normalization；大型 production、mistag/detector/shower study 需另訂計畫，本次不啟動。
