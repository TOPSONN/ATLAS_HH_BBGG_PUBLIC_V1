"""Fixed review content. All deployment/architecture decisions remain unaccepted."""
from . import g2_catalogue as old
SYSTEMCTL='https://www.freedesktop.org/software/systemd/man/255/systemctl.html'
BUS='https://raw.githubusercontent.com/systemd/systemd/v255/src/shared/bus-util.c'
UTIL='https://raw.githubusercontent.com/systemd/systemd/v255/src/systemctl/systemctl-util.c'
CG='https://www.kernel.org/doc/html/v6.6/admin-guide/cgroup-v2.html'
DOCS={
'G2_DIAGNOSTIC_STOP_RULES.md':'''# 單次唯讀診斷停止規則

目前 BLOCKED_TOOL_IDENTITY 與 BLOCKED_AUTHORIZATION，沒有執行。工具 hash、resolved ELF、root ownership/mode、Python3.12、systemd255 source family、nonroot UID/GID、exact source/scope/output 均須另審綁定。hash-only bootstrap 只能建立觀察，不能自證主機或 interpreter 信任根，不能批准 manager query。

新 scope 是三條固定 systemctl argv：system manager、user manager、固定當前 UID 的 user@UID.service。原二條 argv 的 manager properties 語義可保留；新版本另加 --no-ask-password 並明確新增第三條，沒有靜默替代。GNU timeout 只盤點 identity，不啟動，避免多一層 timeout child。任意輸入、remote bus、shell、pager、password agent、network、root fallback、安裝、cgroup 或 service mutation 都不允許。

每 child stdout+stderr 合計8192 bytes；三次最大24576、aggregate ceiling仍32768。超額只保留 bounded prefix並標記OUTPUT_BOUND，不把截斷當完整查詢。pidfd確認直接child exit，PID/start與session group保持到signal之前；5s soft query加1s cleanup，讀/Hash有byte限制、整組30s soft gate。這不是OS hard envelope，scheduler延遲或不可中斷I/O沒有有限hard保證。

固定讀取最多8層，每層9介面、每檔256 bytes；單snapshot32768 bytes、before/after兩份。proc status/mountinfo等是有界輸入，只保留必要投影。過長procs/lineage或snapshot拒絕，不截斷，不遞迴掃全機。兩份snapshot pin各cgroup directory FD；boot、mount/cgroup/pid namespace inode、process start、UID/GID、cgroup dev/inode before-after必須一致。多檔仍非原子交易。

只在單執行緒、預設SIGCHLD、Linux pidfd可用時啟動。owned session group在直接child未reap前以原start identity核對，SIGKILL清理；wait及group-absent不能確認即UNKNOWN，停止後續query，無PID fallback、無自動重試。這不保證能回收惡意逃離session的程序；只准所審systemctl、no-pager及封閉環境，未知binary/版本不能執行。

user private socket必須事先存在且屬當前UID；缺少即skip並記UNKNOWN，不start/enable/linger。v255內部可能從private fallback至default user bus；環境將DBUS_SESSION_BUS_ADDRESS固定為unix:path=/proc/self/fd/-1，使失敗只能到無效FD路徑，不能回到session bus；移除 inherited SYSTEMCTL_FORCE_BUS/LD*/PYTHON*，未證 installed binary前不稱實機驗證。system bus固定既存本機socket，不使用環境remote address。

在受保護parent下exclusive建立0700單次目錄，先寫0600 attempt.json占用scope，再寫0600 receipt.json與receipt.sha256，fsync普通檔及目錄；任何同名殘留或失敗都不得重跑。父目錄不可由group/other寫入。若空間不足、receipt超131072 bytes或寫入失敗，可能只有attempt或shell錯誤；保留現場，不承諾power-loss durability、不自動清理或換目錄繞過單次規則。

systemctl連線與查詢會消耗非零CPU/RAM，可能觸發manager/journal記錄；本方案沒有日誌硬容量或host/VMM成本封裝，也不把這些成本算成0。因此是另行接受風險的diagnostic scope，不能充當S4或正式job驗收。
''',
'G2_MANAGER_ARGV_REVIEW_ZH_TW.md':'''# Manager query source 審查

所審systemd255的show不指定unit會查manager，Version/SystemState可作固定選擇；不是列全部unit、journal或配置檔。額外的user@UID.service只查effective resource/delegation相關properties，不create/start unit；查unit可能引發manager載入unit metadata，須列入incidental control-plane side effects。

新第三條不證明未來job配置：CPUAccounting/MemoryAccounting是該既存service的effective property；Delegate=yes不等於任意未來child或collector UID已獲寫權。ControlGroup/InvocationID/MainPID需要與當時service狀態解讀。沒有合格未來group、受保護UID、fixed device或observer，仍UNKNOWN。

v255 verb_show使用BUS_MANAGER；user private連線失敗可fallback default_user。因此僅檢查session-bus socket不夠。此新版本改檢既存systemd/private且封閉default-user fallback address；沒有bus-autostart helper。這是source-family推論，不是對未讀binary的證明；版本或hash不同先另審，不自行採納新版。

官方來源：[systemctl255](https://www.freedesktop.org/software/systemd/man/255/systemctl.html)、[bus-util255](https://raw.githubusercontent.com/systemd/systemd/v255/src/shared/bus-util.c)、[systemctl-util255](https://raw.githubusercontent.com/systemd/systemd/v255/src/systemctl/systemctl-util.c)。
''',
'G2_DELEGATION_OBSERVABLES_ZH_TW.md':'''# 最小effective觀察與推論界線

新單次receipt擬保存目前boot、UID/GID、PID/start、namespace inodes、統一cgroup membership及祖先dev/inode/ownership；固定9介面是controllers、subtree_control、procs、type、events、cpu.max、memory.max、memory.swap.max、pids.max。controllers存在只證可用；subtree_control是當時enabled，不是delegation授權。direct procs不含child，root預期缺介面與nonroot讀失敗分列。

兩條manager query確認當時system/user可達性；第三條讀當前UID的既存user service的accounting、Delegate、InvocationID、ControlGroup、MainPID、User、limits及active state。user bus缺失保留UNKNOWN，不能憑配置檔或PID1推升成功。read-only結果仍不證明future group creation、controller enable、service/scope placement、不同collector UID權限或cleanup。

真正下一步需manager提供受控且可驗證的child/sibling placement、單writer delegation、nonroot writer/collector分離與protected failure slots；各自另審部署。所審cgroup API：[Linux6.6](https://www.kernel.org/doc/html/v6.6/admin-guide/cgroup-v2.html)。
''',
'G2_ASYNC_KERNEL_COST_AMENDMENT_PROPOSAL_V1.md':'''# Async kernel 成本邊界補充草案 V1（未接受）

原三份B文件保持原bytes/hash。此獨立草案不是修改或接受既有條款，也沒有生效。B1現有三個external角色不能準確保證涵蓋所有guest非同步filesystem/journal/writeback CPU；不能把這些工作默默歸給manager_journal或host_backing。

擬議決策：先要求逐類建立submission、實際execution、parent CPU counter及residual成本證據；不能歸帳的部分明列UNKNOWN。只有另行逐條接受新的ownership定義與誤差/尾量規則後，才可擬議放寬邊界；本草案沒有選擇任何新external排除。固定filesystem容量、journal blocks、allocated blocks與inodes只能說明disk，不證CPU charged to job。

若仍要求原A所有host/guest/VMM與async成本同一累計硬上限，現平台維持A_NOT_DEMONSTRABLY_FEASIBLE。不得把B2的observed-overrun拒絕說成原子零超額停止。未來若獨立測量不足，保留BLOCKED_OS_CAPABILITY，不以source模型補洞。

本草案 user_accepted=false、execution_authorized=false；不增加seeds、CPU/RAM/wall/disk，不啟動任何stress/physics。
''',
'G3_PROTOCOL_TO_DEPLOYMENT_GAPS.md':'''# Pure protocol 與真實部署差距

PR43的PID/start/UID/source/config/slot、cgroup hierarchy、累計counter、stop-state及post-exit observer協定保留，沒有改寫。此次adapter只取得窄幅診斷，並非protected kernel acquirer。

以下全部BLOCKED_OS_CAPABILITY：collector與controller不同death-domain且同parent pool；manager/InvocationID與原始PID-start可信綁定；ancestor/child membership及raw kernel counter完整取得；不可任意fallback的trusted manager；collector退出後、外部權限隔離observer；final parent-empty/cleanup與protected slot commit；固定resident allocation及OOM survivability；async kernel CPU ownership。

讀到user@UID.service不證明以上部署。普通0600/0700 owner目錄不能防同UID惡意process，也不是獨立protected failure slot；原post-exit supplement未接受。沒有發現需修改原g2_protocol的可重現新缺陷，因此原碼不變。
''',
'SCIENTIFIC_CONTINUATION_FEASIBILITY_ZH_TW.md':'''# 科學延續可行性

approval-grade保留full finite-mt/mb LO loop-induced gg→HH、原model/coupling/PDF/alpha_s/scales契約、四個固定replica seeds、B100/C1000來源差異、corrected Route-A guard與STOP92證據。未修改card，未開ROOT/MG5，沒有新build、ME、integration或events；現行scientific runtime仍未驗證。

若OS封裝持續不可行，獨立exploratory sandbox可能有助先檢查numerical trend或工具行為，但必須另立明確較弱保證、全新path/source/input/provenance/budget/seed與授權，不沿用approved campaign身份，不覆寫B/C/D或把結果併入approval-grade統計。此處沒有選定或執行任何sandbox，不能以較弱工程結果取代真正物理驗證。
'''}

def clause_review():
 rows=[]
 unchanged='保留job descendants、歷史資料、device保護及每個live gate另審；不擴張原資源或物理授權。'
 consequences={
  'B1_BOUNDARY':('所有執行與外部control-plane成本的計帳範圍。','放棄所有host/guest/VMM成本同一硬pool；async歸屬尚不能完整表達。','外部負載與未歸帳尾量會影響重現性，不能算0。'),
  'B2_CPU':('可用CPU rate限制、parent累計counter與提前停止。','不再保證原子零超額；最後超額只能拒絕結果。','early-stop安全餘量與counter/cleanup尾量需實測，會降低可用計算量。'),
  'B3_WALL':('由admission到collector退出及外部最後readback的生命週期。','不保證普通scheduler零延遲或有限最壞停止時間。','不同負載會改變牆鐘尾量；RuntimeMaxSec alone不足。'),
  'B4_RAM':('parent memory.max與swap.max=0，檢查peak/events。','放棄literal零暫態超額保證，OOM/超峰仍須拒絕。','tmpfs resident與runtime競爭RAM；2.25GiB ceilings不能同時填入2GiB。'),
  'B5_DISK':('真正獨立固定容量whole device含metadata/journal/failure evidence。','此項不放寬root/history保護，不能改用sparse/root VHD。','ENOSPC/inode exhaustion及journal配置會影響可用payload與失敗收據。'),
  'B6_EVIDENCE':('collector分離死亡域、同budget、固定失敗slot。','outer loss只能保留committed checkpoint與UNKNOWN，非power-loss保證。','slot commit與observer成本必須計入，失敗時可重現性有界。'),
  'B7_CLEANUP':('collector離開後由外部observer核對parent及slot。','observer不能自證自身exit，需接受明列非零外部成本。','排程、observer/collector尾量會改變wall與CPU解讀。'),
  'B8_RELEASE':('條款、設備、kernel、S4、build、physics分開批准。','不放寬release gate，接受架構不授權任何下一步執行。','每階段exact source/input/receipt保留使重現與審查可追溯。')}
 for prior in old.clause_rows():
  key=prior['clause'];physical,gives_up,repro=consequences[key]
  rows.append({'clause':key,'physical_meaning':physical,'gives_up_vs_A':gives_up,'protections_unchanged':unchanged,
   'actual_safety_implications':prior['expected_safety_impact'],'performance_reproducibility':repro,
   'missing_runtime_evidence':prior['remaining_uncertainty']+'; async CPU ownership UNKNOWN',
   'recommendation':'B1暫不接受，先審新async草案；其餘逐條條件式審查，不集體默認接受。',
   'exact_acceptance_decision':prior['exact_human_decision_required'],'accepted':False})
 return rows
