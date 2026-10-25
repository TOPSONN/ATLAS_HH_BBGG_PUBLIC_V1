# 原三條Manager查詢

manager_scope_contract.fixed_argvs()/fixed_env()逐項回歸等於PR45 contract；無新增properties，固定user@1000.service，無remote bus、pager/password agent/root fallback，timeout只hash不執行。client255僅歷史self-report，system/user manager及effective service properties都尚未觀察。show的manager/既存unit property意圖保留，但不稱零control-plane成本。[systemctl v255](https://www.freedesktop.org/software/systemd/man/255/systemctl.html)。

原5s child、1s cleanup、30s adapter soft、8192-byte合併child output、32768 aggregate、131072 receipt、8層lineage、0700/0600、retry0不變。新增security envelope也受131072-byte bound；額外輸入證據是固定有界資料，並不是完整kernel CPU/RAM/wall envelope。原capture/validator不作正式entry，只有新冷啟動guard路徑可候選。

完整diagnostic含原before/after proc/namespace/cgroup snapshot，固定每層九介面各256 bytes，mountinfo65536 bytes；不掃描全機。root預期缺欄位、缺bus、partial、inactive user service都保留UNKNOWN。先確認source/tool/UID/GID、scope/approval bytes鏈與native FS，再談實機批准；現在沒有final launch manifest或human reference。
