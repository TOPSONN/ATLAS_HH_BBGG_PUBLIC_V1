# G1 單次重新擷取操作

Exact source：`61bda291c2bc6a04607cb8ea889e520a4ceb260b`。此命令只供您在原先的一般權限 PowerShell 7 執行一次。請先確認新 PR 的離線 CI 結果；不需 Administrator，也沒有正式 build 確認字串。

ExpectedScriptSha256：`fceee4386b1f90ceb72a3304ab5006e94f935c4d4fdf4ea2ad3e0a0ce36c4eee`。
ExpectedWslExeSha256 維持原綁定，本次唯讀重新核對一致。若日後 binary 改變，停止並另外審查。

```powershell
pwsh -NoLogo -NoProfile -File "C:\HH\.local\phase7i_g1_association_repair_v1\source\simulation\hh_signal\final_closure\resource_closure\g1_windows_inventory.ps1" `
  -OutputDirectory "C:\HH\.local\phase7i_g1_g2_feasibility_v1\private" `
  -ExpectedScriptSha256 "fceee4386b1f90ceb72a3304ab5006e94f935c4d4fdf4ea2ad3e0a0ce36c4eee" `
  -ExpectedWslExeSha256 "fcd08205b608b5c4831e0dcb1801dd274436cd2c8420815f18ae58a085891a18"
```

請複製整段命令一次。每個反引號必須是該行最後一個字元。也可將參數接為同一行。執行完成只回報 `local_receipt`、`sha256`、`observations` 與 `unknown`；不要貼出私有 JSON 內容。

程式沿用已受保護的 private 目錄，先檢查 current-user-only ACL，再用新 UUID 與 CreateNew 產生新檔；不會覆寫舊收據。13 類查詢、128 rows、65,536 bytes/query、196,608 aggregate payload、262,144 capture bytes 全部保留。WSL 只允許既有的版本與 running-list 唯讀查詢；不啟動 distro。

如果出現 SHA、ACL、CIM 型別或 bound 錯誤，保留失敗收據，不重跑、不提高容量。

新收據由以下 installed Python 工具驗證並產生新的 sanitized projection，路徑中的 `<NEW_CAPTURE_ID>` 應替換為這次回報的 UUID，絕不可填舊收據。新輸出必須不存在：

```powershell
Set-Location "C:\HH\.local\phase7i_g1_association_repair_v1\source"
& "C:\Users\User\AppData\Local\Programs\Python\Python314\python.exe" -B -X utf8 -m simulation.hh_signal.final_closure.resource_closure.g1_acquisition --capture "C:\HH\.local\phase7i_g1_g2_feasibility_v1\private\host_<NEW_CAPTURE_ID>.json" --output "C:\HH\.local\phase7i_g1_association_repair_v1\projection_<NEW_CAPTURE_ID>.json"
```

Projection 綁定真實 raw SHA 與這次 script SHA；不接受將舊 V1 收據重綁新 collector。這一步不需要 Master run。若後續需要新 Master run，必須另做 exact new-source 的全新 run；既有 run 不重綁。

13/13 只代表 reported query coverage；仍為 REPORTED_UNATTESTED，不能升級成 host attestation、guest 驗證、G2 批准或完整資源通過。
