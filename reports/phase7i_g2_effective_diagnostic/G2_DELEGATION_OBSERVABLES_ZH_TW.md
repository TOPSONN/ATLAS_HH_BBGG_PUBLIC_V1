# 最小effective觀察與推論界線

新單次receipt擬保存目前boot、UID/GID、PID/start、namespace inodes、統一cgroup membership及祖先dev/inode/ownership；固定9介面是controllers、subtree_control、procs、type、events、cpu.max、memory.max、memory.swap.max、pids.max。controllers存在只證可用；subtree_control是當時enabled，不是delegation授權。direct procs不含child，root預期缺介面與nonroot讀失敗分列。

兩條manager query確認當時system/user可達性；第三條讀當前UID的既存user service的accounting、Delegate、InvocationID、ControlGroup、MainPID、User、limits及active state。user bus缺失保留UNKNOWN，不能憑配置檔或PID1推升成功。read-only結果仍不證明future group creation、controller enable、service/scope placement、不同collector UID權限或cleanup。

真正下一步需manager提供受控且可驗證的child/sibling placement、單writer delegation、nonroot writer/collector分離與protected failure slots；各自另審部署。所審cgroup API：[Linux6.6](https://www.kernel.org/doc/html/v6.6/admin-guide/cgroup-v2.html)。
