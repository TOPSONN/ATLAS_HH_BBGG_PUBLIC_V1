# Pure protocol 與真實部署差距

PR43的PID/start/UID/source/config/slot、cgroup hierarchy、累計counter、stop-state及post-exit observer協定保留，沒有改寫。此次adapter只取得窄幅診斷，並非protected kernel acquirer。

以下全部BLOCKED_OS_CAPABILITY：collector與controller不同death-domain且同parent pool；manager/InvocationID與原始PID-start可信綁定；ancestor/child membership及raw kernel counter完整取得；不可任意fallback的trusted manager；collector退出後、外部權限隔離observer；final parent-empty/cleanup與protected slot commit；固定resident allocation及OOM survivability；async kernel CPU ownership。

讀到user@UID.service不證明以上部署。普通0600/0700 owner目錄不能防同UID惡意process，也不是獨立protected failure slot；原post-exit supplement未接受。沒有發現需修改原g2_protocol的可重現新缺陷，因此原碼不變。
