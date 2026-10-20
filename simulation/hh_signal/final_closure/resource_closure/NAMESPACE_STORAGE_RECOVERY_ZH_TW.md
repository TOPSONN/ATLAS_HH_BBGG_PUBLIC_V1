# Phase7I namespace／storage recovery

本版僅包含 source engineering 與離線驗證。**本輪沒有新 kernel／service／stress invocation 授權**。`launch-live-diagnostic` 現在無條件拒絕；`describe-diagnostic` 只輸出待審 argv，不建立 service、namespace、授權或輸出目錄。正式 build、native zero-ME、ME、integration、events 均未授權，兩個 FULL flags 為 false。

## Mount 診斷修補

`mount_attestation.py` 有界讀取 mountinfo，解析 mount/parent IDs、device、root、mountpoint、mount flags、optional fields、filesystem、source、superblock flags，正確處理四種 kernel octal escapes。per-mount ro 與 superblock rw 分開判斷；後者不能推翻 readonly bind。重複／模糊 mountpoint、malformed／超限輸入一律拒絕。

在 parser 或 guard 拒絕前，controller 先送出 private 原始 bytes 分片、SHA256、完整／截斷標記，再送 safe inventory。原始 capture 上限16KiB、256 rows；超限僅保存 bounded prefix，明列 incomplete，拒絕繼續，不能稱作完整 mount 表。safe projection 也限16KiB。原始 capture 只留本機，public evidence 必須經人工內容審查後僅保留安全投影和原檔 SHA256。

分類包含 private tmpfs、source、精確 type/path 的 kernel pseudo-filesystem、persistent、unknown。分類不等於放行：沒有新 writable pseudo exception，除了既定 `/tmp` 與 `/var/tmp`，其他 rw 仍拒絕。兩個 private tmpfs 還須精確 source/root/type/security flags、statvfs byte/inode cap。沒有刪除 mount guard，也沒有把 `/dev`／`/proc`／`/sys` 子目錄無條件列為可寫白名單。

舊 Pre 只有拒絕理由，缺少 mount 清單；本輪不能追溯證明哪個 mount 是 false positive。這是診斷與解析修補，尚未實測解除該 blocker。

## 等價隔離架構提案

上游 systemd v255／v255.4 會對各 Exec 命令建立個別 user namespace，但同一 service 可能重用 net／IPC namespace FDs。Linux setns 要求 target owner userns 的 capability，支持 sibling-userns 權限不符的假說。舊 journal 只有 EPERM／226，沒有 owner/syscall trace；exact Ubuntu patched-source 差異尚未取得，根因保持推論。

新提案只用一個 ExecStart，將 preflight／postflight／failure-finalization 放在 Main 內，child 繼承 Main 的 namespace。`ExecStartPre`／`ExecStopPost` 為 NOT_USED_BY_PROPOSED_ARCHITECTURE，不算通過舊命令的實測。保留 PrivateUsers／PrivateNetwork／PrivateIPC=yes、RestrictNamespaces、NNP、capability 空集合、readonly source/cgroup、固定 tmpfs、所有原資源 caps；沒有透過停用隔離解決錯誤。

威脅與界線：同一 Main 避免第二個 sibling userns 回到 manager 快取的 net／IPC；child 不建立新 namespace。一般 Python 例外保留原錯誤並做有界 finally；SIGKILL／OOM 後 Python 無法寫完收據，必須保留 INCOMPLETE，依 manager／kernel 清理證據另行判讀。取消自訂 StopPost 不是完整 abrupt-death finalization 的證明，也不解除 storage blocker。

`namespace_attestation.py` 未在本輪實際呼叫 ioctl。未來單次獲准的 service 才可用 readonly nsfs NS_GET_NSTYPE／NS_GET_USERNS 讀回身份，核對 net／IPC owner 為本服務 private userns、非 initial/full UID/GID maps、cap0、NNP1、seccomp2、只有lo；child 必須保留相同 namespace identities。任何拒絕、缺測、type／owner／FD cleanup 不符都保持 UNKNOWN／FAIL。manager 顯示 yes 不能取代這些讀回。

child 診斷採固定 kind、嵌套 wrapper、record/byte/depth caps；偽造 Main 完成或任何 FULL=true 診斷都拒絕。private stderr／mount raw frames 不能透過 public JSON、JSONL、Markdown 或 encoded wrappers 發布。

## 資源與 persistent storage

Harmless 上限維持 CPU4s、wall13s、RAM512MiB、swap0、work8MiB、private1MiB、total disk16MiB。單 Main 設定 activation1s、runtime8s、stop0.5s、保守 final kill0.5s，timer計算10s、30%quota加period carry為3.003 CPU s；這是設計計算，沒有 realtime 或 kernel 驗收宣稱。

未來 formal 提案維持 CPU/wall14400s、RAM2GiB、swap0、1job/worker、5GiB、retained LHE0，未執行。

Storage A quota、B fixed backing filesystem、C fixed FDs 均須證明 allocated blocks/inodes、extent／metadata／journal／tmpfs accounting、bypass 與失敗收據。當前沒有可核實 backend。C 僅可作 transport，FSIZE／logical size／事後 st_blocks／IO rate 不等於完整容量。FUSE device／libraries 存在不等於已安裝並審查可用的 fixed-image driver。任何 admin quota、mount、安裝或主機變更需另行提出，不會自動執行。

## 測試和後續授權

固定離線集合保留既有207個 test IDs、81 safe legacy 與47 fixture規格；舊45個controller測試僅調整 fixture／單Main架構介面及更嚴格 launch 拒絕。另補 mount parser、namespace ownership、失敗前capture順序、child forged claims、publication 私密資料負面案例。這些是 mock／synthetic source evidence，不能取代新 service 執行。

另以真正 readonly `check_revision(full=True)` 量測完整 tracked source 成本；未在受限service內執行的成本不能宣稱已符合完整 kernel budget。

下一次需提交 exact committed revision、argv、fresh output、既有 caps、stop conditions，另取明確人類授權。第一個範圍僅為 namespace／mount inspection，沒有child／八階段／正式build；完整 lifecycle仍受 persistent hard-bound blocker 限制。request 文件不是授權物件或可重用 token。
