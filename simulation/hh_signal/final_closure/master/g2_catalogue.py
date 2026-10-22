"""Versioned G2/G3 decision prose; factual status comes from g2_stages inputs."""
LINUX='https://www.kernel.org/doc/html/v6.6/admin-guide/cgroup-v2.html'
MEM='https://raw.githubusercontent.com/torvalds/linux/v6.6/mm/memcontrol.c'
CORE='https://raw.githubusercontent.com/torvalds/linux/v6.6/kernel/cgroup/cgroup.c'
RSTAT='https://raw.githubusercontent.com/torvalds/linux/v6.6/kernel/cgroup/rstat.c'
SYSTEMD='https://www.freedesktop.org/software/systemd/man/255/systemd.resource-control.html'
SERVICE='https://www.freedesktop.org/software/systemd/man/255/systemd.service.html'
KILL='https://www.freedesktop.org/software/systemd/man/255/systemd.kill.html'
DELEGATE='https://systemd.io/CGROUP_DELEGATION/'
TMPFS='https://www.kernel.org/doc/html/v6.6/filesystems/tmpfs.html'
JOURNAL='https://raw.githubusercontent.com/tytso/e2fsprogs/v1.47.0/lib/ext2fs/mkjournal.c'
JBD='https://raw.githubusercontent.com/tytso/e2fsprogs/v1.47.0/lib/ext2fs/kernel-jbd.h'
WSL='https://learn.microsoft.com/en-us/windows/wsl/wsl2-mount-disk'
TERMS='c01968bda61e705c25cca774372572ad8b5efb221451db21ba33c21b77682193'
VM='eedc17a761f2aaefde628d858a70bf9d4518d271df8bedcaf54f34d96cf6237d'
OBSERVER='fcbfba8c4dececd545b4f75a852a7ec4b123d67078a038d03d85772c5076364b'
BLOCKERS=['EXACT_ARCHITECTURE_TERMS_ACCEPTANCE','EFFECTIVE_MANAGER_AND_DELEGATION',
 'INDEPENDENT_FIXED_DEVICE_PROVISION','HOST_GUEST_SAME_INSTANCE_EXCLUSIVITY',
 'PROTECTED_COLLECTOR_AND_FINAL_OBSERVER','WHOLE_JOB_NORMAL_AND_FAILURE_KERNEL_TESTS','BOUNDED_CONTROL_PLANE_AND_LOG_COSTS','GUEST_ASYNC_KERNEL_COST_OWNERSHIP']

DOCS={
'G2_CPU_ACCOUNTING_PROTOCOL.md':f'''# CPU accounting protocol

原額度 S4=4,000,000 µs；BUILD=14,400,000,000 µs，是一個完整job的總量，不是每個PID各一份。新g2_protocol以單一fresh parent的cpu.stat usage_usec作累積來源，user_usec/system_usec作同一已審Linux6.6 ABI的整數一致性診斷；不再逐process加總，避免漏掉短命compiler/helper或double counting。保留parent直到collector退出後的最終readback，不能先刪群組再猜計數。ancestor可能承受其他工作；驗證的是專用job parent，不能直接拿共享ancestor總量當本job。

admission由外部trusted manager在空的新parent、counter=0時記錄。admission後才啟動controller、worker、compiler/helpers與collector；全部在parent以下、不同子死亡域。parent本身不放process，符合domain controller的no-internal-process限制。所有註冊角色以PID/start/UID及group identity綁定；protected acquisition尚未實作，因此來源驗證仍只代表input consistency。不得把JSON的membership_complete旗標當成kernel attestation。

早停比較整數累積CPU與獨立monotonic elapsed；stop_decision只產生TERM/KILL/observer請求，沒有任何signal、service或cgroup寫入。S4既有3s early-stop是保留的提案，不是剩餘1s必然足夠的證明；BUILD實際early threshold與poll/termination尾成本仍需實測及獨立審核。cpu.max/CPUQuota限每period的bandwidth；cpu.weight只是相對分配，均不是精確lifetime kill。CPUAccounting提供觀察，不提供此contract的原子總量停止。

非root cpu.stat在v6.6 rstat flush/adjust後以µs輸出，parts因整數截位允許2µs一致性容差；此容差不是資源額度加2µs。到最後observer讀取仍以原CPU cap判斷，超額一律拒絕。scheduler延遲、signal延遲、collector/cleanup尾量沒有已證明最壞有限值；不能由bandwidth乘wall推得零超額保證。

service/scope由一個manager管理，delegated subtree遵守single-writer；slice不能作Delegate對象。選擇system-manager持有parent/children，或另審service/scope delegation；不能讓systemd與自行mkdir的helper同時管理同一層。既有shell在init.scope及UNLIMITED，不證明新專用群組不能設定限制。實際owner、可用controllers、effective hierarchy、fresh admission及final acquisition仍需獨立scope。

來源：[cgroup v2]({LINUX})、[rstat]({RSTAT})、[systemd accounting/quota]({SYSTEMD})、[delegation]({DELEGATE})。只審API，沒有部署。
''',
'G2_CPU_FAILURE_MODEL.md':'''# CPU failure model

CPU-rate與lifetime-budget分開記錄。輪詢停頓、controller死亡、collector死亡、parent替換、InvocationID重播、缺counter、u64 overflow、counter reset或角色逃逸均不能接受完成。OOM/timeout/controller loss是failure；一個仍存活的collector可保留已完成slots，但不因此將job改判成功。

先要求整個worker/controller死亡域TERM，經已審grace後由獨立manager要求group KILL；collector暫留同budget parent作postmortem，再退出。最終observer在外部trusted context觀察parent populated=0、registry全部EXITED與collector PID/start綁定；完整cleanup CPU仍包含於parent final counter。外部observer CPU在B提案為manager_journal非零成本，不能用此架構聲稱原A完整成立。

collector/observer失去聯繫或收尾未確認，終態UNKNOWN、保留已commit證據，不盲目重跑；overrun終態FAIL，不能換seed、延長限額或重置總budget。沒有真實native CPU測量，本次相關欄位均null。
''',
'G2_MEMORY_CHARGING_AND_TMPFS.md':f'''# RAM, swap and tmpfs charging

一個job parent的memory.max涵蓋controller、worker、compiler、helpers、collector、可歸帳kernel/cache與tmpfs/shmem resident pages。不能給每個child完整RAM再相加。memory.events為hierarchical時不再加各child同名計數；events.local只看該層。memory_localevents mount語義須被future acquirer核對，未知則拒絕hierarchical宣稱。

BUILD work tmpfs ceiling=2,147,483,648 bytes，private=268,435,456 bytes，合計2,415,919,104 bytes，已比2,147,483,648 RAM pool多268,435,456 bytes；尚未計入process與collector。filesystem size不是預配置resident RAM，也不保證兩個tmpfs可填滿。既有ceilings不改，不能在報告中把這個配置宣稱可同時滿載。

新memory_plan要求逐項非負整數：work_resident + private_resident + process_runtime + collector + kernel_and_cache + safety_reserve <= 原RAM cap，且後四項必須非零。任何未量測/未規劃項為null就拒絕；正例只為SYNTHETIC arithmetic fixture，沒有把任意reserve當成真實runtime需求。現階段BUILD resident allocation實際可行配置仍UNKNOWN，需未來受控試驗，不能自動降低或提高上限。

須fresh私有tmpfs、排除外部writer與預先charged共享pages；否則page初始charge可能留在其他memcg，路徑名稱不保證RAM都歸此job。ancestor同時承受其他workload，會比job leaf更早OOM；需exclusive parent或明確上層約束讀回。shared host/VMM overhead另依未接受的B條款記帳，不是零。

memory.swap.max=0必須有effective readback，swap.current=0只是瞬時usage。memory.max可短暫超額；分開讀的current、peak、limit不是原子snapshot，較晚current可以大於較早peak。任一observed peak超原cap或OOM仍拒絕run，沒有證明零transient overshoot。原A若要求literal零超額，標準Linux此API不能證成。[memory]({MEM})、[tmpfs]({TMPFS})、[systemd]({SYSTEMD})。
''',
'G2_OOM_AND_COLLECTOR_SURVIVAL.md':'''# OOM and protected evidence

worker/controller子死亡域與collector子域分離，但同一parent RAM/CPU pool。這減少worker失敗直接殺掉collector的機會，不保證parent OOM時collector存活。memory.oom.group、OOM score與manager設定都需獨立部署審查；不得假設原先MemoryMax旗標已覆蓋全部child或排除共享charge。

8×4096-byte slots中預留2個failure lanes；worker不得取得writer FD或collector UID權限。collector只寫預先核實、preallocated、受保護的fixed-device slots。UID、SO_PEERCRED、PID start、boot、InvocationID、source/config、slot身份及序號都要由future trusted acquirer綁定。現階段只有source predicates，沒有真的privileged consumer、writer保護或OOM測試。

遇OOM、collector死亡、ENOSPC或outer manager失效，只保留已commit slots並將缺失後段標UNKNOWN。重開相等/fsync ACK不能證明突然掉電後存活。final observer不得自稱觀察自己的死亡；它觀察的是已退出collector及空parent，自身生命週期留在declared external boundary。原A仍未滿足。
''',
'G2_CONTROLLER_STOP_STATE_MACHINE.md':f'''# Controller stop state machine

g2_protocol.stop_decision為純函數：RUNNING → TERM_REQUESTED → KILL_REQUESTED → DRAINING_COLLECTOR → WAIT_OBSERVER；collector/observer loss、總wall/CPU超限 → UNKNOWN。先只TERM/KILL worker/controller死亡域，collector仍計帳並限時postmortem後退出；collector-loss／deadline失敗才要求manager清全部job並保留既有commit。UNKNOWN沒有自動retry。輸入event叫FINAL_ACCEPTED也不能取代完整trace驗證或trusted capture；此函數任何分支accept=false，沒有執行kill或service。

完整順序為ADMISSION、ACTIVATION、CONTROLLER_START、WORKER、TERMINATION、POSTMORTEM、DESCENDANT_CLEANUP、COLLECTOR_FINALIZATION、INDEPENDENT_FINAL_OBSERVATION。每個sample有start/end monotonic、序號、job identity及phase budget；phase總和不得超過原S4 13s／BUILD14400s，最後端點不得用Main PID exit替代。時間單位只用checked整數ns。

future部署需事先武裝獨立manager deadline；RuntimeMaxSec只對active runtime生效，start/stop另外設定TimeoutStartSec/TimeoutStopSec。KillMode=control-group只清該unit的群組，不能據此推論其他sibling collector或parent已空；需外部管理整個job registry。SIGTERM後grace與SIGKILL fallback仍受普通scheduler延遲，沒有硬即時保證。[service]({SERVICE})、[kill]({KILL})。

observer最後時間是收集完final kernel readback的end；後續receipt序列化/commit及observer自身termination是B supplement明載的external非零成本，不能偷偷算成原A已全涵蓋。若沒有最終committed receipt，終態UNKNOWN；不能用一個已死亡collector自己的宣告補足。
''',
'G2_HOST_GUEST_ACCOUNTING_GAP.md':'''# Host/guest accounting gap

原A保留所有相關host/guest成本在同一總額。Linux job parent能歸帳它的descendants；不能單靠cpu.stat/memory.max歸帳Windows launcher、shared WSL VM/VMM、system-manager及journald/rsyslog。Windows inventory 13/13只是拓樸query coverage，不是joint host+guest lifetime CPU/RAM或allocated storage enforcement。

來源中已有G1-G7_RESOURCE_LEDGER，但未部署joint enforcer；本次將每個role的owner、CPU/RAM/disk歸屬、wall端點、counter、未觀察成本列入A matrix。沒有另給每個role一份4s/512MiB，不將external角色填0。固定device的metadata、inodes、internal journal和evidence reserve在同capacity內；不能重複加journal，也不能遺漏host backing metadata/control-plane寫入。

A_NOT_DEMONSTRABLY_FEASIBLE_ON_CURRENT_HOST。這不是由init.scope的UNLIMITED推得，而是缺共同host/guest enforcer、零排程延遲/零瞬時超額證明、persistent allocated容量及完整post-exit證據。也不是宣稱所有受控Linux或專用平台都不可能；若保留A，須先提供滿足這些原始強保證的實際平台/形式化契約，不虛構替代機器已存在。

新辨識的成本歸屬缺口：filesystem/journal的fixed-device容量不是CPU enforcer。writer程序CPU可在parent，但異步kernel writeback/journal工作是否完整歸帳尚未證明。不能偷偷將它加進三個external角色或假設是0；B條款如不足以涵蓋此語義，需另作精確邊界審查，原件不改。matrix保留WRITER_PARENT_PLUS_ASYNC_KERNEL_UNVERIFIED，不聲稱現有B已封閉全部成本。
''',
'G2_PATH_A_VS_B_COMPARISON.md':'''# Path A versus B

| 比較 | A：原契約 | B-V2：待接受的WSL研究架構 |
|---|---|---|
| 可行性 | 此host未證成joint全部成本與強停止 | Linux documented hierarchy可作候選；manager/delegation權限未驗證 |
| 重現性 | 需同時固定Windows/VM/kernel與全成本capture | 固定job/source/device/observer，external成本另報；仍需真實readback |
| 安全 | 原始保護與零超額要求不放寬 | root/history/device保護保留，CPU/RAM暫態及external邊界較弱 |
| 複雜度 | 缺joint host/guest enforcer，工作量未可量測 | 可重用controller/slots/ledger；新protected acquisition與observer未部署 |
| 科學用途 | 未成立前不能啟動物理 | 可接受overshoot失敗判定及external成本時較實際，但不是ATLAS認證 |
| 依賴 | 實際受控平台＋全部原A強保證 | 條款、manager、fixed device、exclusivity、protected observer、kernel正反、bounded logs |
| 剩餘風險 | 沒有證成上界 | scheduler/outer失效、OOM、外部成本及durability未知，均需明示 |

B的8組阻擋由具名清單計數（另含guest異步kernel成本歸屬），不是概率或信心分數。沒有新硬體可用證據。普通大physical disk不能只切4MiB filesystem來冒充已審S4 4MiB whole-device identity；fixed virtual LUN亦須不grow、不thin/sparse、不在protected backing，並另證allocated成本與host-writer排除，現在沒有合格candidate。

推薦先審B-V2三份exact文件，而不是繼續把source-only工作當作A的實機驗收。若不能接受較弱邊界，停止此WSL部署路徑，先找能提供原A實際證據的平台；不自動遷移或安裝。
''',
'G2_RECOMMENDED_ARCHITECTURE_ZH_TW.md':'''# 建議架構

推薦路徑為 **B-V2候選＋VM成本歸屬＋collector退出後的獨立observer**，仍為PROPOSED_NOT_ACCEPTED。理由是已有Linux介面觀察與source可重用，能明確設計一個job parent和受保護子域；不存在的joint host/VMM強保證不應由更多Python tests代替。

建議使用由一個受信manager管理的parent hierarchy；worker/controller與collector分開死亡子域，CPU/RAM使用共同parent counter和cap；external manager的final observer從外部確認collector已退出與parent空。若走delegation，必須service/scope與single-writer，不能Delegate=slice；不部署任何新unit或猜UID。

保留4固定seed、原CPU/wall/RAM/swap/disk、1job/1worker與0retained events。BUILD兩tmpfs不能同時滿載於2GiB；需先有可審resident模型及measurements，不能因此降限制或把shared page免費外移。S4通過也僅能是有限語義驗收，不能使原A FULL true。

本次建議不是使用者已接受，也不構成diagnostic、provision、format、mount、S4、BUILD_ONLY或physics approval。
''',
'G2_MINIMUM_DECISION_REQUIRED.md':f'''# 最小使用者決策（不在本次要求執行）

先決定是否願意逐條審核較弱的B-V2語義：允許明列external非零成本、普通scheduler的早停／overrun拒絕，以及memory.max的暫態語義。若不接受，原A維持，不部署WSL候選。

需要明確綁定的三份原件SHA256：

- B1–B8 terms：`{TERMS}`。
- VM cost assignment：`{VM}`。
- Post-exit observer supplement：`{OBSERVER}`。

附件terms引用只有57字元，不能作SHA256批准binding；以上是原件與既有assignment相互核對的完整hash，沒有修改條款。B1–B8逐條decision、VM assignment與observer均仍NOT_ACCEPTED；任何單一含糊回覆不能自動補滿所有欄位，更不能產生approval token。

架構接受前尚需處理guest異步filesystem/journal CPU是否完整歸帳；不能把fixed-device容量當作此CPU證明，也不自行排除新角色。如現有三份條款不能表達實際成本，先精確審查所需補充，不修改舊條款、不自動接受。

下一個可審scope可先是單次、非管理員、唯讀的effective manager/delegation/tool identity診斷，僅收集決策資訊，不要求先接受B。現在不執行，也不啟動WSL；精確proposal見G2_EFFECTIVE_STATE_DIAGNOSTIC_PROPOSAL.json，尚缺tool binary identity而不是execution-ready。之後device provision/format/mount、kernel正常與故障測試、S4、正式build、binary binding與物理restart各自另審。
''',
'G3_REAL_GAP_CLOSURE.md':'''# G3 genuine source gaps closed

保留舊resource_trace與job_envelope，未修改歷史runtime/guard。新g2_protocol提供版本化pure contract/trace decoder、observer verification、checked integer memory模型與stop-state請求函數。

實際重現的舊缺口：(1)舊final observer只靠不同字串，不能綁定PID/start/UID/source/slot及同一預期job；(2)舊raw reader把空direct cgroup.procs等同空subtree，會拒絕parent無direct process、children仍活著的合法hierarchy。新decoder區分direct members與populated subtree，並保留seq_file可能重複PID的明確dedup診斷。

新trace綁定外部預期boot/Invocation/run nonce、parent dev/inode、source/config/slot、role registry與每個PID/start/UID。final observer必須位於job death domain之外、非worker UID、符合獨立source identity；綁定collector exit與slot commit。階段順序、sample windows、CPU parts/reset/overflow、local/hierarchical events、peak reset、OOM、swap、resurrection、missing registry與實際最終CPU/wall超額均拒絕。

source-only positive永不輸出actual enforcement verified。舊live reader不適用此新parent/children拓樸；新decoder尚未接到真實protected acquisition/manager。這個migration是明確runtime blocker，沒有偷偷把新pure協定視為已修好production controller。
''',
'G3_FINAL_OBSERVER_PROTOCOL.md':'''# Independent final observer V2

consumer先取得trusted acquisition的expected contract，不能從不受信trace抄自己的identity當expected。包含boot、InvocationID、run nonce、parent dev/inode、source/config與slot SHA；registry含controller/worker/collector及所有designated helpers的PID/start/UID/group。registry必須由未部署的受保護manager確認完整且封閉migration，不能只相信JSON布林值。

最後observer在parent與所有job child death domains之外，使用獨立PID/start、UID與source hash；外部成本只在未接受的B supplement proposed manager_journal歸屬，原A未滿足。observer只能觀察collector已退出，不能自證自己termination。

九個phase sample windows含同job identity、sequence、registry hash、role states、parent raw cpu/memory/events/procs與membership讀回。最後還有observer actor/source、observed collector PID/start、postmortem SHA、slot identity/complete。cpu.stat應在collector退出後、parent移除前flush/read；若group已消失或缺counter則UNKNOWN，不補0。

final populated=0、direct members空、完整owned registry EXITED及獨立掃描無descendant必須一致。過早Main PID exit、unit消失、collector自己的empty聲明不能接受。protected slot落盤失敗、observer死亡或timeout只保留既有commits，不重跑。raw acquisition、UID/FD/peer credential保護、slot writer及manager部署仍缺，任何通過只稱PASS_G2_TRACE_INPUT_CONSISTENCY_ONLY。
''',
'G4_G7_MINIMUM_OS_CAPABILITIES.md':f'''# Minimum deployable OS capabilities

G4：需要真正可拋棄、固定容量、whole-device、獨立host backing、完整root/history排除、stable host↔guest identity與all-writer exclusion。WSL官方支援管理員attach未被使用的whole disk，不能attach Windows安裝盤；這只證明API路徑，不證明本機有合格裝置或lease。[WSL]({WSL})。不選目前任何Windows/Ubuntu disk，不提供猜target的可執行format/mount命令。

G5：4MiB、1KiB blocks、128 inodes、1MiB internal journal的核心幾何在e2fsprogs1.47.0 source下可相容：4096 blocks的default journal為1024 blocks，JBD2 minimum亦1024。inode table為32KiB，journal與metadata包含在4MiB內。這不是實際mke2fs執行；features、fast_commit/orphan_file、mke2fs.conf、工具build與精確free blocks/inodes尚待固定與readback，不能省略配置或擴大device讓測試綠。[journal sizing]({JOURNAL})、[JBD]({JBD})。

G6：保留既有geometry/header pure verifier。未來須固定device instance與UUID，核實FS block_count×block_size、allocated backing而非sparse logical length、inodes、internal journal、兩failure lanes與32KiB slots reserve；正常/block/inode ENOSPC/torn/reopen等獨立實測。fsync ACK不等於power-loss durability，outer device/host flush boundary需另審。真正FS與readback目前均無新增。

G7：一個manager/單writer、合法delegation、專用parent及子域、protected collector UID/FD、swap0/effective ancestors、bounded stdout/manager logs、post-collector observer、完整cleanup、capacity與failure slots缺一不可。不得只用LogNamespace或user-session存在推斷整個control plane已受限。維持無service啟動argv、無mount、無collector deployment。
''',
'G4_G7_NEXT_APPROVALS.md':'''# Later approval sequence

1. 精確B條款／VM／observer邊界決策；或保留A並提供可證成原契約的平台。
2. 另審單次唯讀effective manager/delegation與工具身份診斷；不得以舊capture證明當前boot。
3. 管理員提供全新獨立fixed device及host/guest identity/exclusivity方案。先驗證不是protected/root/history，target未知保持null。
4. 另審provision、source/helper、UID/FD/namespace/log boundary及rollback；之後才能分別申請format與mount。
5. 真實FS readback、allocated blocks/inodes、journal/failure reserve；然後精確S4正常與故障kernel scope。不得自動retry。
6. 完整CPU/RAM/wall/disk/evidence/cleanup驗收後，另審正式BUILD_ONLY；build後binary/source/dependency binding，再另審zero-ME與物理restart。

本檔不批准任何一步。原4seeds、4h CPU/wall、1job/1worker、5GiB、0retained不重置、不擴充。S4僅可在其實測範圍標PASS_S4_VOLATILE_RUNTIME_WITH_LIMITS，原A FULL=false。
'''
}

def clause_rows():
 meanings=[
 ('B1_BOUNDARY','一個job pool；只將三個具名shared角色記為external非零成本。','可重用Linux hierarchy，不能joint量測Windows/VMM。','放寬原A成本邊界；job descendants與寫入不排除。','保留S4 4s/512MiB、BUILD14400s/2GiB總量；external CPU/RAM仍null。','是否接受manager_journal、launcher、host_backing三項外部歸屬及VM residual明列？'),
 ('B2_CPU','bandwidth＋累積parent counter＋early stop，最後超額拒絕。','cpu.max不是lifetime總量kill；新pure protocol可檢查全parent尾量。','允許非即時停止語義，不能稱零overshoot。','4,000,000／14,400,000,000µs unchanged；early tail最壞值UNKNOWN。','是否接受observed-overrun拒絕而非原子總量零超額保證？'),
 ('B3_WALL','trusted admission到independent final readback；普通scheduler。','active RuntimeMaxSec不含完整start/cleanup。','外部observer與receipt尾成本須明列。','13／14400s unchanged；無有限排程延遲測量。','是否接受普通scheduler及指定final-readback端點，不要求零延遲？'),
 ('B4_RAM','parent memory.max，實際swap.max=0與peak/events。','Linux可暫態超額，tmpfs resident也歸帳。','放寬literal零transient overshoot；OOM/peak overcap拒絕。','512MiB／2GiB、swap0 unchanged；BUILD tmpfs full比RAM多256MiB。','是否接受Linux記憶體語義，並要求先補resident allocation及實測？'),
 ('B5_DISK','獨立可拋棄fixed whole device；所有job writes與evidence計帳。','現有device/same-instance guards可重用，無合格本機candidate。','root/history保護不放寬；不能用C-drive VHD/shared-root代替。','S4 fixed FS4MiB、BUILD fixed2GiB為未執行提案；metadata/journal不重複計。','是否保留此不放寬的device安全門檻，另行提供合格device？'),
 ('B6_EVIDENCE','分離collector死亡域、同parent budget、固定slots。','pure source不是UID/FD保護或durability部署。','outer失效可留下UNKNOWN，不承諾power loss。','8×4096=32768 bytes，2 failure slots，不增加disk ceiling。','是否接受outer loss時僅保留committed checkpoints與UNKNOWN？'),
 ('B7_CLEANUP','所有owned descendants退出，collector後由外部observer讀空parent。','新V2綁定observer PID/start/source/slot，未部署acquirer。','observer自身termination不能自證；外部非零成本需接受。','collector尾CPU仍在同parent；final observer成本null而非0。','是否接受該exact post-exit observer supplement及成本歸屬？'),
 ('B8_RELEASE','接受條款不等於provision、kernel、S4、build或physics授權。','每個live gate需要exact source/input與獨立scope。','不放寬release與歷史保護。','4 fixed seeds與零retained不變；本任務新ME/integrals/events=0。','是否同意條款決策與每個後續execution approval嚴格分開？')]
 return [{'clause':i,'proposed_meaning':m,'technical_justification':j,'expected_safety_impact':s,'quantitative_resource_consequence':q,
  'current_evidence':'IMMUTABLE_G1_PLUS_SOURCE_AND_SYNTHETIC_TESTS_ONLY','remaining_uncertainty':'EFFECTIVE_CONFIGURATION_AND_ACTUAL_JOB_ENFORCEMENT_UNVERIFIED',
  'recommendation':'REVIEW_EXACT_MEANING_BEFORE_ACCEPTANCE','original_A_weakened':i in ('B1_BOUNDARY','B2_CPU','B3_WALL','B4_RAM','B6_EVIDENCE','B7_CLEANUP'),
  'exact_human_decision_required':d,'decision':'NOT_ACCEPTED','user_accepted':False,'execution_authorized':False} for i,m,j,s,q,d in meanings]
