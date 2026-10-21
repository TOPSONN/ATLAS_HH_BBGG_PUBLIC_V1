本文件為待獨立審查提案，不是執行授權。Exact source `83d1cda235e1d5fcc23f48d6a53065f88f2d1b1d`。未批准者保持BLOCKED；不得自行填假approval、降限制或改原始收據。

# Device graph adapter review

保留既有device_policy/instance_binding原碼；新adapter先驗真實host V2完整edges，明確將未具host/guest mapping及all-mount-namespace inventory的資料拒為REJECTED_INCOMPLETE_ACQUISITION，不會把完整JSON shape轉成complete=true。

本次reported Windows僅一個physical disk且有boot partition；沒有已核實可拋棄候選，不能拿已知Windows boot backing作容量store。guest root/history parent、holders/slaves、dm/loop、hotplug/diskseq、by-id、mount alias與host映射仍缺實證。既有policy仍只允許簡單、獨立whole disk；part/sibling/dm/loop/thin/sparse/snapshot/growable、重複alias、protected overlap均拒絕。

新guest V2不再把holders/slaves前129項當完整集合；超限整項UNKNOWN。這仍只是guest內reported拓撲，沒有host writer/hotplug lease，無權挑選format裝置。
