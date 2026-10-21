本文件為待獨立審查提案，不是執行授權。Exact source `83d1cda235e1d5fcc23f48d6a53065f88f2d1b1d`。未批准者保持BLOCKED；不得自行填假approval、降限制或改原始收據。

# 管理員執行前scope：UNBOUND，不可執行

順序：先提供exact device與disposable receipt；核對root/history ancestor排除；freeze helper/source/binaries和政策digest；建立單次host-writer/hotplug lease；再請求specific provisioning批准。每一步保存before/after identity與失敗證據；不自動進入format。

本輪target、helper identity、lease identity、host allocation與UID均null，因此沒有合法可執行的attach/format/mount命令。用猜測/dev/sdX、PHYSICALDRIVE或外部mkfs重開路徑會違反既有policy，必須STOP。此為明確未綁定阻擋，不是READY_TO_EXECUTE。取得實際identity後，下一個safe動作是用既有policy及新adapter驗證，不是直接執行。
