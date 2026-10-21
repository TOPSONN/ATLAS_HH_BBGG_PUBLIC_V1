# 管理員架構比較與精確資源邊界

狀態：DESIGN_REVIEW_CANDIDATE。未授權 provisioning、S4 或任何 build。選定 Architecture A 作為滿足原合約的工程目標；Architecture B 只作明確較弱、尚未接受的備選。兩者目前都不具執行准入。

## 不可變的原合約

S4 是全工作合計 CPU4s、activation→cleanup wall13s、RAM512MiB、swap0、disk16MiB、1job／1scientific worker。未來 BUILD 是 CPU／wall14400s、RAM2GiB、swap0、disk5GiB、1job／1worker。原104-token S4仍未授權，舊 Python watchdog不被替換或當成新架構已部署。

CPU/RAM/disk 是一個 shared aggregate pool，不能每個role各領一份4s／512MiB／16MiB。wall從可信管理端接受啟動、尚未建立worker時開始，到全部本工作程序終止、postmortem bounded capture與cleanup證據收尾才結束；不能從Main入口才開始，也不能把collector結束移到計時外。管理端與主機的額外開銷若無法計入，就不能通過原合約。

## Architecture A：選定的嚴格目標

拓樸：可信host guardian／collector → 專用可丟棄VM → guest可信controller → 單一不可信worker。worker與controller的死亡域分開；collector在VM外，可在兩者死亡後保留已同步checkpoint及獨立觀測。VM外不代表預算外：host guardian、collector、虛擬磁碟寫入、launcher、與本工作相關的manager/log成本全部列入同一aggregate邊界。

| 元件 | 信任與可寫路徑 | 計帳／死亡行為 |
|---|---|---|
| scientific worker | untrusted；僅work/private tmpfs，沒有evidence FD | VM內worker子域；1個scientific worker；worker被kill不得影響已寫evidence |
| guest controller | trusted；work tmpfs及有界collector protocol pipe | 納入同一CPU/RAM/wall；死後只能由collector觀測，不能替它發明terminal |
| host collector | trusted；8個固定protected slots | 獨立於worker/controller，仍計入同一aggregate；自身死亡或outer budget耗盡後只剩先前checkpoint，終結UNKNOWN |
| guest/host manager與logs | trusted；只准另審的bounded control state/log store | 含unit activation、journal/forwarding、failure logs；不能把guest filesystem上限當host日誌上限 |
| launcher／hypervisor | trusted；另審的控制狀態與log位置 | 啟動、VM執行、停止及cleanup的CPU與wall都要算；不能用CPU rate代替累計截止 |
| host backing | trusted；固定裝置與其metadata | host與guest身分圖需相符；若是VHD，container/header、外層blocks/inodes/journal、cache/flush都要計入 |

Guest建議使用不可改的、hash-pinned base與固定writable store；沒有已供應的base、hypervisor或新裝置。若建立新的readonly base image，其新增allocated bytes仍要計帳，不能因readonly便排除。額外裝置、VM image、host state總額超出16MiB／5GiB時，原合約即失敗；不得自行增加上限。

磁碟帳：S4既有work8＋private1＋候選persistent4＝13MiB，餘額3MiB尚未分配或強制封閉；未來build既有tmpfs2.25＋候選persistent2＝4.25GiB，餘額768MiB亦同。這些是不可超出的已知需求，不是可用的host-control-plane容量證明。所有metadata與internal journal在自身固定裝置內，外部container/host metadata不會自動消失。VM方案必須先交出整個實體配置帳本，不能先建立VM再補算。

所需但目前未證明的控制能力：

1. 可限制所有guest及相關host執行的共同控制域，能量測並停止累計user＋kernel CPU；總額含guardian/collector，不能只讀guest CPU或設定CPU百分比。
2. 獨立於guest Python排程的wall watchdog，啟動前已armed；逾期能終止整個執行樹。一般非realtime WSL/Hyper-V設定不能被寫成無延遲保證。
3. RAM與swap的精確計帳語義。memory.max是Linux標準限制，但特定情況可暫時超限；原驗收若堅持零超調便繼續BLOCKED，不修改validator。
4. 固定guest/host writable容量與inode池，所有log轉送關閉或導向已計帳受限區；不能影響歷史logs。
5. 工作程序身分、VM/vCPU/collector對應與死亡後可讀的原始counter retention；capture在unit卸載前建立，缺失一律UNKNOWN。

目前沒有審查過可同時實現上述累計CPU、whole-wall及全部host allocation的WSL部署。A是嚴格架構設計，並非「已找到可直接安裝的VM設定」。若管理員無法提供這些能力，停止原合約路線，不執行provisioning。

## Architecture B：保留WSL，候選V2修約，不是原規格PASS

拓樸：既有WSL/systemd infrastructure（external trusted）→ 一個受限aggregate parent → trusted collector、trusted controller、untrusted worker三個子域。collector不放在worker/control單一死亡域；outer budget耗盡或host死亡仍只能保留最後checkpoint。每個子域CPU/RAM合計仍受原數字限制，collector不是免費的第二個工作。

worker不能存取protected evidence，IPC須定長、限量、驗證peer UID/PID/starttime與run/boot身分。collector獨立採樣原始cgroup與manager資料，不把worker宣稱當native事實。UID分離、namespace/FD、capability與mount白名單均須另審，不能臨時chmod。systemd255 LogNamespace不支援user service，不能單加旗標解決外部日誌。

V2明確排除三類現有共享host成本：manager/journal infrastructure、Windows/WSL launcher、host backing管理成本。它們由主機管理員負責，不能在現有共享WSL中宣稱逐job硬計帳。候選檔完整列出這些external roles，status=PROPOSED_NOT_ACCEPTED、weaker_than_original=true、user_accepted=false。這是較弱合約，尚未接受；原16MiB／4s／13s與未來5GiB／14400s保持原樣。沒有任何程式會把V2自動切成生效或改舊FULL旗標。

## 最小部署決策順序（全部非執行）

1. 先審A的控制能力與host/guest實體帳本；不能只送一個小磁碟。若A不可提供，使用者才決定是否審B的V2例外；沒有默認同意。
2. 定義獨立collector的生存域、UID、32KiB fixed-slot reserve、IPC上限、資源owner、raw採集與unit pinning。包括collector自身crash及outer OOM；不能承諾死亡後再寫新結果。
3. 管理員提供真實host/guest device topology與完整protected storage清單。source guards只檢查資料一致性，不驗證JSON的真實來源，也不是操作權限。
4. 審查真正同FD消費的privileged helper及exclusive/hotplug邊界。現有mkfs/mount路徑重開方案不可用。
5. 上述source、device/namespace/helper身分精確freeze後，才依管理員文件逐項批准inventory/provision/format/mount。無一步含S4。
6. 之後另審無害kernel正反測試與單次S4。原542 offline與81 legacy成功不替代該證據。Full完成後才準備BUILD_ONLY，binary/physics各自另審。

本設計可供獨立審查，但ADMIN_PROVISIONING_APPROVED=false、FULL_LAUNCH_ENVELOPE_VERIFIED=false、S4_EXECUTED=false、BUILD_ONLY_AUTHORIZED=false、PHASE7I_PHYSICS_VALIDATED=false。

主要來源：[Linux6.6 cgroup](https://www.kernel.org/doc/html/v6.6/admin-guide/cgroup-v2.html)、[systemd255 resource-control](https://www.freedesktop.org/software/systemd/man/255/systemd.resource-control.html)、[systemd255 exec](https://www.freedesktop.org/software/systemd/man/255/systemd.exec.html)、[WSL磁碟附加](https://learn.microsoft.com/en-us/windows/wsl/wsl2-mount-disk)。來源語義與本機實際部署證明分開。
