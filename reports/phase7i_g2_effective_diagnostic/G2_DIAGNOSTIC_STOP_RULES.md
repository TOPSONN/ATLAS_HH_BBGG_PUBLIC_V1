# 單次唯讀診斷停止規則

目前 BLOCKED_TOOL_IDENTITY 與 BLOCKED_AUTHORIZATION，沒有執行。工具 hash、resolved ELF、root ownership/mode、Python3.12、systemd255 source family、nonroot UID/GID、exact source/scope/output 均須另審綁定。hash-only bootstrap 只能建立觀察，不能自證主機或 interpreter 信任根，不能批准 manager query。

新 scope 是三條固定 systemctl argv：system manager、user manager、固定當前 UID 的 user@UID.service。原二條 argv 的 manager properties 語義可保留；新版本另加 --no-ask-password 並明確新增第三條，沒有靜默替代。GNU timeout 只盤點 identity，不啟動，避免多一層 timeout child。任意輸入、remote bus、shell、pager、password agent、network、root fallback、安裝、cgroup 或 service mutation 都不允許。

每 child stdout+stderr 合計8192 bytes；三次最大24576、aggregate ceiling仍32768。超額只保留 bounded prefix並標記OUTPUT_BOUND，不把截斷當完整查詢。pidfd確認直接child exit，PID/start與session group保持到signal之前；5s soft query加1s cleanup，讀/Hash有byte限制、整組30s soft gate。這不是OS hard envelope，scheduler延遲或不可中斷I/O沒有有限hard保證。

固定讀取最多8層，每層9介面、每檔256 bytes；單snapshot32768 bytes、before/after兩份。proc status/mountinfo等是有界輸入，只保留必要投影。過長procs/lineage或snapshot拒絕，不截斷，不遞迴掃全機。兩份snapshot pin各cgroup directory FD；boot、mount/cgroup/pid namespace inode、process start、UID/GID、cgroup dev/inode before-after必須一致。多檔仍非原子交易。

只在單執行緒、預設SIGCHLD、Linux pidfd可用時啟動。owned session group在直接child未reap前以原start identity核對，SIGKILL清理；wait及group-absent不能確認即UNKNOWN，停止後續query，無PID fallback、無自動重試。這不保證能回收惡意逃離session的程序；只准所審systemctl、no-pager及封閉環境，未知binary/版本不能執行。

user private socket必須事先存在且屬當前UID；缺少即skip並記UNKNOWN，不start/enable/linger。v255內部可能從private fallback至default user bus；環境將DBUS_SESSION_BUS_ADDRESS固定為unix:path=/proc/self/fd/-1，使失敗只能到無效FD路徑，不能回到session bus；移除 inherited SYSTEMCTL_FORCE_BUS/LD*/PYTHON*，未證 installed binary前不稱實機驗證。system bus固定既存本機socket，不使用環境remote address。

在受保護parent下exclusive建立0700單次目錄，先寫0600 attempt.json占用scope，再寫0600 receipt.json與receipt.sha256，fsync普通檔及目錄；任何同名殘留或失敗都不得重跑。父目錄不可由group/other寫入。若空間不足、receipt超131072 bytes或寫入失敗，可能只有attempt或shell錯誤；保留現場，不承諾power-loss durability、不自動清理或換目錄繞過單次規則。

systemctl連線與查詢會消耗非零CPU/RAM，可能觸發manager/journal記錄；本方案沒有日誌硬容量或host/VMM成本封裝，也不把這些成本算成0。因此是另行接受風險的diagnostic scope，不能充當S4或正式job驗收。
