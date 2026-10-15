# Phase7F：零保留 writer 與 runtime 邊界

**INTEGRATION_EXECUTED=NO；NATIVE_RUNTIME_GATE=NOT_EVALUATED。**

原生 driver 先開啟 scratch unit27，再 setrun/setpara/cuts/printout；真正 helicity 初始化、sampling 與 sample_full 在後。Phase7F 的 pre-sampling gate 與初始化專用退出分支插在第一個 init_good_hel 之前。現版任何非初始化入口均 STOP80；Python CLI/runtime bridge 也在任何 output I/O 前拒絕積分，無 token/file/env 授權繞道。

| 物件／API | 本版處理 | 實測範圍 |
|---|---|---|
| integration scratch／空 unit27 | 可存在；不視為物理樣本 | 四個 driver 初始化出口，零 ME/iteration |
| RAM 動量／candidate arrays | 不等同 retained LHE | 未跑 integration；不聲稱完整 runtime 支持已驗證 |
| write_leshouche | no serialization、只增加 suppressed counter | synthetic boundary 實際執行 |
| store_events | 原 unweight/store body 移除；只計數並明確將 retained/theoretical event counters 設0 | synthetic boundary 實際執行 |
| clear_events | 清 scalar/candidate count；不呼叫 store、不 rewind 未使用的 event file | synthetic boundary 實際執行 |
| direct write_event | fatal STOP86 | 原生拒絕實測 |
| generate/combine/final-unweight/shower/detector | 無 allowed dispatcher；legacy actual launch 被拒絕 | CLI、command allowlist 與 native STOP80 實測 |

沒有修改 upstream MG5 或舊 process。四份 native source/library 副本各自 hash-bound、無 symlink；原 unwgt/Zoom_Event 的主體保留，但 writer 內部 RNG 消耗及 candidate 狀態會改變。**不能由編譯與 synthetic tests 推論完整 survey 的積分語義、收斂或誤差 coverage 已正確。**

事件輸出 audit 拒絕物理 sample 副檔名、events.dat 與偽裝 extension 的 `<event>`/LHE/HepMC/ROOT；掃描後的 files/bytes/SHA 保留。source/evidence publication guard 另拒絕新物理 sample、archives、binary objects 及未核准 PDF/PNG。postcondition 只能證明受檢查目錄的當下狀態，不能證明真實 survey 未寫過 transient records；目前沒有真實 survey。

未來 runtime bridge 已準備 source/binary hash 檢查、單 CPU affinity、CPU/file-size limits、wall/disk 輪詢與整個 process group 終止；本階段 authorization 在此路徑最前端無條件拒絕。準備／probe 子程序已用單 CPU、60秒 per-child wall/CPU 與64MiB per-file限制；額外磁碟與 aggregate 4h budget 在準備中檢查。完整積分 watchdog、stage transitions、實際 ME counters 與零保留驗收須在另行授權後評估。

原生 synthetic context tests 實際退出碼：正常0、錯 global PDF71、beam label72、running73、seed74、mass76、HEPRUP metadata77。完整 driver 的實際初始化出口另 PASS，未授權積分 dispatch 為80；permanent writer86。這些數字是防護證據，不是新物理測量。
