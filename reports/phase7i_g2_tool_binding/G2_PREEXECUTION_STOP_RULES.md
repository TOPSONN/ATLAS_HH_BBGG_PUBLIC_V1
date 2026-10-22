# 執行前停止規則

現在僅source-only；完整diagnostic與version-only新query均未執行、未授權。TOOL_IDENTITY_OBSERVED=true只表示此次直接使用者回報已保存；TOOL_IDENTITY_VERIFIED=false。沒有原probe raw bytes，不捏造其digest或capture時間，也不要求重跑成功的hash-only probe。

完整diagnostic繼續用原四個source SHA、UID/GID1000/1000、固定三條argv、封閉environment、no-pager/no-ask-password/no-autostart與固定output。每child5s、cleanup1s、adapter30s都是soft；8192/32768/131072 bytes、8 lineage、0700/0600 exclusive及no retry不變。不能以expected hashes填入就推升execution-ready。

installed systemd、dependency closure、existing root-owned system-bus socket、UID1000-owned user systemd/private socket及安全parents、private output parent與scope authorization reference全部需分別核實。目前bus/socket/parent實測null。user socket缺失記UNKNOWN、不start/enable/linger；v255內部default-user fallback的無效FD地址封閉規則保留；新version-only argv不觸碰bus。

任一source/tool/UID/GID/argv/env變更、unknown cleanup、超界、缺receipt、重複scope/input、舊attempt或既有output都停止；不改名自動重試、不換目錄逃避single-use、不補human reference、不將false改true。必要的新版本/依賴資料只能建立新source/input run。

原private writer僅ordinary filesystem fsync，空間/權限/寫入失敗可能只保留attempt，不能保證durability或failure evidence在所有主機故障下完整。保留stderr與既有檔案，不清理、不sudo、不mount、不改服務。查詢批准不接受B-V2，也不批准cgroup、device、S4、BUILD或物理工作。
