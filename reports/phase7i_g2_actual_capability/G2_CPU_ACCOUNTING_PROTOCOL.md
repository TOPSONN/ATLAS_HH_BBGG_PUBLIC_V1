# CPU accounting protocol

原額度 S4=4,000,000 µs；BUILD=14,400,000,000 µs，是一個完整job的總量，不是每個PID各一份。新g2_protocol以單一fresh parent的cpu.stat usage_usec作累積來源，user_usec/system_usec作同一已審Linux6.6 ABI的整數一致性診斷；不再逐process加總，避免漏掉短命compiler/helper或double counting。保留parent直到collector退出後的最終readback，不能先刪群組再猜計數。ancestor可能承受其他工作；驗證的是專用job parent，不能直接拿共享ancestor總量當本job。

admission由外部trusted manager在空的新parent、counter=0時記錄。admission後才啟動controller、worker、compiler/helpers與collector；全部在parent以下、不同子死亡域。parent本身不放process，符合domain controller的no-internal-process限制。所有註冊角色以PID/start/UID及group identity綁定；protected acquisition尚未實作，因此來源驗證仍只代表input consistency。不得把JSON的membership_complete旗標當成kernel attestation。

早停比較整數累積CPU與獨立monotonic elapsed；stop_decision只產生TERM/KILL/observer請求，沒有任何signal、service或cgroup寫入。S4既有3s early-stop是保留的提案，不是剩餘1s必然足夠的證明；BUILD實際early threshold與poll/termination尾成本仍需實測及獨立審核。cpu.max/CPUQuota限每period的bandwidth；cpu.weight只是相對分配，均不是精確lifetime kill。CPUAccounting提供觀察，不提供此contract的原子總量停止。

非root cpu.stat在v6.6 rstat flush/adjust後以µs輸出，parts因整數截位允許2µs一致性容差；此容差不是資源額度加2µs。到最後observer讀取仍以原CPU cap判斷，超額一律拒絕。scheduler延遲、signal延遲、collector/cleanup尾量沒有已證明最壞有限值；不能由bandwidth乘wall推得零超額保證。

service/scope由一個manager管理，delegated subtree遵守single-writer；slice不能作Delegate對象。選擇system-manager持有parent/children，或另審service/scope delegation；不能讓systemd與自行mkdir的helper同時管理同一層。既有shell在init.scope及UNLIMITED，不證明新專用群組不能設定限制。實際owner、可用controllers、effective hierarchy、fresh admission及final acquisition仍需獨立scope。

來源：[cgroup v2](https://www.kernel.org/doc/html/v6.6/admin-guide/cgroup-v2.html)、[rstat](https://raw.githubusercontent.com/torvalds/linux/v6.6/kernel/cgroup/rstat.c)、[systemd accounting/quota](https://www.freedesktop.org/software/systemd/man/255/systemd.resource-control.html)、[delegation](https://systemd.io/CGROUP_DELEGATION/)。只審API，沒有部署。
