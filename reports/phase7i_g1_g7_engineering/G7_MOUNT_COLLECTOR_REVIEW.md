本文件為待獨立審查提案，不是執行授權。Exact source `83d1cda235e1d5fcc23f48d6a53065f88f2d1b1d`。未批准者保持BLOCKED；不得自行填假approval、降限制或改原始收據。

# Mount／collector與S4前環境

source preflight沿用review_mount，獨立postmount再核exact namespace/device、UUID、非bind/nested mount、mount options、mount後root UID/0700、獨立findmnt一致、worker無raw access及無unexpected writable source。掛載前空0700目錄不足；actual mount approval仍缺。postmount是pure reader，不執行mount。

Collector UID、worker UID、helper identity、mountpoint instance及unit InvocationID都尚未綁定。需獨立帳號與root-owned protected directories時，只提案，未建立。Worker不得持有evidence writer FD；IPC以SO_PEERCRED、PID start/boot、InvocationID與定長序號/nonce綁定，capabilities清空，歷史source/data唯讀，僅work/private tmpfs可寫。Collector持8x4096預配置slots，failure保留2槽，worker/controller死亡域不包含collector；同parent CPU/RAM仍需計入。最後外部observer由新supplement提出，未接受。

未部署的systemd設定提案：單一parent pool；MemoryMax=536870912、MemorySwapMax=0、CPUAccounting/MemoryAccounting、KillMode=control-group、Restart=no、NoNewPrivileges=yes；worker/controller獨立受控子域，collector另子域。CPUQuota僅rate，不代替累積4s。實際UID、可寫mount與ExecStart未知，所以不產生可啟動.service。此處也不執行systemd-analyze/daemon-reload或start。

stdout/stderr應走預開有界pipe/slots或null，不能只靠LogNamespace解決user manager寫入。systemd255文件說明LogNamespace不支援per-user service；manager-generated logs不因worker log filter而全消失。實際journald storage/forwarding、rsyslog、user-session warning、unit unload保留策略仍缺guest effective-state證據，不能只讀conf就PASS。不得改全域journald或清舊logs。

正常、controller/worker/collector死亡、OOM、wall/CPU overrun、block/inode ENOSPC、partial/torn/replay、wrong InvocationID、orphan、resurrection、missing postmortem及mount substitution已做pure負面驗證。真正kernel/permission/allocated-capacity正反測試仍需exact-source/device授權。G7_SOURCE_AND_DEPLOYMENT_PLAN_READY不等於G7_ENVIRONMENT_READY_FOR_S4_REVIEW。


來源語義：[Linux6.6 cgroup](https://www.kernel.org/doc/html/v6.6/admin-guide/cgroup-v2.html)、[systemd255 exec](https://www.freedesktop.org/software/systemd/man/255/systemd.exec.html)、[Linux6.6 get_tree_bdev](https://github.com/torvalds/linux/blob/v6.6/fs/super.c#L1448)、[mke2fs手冊](https://man7.org/linux/man-pages/man8/mke2fs.8.html)。這些是API/source審查，不是本機kernel版本或實機能力證明。
