# Phase7G：已鎖定的積分準備與操作界線

目前 `AUTHORIZATION_STATUS=NOT_GRANTED`，且 `WRITER_SEMANTICS_VALIDATED=false`。
本版**不能執行物理積分**。收到任務、命令列文字、環境變數或授權檔案都不構成另行的人類授權。
這不是事件產生器；需要一般 MG5 事件生成時，請另讀既有的 MG5 使用指南，勿用本任務解除歷史 HH 生成閘門。

以下命令在既有 WSL Ubuntu 環境、儲存庫根目錄執行，不需安裝或更新軟體。
輸出路徑必須是尚不存在的 `$HOME/simulations/hh_matched_integration/` 子目錄。

```bash
bash simulation/hh_signal/matched_integration/integration_only.sh \
  --output "$HOME/simulations/hh_matched_integration/my_plan_01"
bash simulation/hh_signal/matched_integration/integration_only.sh \
  --output "$HOME/simulations/hh_matched_integration/my_plan_01" --validate
python3 -B -m simulation.hh_signal.matched_integration.validate
python3 -B -m unittest simulation.hh_signal.matched_integration.test_matched -v
```

前兩條只複製、核對卡片，建立四個獨立工作目錄及預定端點；第三條核對已公布的實測準備證據。
本次已實際執行同樣命令，使用 `plan_01`；重新操作請用新的目錄名稱。既有目錄會被拒絕覆寫。
`plan.json` 記錄 code/config hashes；`scope_identity.json` 是其 canonical JSON SHA256。
每次原始碼、卡片或端點變更都需建立新的計畫與審查，不能沿用舊 hash。
每個 `replica_<seed>/cards/` 保存 Phase7F 已核對的 run/param/include/prepared Banner；這個 Banner 不是新生成的物理 LHE header。
`adaptation/` 和 `measurement/` 各保存 `input_app.txt`、`randinit`、`iproc.dat`、`moffset.dat`；沒有 grid、結果或事件檔。

下列命令是**拒絕案例**，預期 exit code 2，且不會建立輸出；不是啟動方式：

```bash
bash simulation/hh_signal/matched_integration/integration_only.sh \
  --output "$HOME/simulations/hh_matched_integration/denied_01" --execute
```

即使傳入 `--authorization AUTHORIZE_PHASE7G_HH_INTEGRATION_ONLY_4_REPLICAS`，仍會拒絕。
若日後另行給予該明確人類指令，也仍需先解決語義阻擋並審查綁定到新程式版本的執行路徑；此提交沒有可由 token 解鎖的 native dispatch。
原 Phase7F `STOP80` 授權邊界與 `STOP86` 永久寫入拒絕完整保留。

預定 Stage A 只用 seed 910001 做一次真正 adaptation survey；尚未執行。
Stage A 的實際 ME/config/seed/counters/grid/零保留/完整性證據全部通過，才能考慮其他 replica。
seed 910001、910019、910037、910061 的 grids 必須各自從空白開始，不能匯入 B/C 或其他 replica 的 grid。
measurement 只使用同一 replica 的 hash-bound adaptation grid；它不是另一個獨立 replica。

預定 adaptation：初始 250 points、固定 4 iterations；measurement：初始 250 points、固定 3 iterations。
兩者 accuracy=0、min=max iterations，排除 accuracy 與負 accuracy 的事件數停止機制。
原生程式每輪會加倍 points，因此不能把它估成每輪固定 250。
這是待審查端點，尚未通過真正 survey 的行為驗證，也不保證收斂。
Stage A adaptation estimate 不當作最終 measurement；只有完全相同的 frozen endpoint 才能重用對應階段的結果。
未授權前不可執行 `input_app.txt` 對應的 native binary，也不可修改 `STOP80`。

未來執行仍受一個 job、一個 worker、合計 CPU/牆鐘各四小時、額外磁碟五 GiB 限制。
超時、磁碟超限、native 失敗或少於四個完整端點都記為 PARTIAL，保留日誌、當時 grid、終止原因與已消耗資源；不得自動加預算。
目前只有 compiler/RNG fixture 的實測資源數字；沒有 survey CPU/RAM 量測。

檢查結果請讀 `reports/phase7g_final_report.md` 與 `reports/phase7g_writer_semantics.md`。
`semantics.json`、兩份 RNG trace、synthetic 固定權重結果、CLI receipts、回歸日誌均有 manifest hash。
固定權重 41 / 289 是方法測試的和／平方和，**不是截面**。
實際 ME、積分 counters、grid 穩定性、尾端行為及完整 transient monitoring 仍為 NOT_EVALUATED。
最終檔案掃描不能證明執行途中從未寫入；完整 survey 也尚未發生。

將來比較時，B 原始截面 0.017276 pb 是 CTEQ6L1／一圈、actual seed 21，積分歷程不同，須保留限定。
C 原始截面 0.019069 pb 實際是 NNPDF23 LO／兩圈、seed 20261122，不可視為相同 integrand。
本版不變更舊卡片、權重、事件、截面、報告；κλ=2.5/5 的既有支撐限制也不因此解除。

公開僅選定來源、文字及有界數值證據。不要提交個人工作目錄、執行檔、事件或大型 grid。
提交／push 前需檢查 index 及每個 outgoing commit；未經使用者核准的 PDF/PNG 不能提交。
Draft PR 不會自動 merge，也不能 force-push。
