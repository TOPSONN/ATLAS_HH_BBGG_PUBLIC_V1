# Phase7I S4 與持久容量驗收報告

判定：SOURCE_REPAIR_VERIFIED_OS_CAPACITY_AND_S4_BLOCKED。來源修補、OS 現況調查及獨立審查已完成；尚未解除真正的持久容量與控制平面阻擋。S4 未執行，沒有 FULL PASS，也尚不適合請求正式 BUILD_ONLY。

**精確來源與保存**

Base PR35 HEAD cd6b43202318560492491104f994312133e8e436；原 tested source 114b5c00341be22982244d3d9548e80adf2d00e5。新 exact tested source 74f8dc3dd53502a430676c7327a4eb8801f7afca。本次獨立分支為 codex/phase7i-s4-persistent-capacity-closure；新的 stacked Draft PR 與最終 report-only commit 由 GitHub PR metadata／本機 DELIVERY.json 記錄，以避免把報告自身 commit hash 寫入自身。

原104-token argv、21份身分逐項核對相符。授權工程修改使其中7份改變，因此本次以新334份 source/config/workflow manifest 綁定新 revision，沒有將舊21份身分冒充新 executable identity。fresh exact checkout 為 /home/btu/projects/atlas_hh_phase7i_s4_74f8dc3d_capacity_01，normal .git、detached、official origin。實跑兩次普通完整 Git preflight，各1509 tracked／330 critical；host wall 分別0.692232314s／0.713603961s、CPU0.487346631s／0.469009327s。這是普通唯讀 preflight，沒有啟動受限 service，也不證明 borrowed watchdog 已在 kernel envelope 中成功。

科學 physics contract、guard三個依賴及既有 profiles 未變；921個 base tracked 歷史 reports/data/evidence/cards/figures 路徑無 Git diff。舊449 IDs、45個 controller methods 全保留。外部並行 MC 資料本輪未掃描，不能重用先前全量 hash 當成本輪證明。舊 PR、來源、失敗及原始 receipts 全保留。

**S4 readiness：BLOCKED**

proposed_kernel_scope.json 完整列出新 exact source、manifest digest、104-token argv、新 unit atlas-hh-phase7i-s4-capacity-01.service。範圍仍為一個 eight-phase Main workflow、一個 inert child、1 guard、initial7個 nsfs 唯讀 ioctl、最多18個固定 invalid-target calls，0 stress、0自動 retry、0 MG5／physics。

CPU4s、whole wall13s、RAM512MiB、swap0、work tmpfs8MiB、private tmpfs1MiB、disk16MiB、1 job／1 worker 不提高。CPUQuota30% 是 bandwidth，LimitCPU2s 是 per-process；manager runtime8/start1/stop0.5 不等於 activation→cleanup13秒保證。新程式對 aggregate absolute cpu.stat 使用量到3s及 Main-origin wall10s提早停止，以10ms同process SIGALRM觀察；這是 source implementation，並非 atomic整組4秒 hardkill 證據。

Python handler 有 scheduling／throttle／C blocking／OOM／SIGKILL限制，pre-arm 初始同步讀取與close後return亦有邊界。controller仍活著不能自稱cleanup empty；Main self-exit後是否整組終止仍須實際manager/cgroup證明。缺失、已刪cgroup或unloaded unit均 UNKNOWN，不能轉換成零。

現有 stdout64KiB／S3 logical slots／tmpfs診斷不足以證明 persistent blocks/inodes/metadata/journal。正常 --pipe／journal亦不能保證controller死亡後保留失敗證據。因此這是精確的未授權審查套件，next_authorization_request_ready=false；尚不可直接執行。

**Persistent backend selection：管理員新專用固定容量 block device**

實際 /home ext4 為 /dev/sdd、8:48、共享1TiB root裝置。對user/group/project的6次 GETFMT／GETINFO 均回ESRCH，匹配WSL6.6.87.2來源表明目前沒有 active accounting；不是從 mount旗標或工具缺少推論。raw superblock因權限拒絕，quota/project feature仍UNKNOWN；沒有找到既有專用小容量filesystem。

本輪最初另外執行3次 GETQUOTA，之後來源審查發現這個GET操作屬potential write-class，可能配置dquot，故立即停止且沒有重試。user/group ESRCH、project EPERM皆失敗；匹配版本來源推論在這些路徑尚未取得dquot。沒有量測allocated-block delta或證明所有host寫入為零；原始9-call收據與更正紀錄保留。未來唯讀檢查只提案GETFMT／GETINFO。

目前systemd255.4、journald與rsyslog active；ForwardToSyslog=yes，journal/syslog涉及共享root ext4，user manager部分limits為infinity。沒有已驗證的per-job allocated blocks／inodes硬限制涵蓋這些輸出。因此選擇新、非thin／sparse、不可成長的專用block device，避免變更root quota／remount；目前尚無該裝置，不能宣稱backend PASS。

| 提案 | 專用volume（含內部journal／metadata） | 保留tmpfs | 已知總額 | 未強制封閉reserve |
|---|---:|---:|---:|---:|
| S4 | 4MiB；1KiB blocks、128 inodes、1MiB internal journal | 8＋1MiB | 13MiB／16MiB | 3MiB |
| 未來build | 2GiB；4KiB blocks、32768 inodes、32MiB internal journal | 2GiB＋256MiB | 4.25GiB／5GiB | 768MiB |

reserve只是算術，不是OS enforcement。新volume無法自行包住外部manager/journal/syslog；完整容量仍BLOCKED。未來不能用4GiB volume加既有2.25GiB tmpfs冒充5GiB。

**Required administrator action**

ADMIN_ACTIONS_ZH_TW.md 提供未執行的精確 guard、dry-run、新裝置格式化、post-format UUID/header digest、mount、blocks/inodes readback與rollback步驟。先由管理員提供stable by-id、major:minor、exact size、非thin ancestry、root:root0600 raw-device及root-owned mountpoint證據；本文不猜裝置編號。placeholder未填必須STOP。

格式化前必須空白signature，格式化後另停下審查新UUID／geometry/header hash，掛載前使用不同guard；不加force、不自動套用、不修改root或既有資料。新裝置內部journal、inode table、bitmaps與metadata均納入容量；尚未實際建立或驗證4MiB幾何。mountpoint本身的host inode與外部日誌仍要記帳。完整控制平面配置、預配置failure slots及獨立postmortem capture必須另審，不能只把stdout換路徑便PASS。

另授權的正反測試須涵蓋實際blocks/inodes ENOSPC、metadata／journal、partial capture、controller loss、OOM／timeout、殘留程序與失敗checkpoint。rollback只針對新mount，保存證據、確認writer停止及exact device後才umount；不lazy unmount、不刪歷史logs、不重格式化。

**Actual source modifications**

保留既有八階段controller與45項methods。新增純數值／有界raw parser job_envelope、pure storage receipt/geometry verifier；接入累計CPU early-stop、Main wall observation、failure terminal寫入監控及timer ownership清理。這些JSON/parser不能自行授予OS或人類能力。

GitGuard借用同一active timer，保持full tracked status/index/blob/hash/race範圍；inherited CPU/FSIZE/CORE只可降低。有界增量RAM pipe取代borrowed模式的regular temp output。所有HEAD查詢也經相同有界guard並保留1秒期限。kill出錯仍獨立wait，cleanup UNKNOWN不能變成功，原始錯誤保留。發布allowlist與CI限本分支離線審查；沒有新增runtime launch flag或授權token。

**Offline results 與失敗保存**

- 最終542 unique audited offline：0fail／error／skip，55份source前後相同，wall 1.553626138s；禁止live timers/signals/exit、namespace ioctl、非Git process、physics import。這是固定可信tests，不是一般sandbox；stat/readlink及directory-FD alias限制明列。
- 最終81 safe legacy：0fail／error／skip，48-file implementation snapshot相同，wall 8.421784369s。此舊suite實際包含普通Git、固定harmless Python與sleep cleanup fixture，不將其稱為新S4資源測試或全部OS calls為零。
- 獨立58 focused unique tests為主suite子集，0fail／error／skip；獨立review核對全部55 source hashes、CI condition與出版路徑。
- 審查找到HEAD capture與kill/wait缺口，已修補。offline_final_03實際6個missing-import errors保留；補re import後final04全PASS。早先storage與job-envelope mock失敗亦在本機hash index保留，未覆寫或刪除。

**Kernel tests actually executed 與量測**

本輪新的S4 service／resource kernel case／stress／guard install／正式build／zero-ME／MG5 parser與model import／ME／integration／event／Pythia／Delphes／HumanReview建立全部0。上面的quota查詢與唯讀OS現況調查已實作，不能與「沒有新resource kernel test」混淆。普通Git preflight與legacy fixture亦已實跑。

| S4證據 | 本輪實測 |
|---|---|
| Aggregate cumulative CPU／activation→cleanup wall | null／UNKNOWN |
| RAM peak／swap peak | null／UNKNOWN |
| Persistent allocated blocks／inodes／journal／metadata | null／BLOCKED |
| OOM／timeout／controller-loss whole-cgroup cleanup | null／UNKNOWN |
| Failure evidence durability | BLOCKED |

raw parser會綁unit／InvocationID／MainPID／cgroup identity與完整monotonic timestamps。純數字合格最多PASS_RAW_NUMERICAL_ONLY；不能證明raw origin、hard enforcement或FULL。

**PASS／FAIL／BLOCKED／UNKNOWN**

PASS：來源與離線修補、獨立review、原449/45保留、921 tracked歷史路徑保存、fresh checkout普通完整Git preflight。
FAIL：現有active quota不可用；沒有通過完整durable容量。歷史局部test failure已保留並修正，不冒充最終失敗為成功。
BLOCKED：S4執行、持久volume及整個control-plane硬限制、failure writer/capture、完整CPU/RAM/wall/cleanup正反測試、正式BUILD_ONLY。
UNKNOWN：raw superblock feature、kernel binary-source attestation、外部MC資料本輪身分及所有新S4 raw metrics。

FULL_LAUNCH_ENVELOPE_VERIFIED=false；FULL_CONTROLLER_RESOURCE_ENFORCEMENT_IMPLEMENTED=false；FORMAL_BUILD_ONLY_AUTHORIZED=false。

**下一個獨立授權動作**

先審管理員新固定裝置的exact identity與job-specific bounded logging／failure capture配置，取得特定provisioning授權；未授權前不格式化、mount或改host。必要source修補後重新freeze exact revision；當容量與capture前置條件成立，再請求一次性S4明確授權。S4真正通過亦只可標PASS_S4_VOLATILE_RUNTIME_WITH_LIMITS。Full仍需持久容量、整個CPU/RAM/wall與cleanup正反證據。全部完成後才準備獨立BUILD_ONLY，後續binary與physical restart繼續分開審。

證據入口：evidence.json、proposed_kernel_scope.json、source_manifest.json、ADMIN_ACTIONS_ZH_TW.md、local_evidence_index.json。GitHub CI結果以PR checks及DELIVERY.json為準，hosted green不能代替WSL kernel證明。無PDF/PNG、新物理輸出、merge或force push。

來源解讀：[WSL quota implementation](https://github.com/microsoft/WSL2-Linux-Kernel/blob/linux-msft-wsl-6.6.87.2/fs/quota/quota.c)、[Linux cgroup v2](https://www.kernel.org/doc/html/v6.6/admin-guide/cgroup-v2.html)、[systemd255 service](https://www.freedesktop.org/software/systemd/man/255/systemd.service.html)。OS實測與source inference在上文明確分列。
