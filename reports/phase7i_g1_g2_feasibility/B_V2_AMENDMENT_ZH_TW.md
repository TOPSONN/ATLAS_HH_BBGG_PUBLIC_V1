# B-V2 逐條研究執行合約提案

機器版本：`B_V2_RESEARCH_EXECUTION_TERMS_PROPOSAL_V1`，延續 `BOUNDARY_AMENDMENT_CANDIDATE_V2`。狀態 PROPOSED_NOT_ACCEPTED；weaker_than_original=true；user_accepted=false；execution_authorized=false。確切文字與 hash 位於 source manifest 和 `config/b_v2_research_execution_terms.json`。

建議審核此研究路徑，因目前 A 的 host+guest 共同硬總額不可證明。這裡明確揭露較弱的保證，沒有替使用者接受任何條款，也不放寬 root／歷史磁碟安全條件。

| 條款 | 待人類明確接受或拒絕的內容 | 影響／目前決定 |
|---|---|---|
| B1 BOUNDARY | 工作 parent 包含 worker、compiler/Git/helpers、trusted controller、protected collector；僅既有 manager_journal、launcher、host_backing 三角色列外部可信基礎設施 | 外部成本真實且非零，不再屬原 A 全包含總額。NOT_ACCEPTED |
| B2 CPU | cpu.max 頻寬限制＋同 parent 累積 user+system 監測、提早整組停止、最終實測驗收 | 不是零超調的原子 lifetime quota；最後 CPU 超 nominal、重設／缺 counter 均拒絕或 UNKNOWN。controller/collector 至 capture/cleanup 均計入。NOT_ACCEPTED |
| B3 WALL | dispatch 前預置獨立 deadline；以 activation admission 至全部 cleanup 完成計 wall；提早停止保留餘裕 | 普通排程無硬即時零延遲；需凍結 clock、suspend/VM pause、capture/kill 策略。超額拒絕，缺 endpoint UNKNOWN；RuntimeMaxSec 不能單獨涵蓋全生命週期。NOT_ACCEPTED |
| B4 RAM | 接受 memory.max、memory.swap.max=0 的標準 hierarchical kernel 語意，保存 peak/events/OOM | 包括文件載明的可能暫時超額；不能聲稱 literal zero-transient 保證。外層 OOM 可殺 collector。NOT_ACCEPTED |
| B5 DISK | 保留 P1-safe 獨立可拋棄 whole-device，work/private/persistent 共用 nominal disk ceiling，allocated blocks/inodes＋metadata/journal/failure reserve | 不接受 C-drive VHD、shared-root partition、loop 或 logical slots 代替。identity/provisioning 另審。NOT_ACCEPTED |
| B6 EVIDENCE | collector 與 worker/controller 不同死亡域但仍計入 aggregate；保留原32KiB slots、保護 UID/FD、先配置後工作、卸載前 raw capture | 外層／host／collector 死亡僅保留以前 commit checkpoint，之後 UNKNOWN；不保證未測 power loss。NOT_ACCEPTED |
| B7 CLEANUP | parent membership 與獨立 manager fallback；需驗空 cgroup、無 owned descendants、同一 instance | unit 不見不能推論 cleanup 成功；缺資料拒絕／UNKNOWN。NOT_ACCEPTED |
| B8 RELEASE | 所有條款人類接受後，provisioning、exact-source review、正反 kernel tests、S4／正式 build 仍各自取得授權 | source/CI 不授權任何 runtime，不得將 B 改名原 A FULL。NOT_ACCEPTED |

Nominal 數字維持 S4 CPU4s／wall13s／RAM512MiB／swap0／disk16MiB；未來 BUILD CPU及wall各14400s／RAM2GiB／swap0／disk5GiB；1 job／1 scientific worker。這些是提案的成功驗收上限，不構成「排程絕不超額」的隱含保證。

任何實測 overshoot 均照契約拒絕，不可用調高 limit 或事後改旗標通過。原 A validators 與 historical PASS/FAIL 保留。B 若日後通過需使用獨立結果名稱、accepted clause hashes、exact source/config、實際證據，FULL_LAUNCH_ENVELOPE_VERIFIED 仍 false。

B1 的 VM／hypervisor CPU/RAM runtime overhead 尚未明確歸屬；目前標記 UNASSIGNED／BLOCKED，不自動將它納入 host_backing management，也不新增第四個 external role。取得真實 host 能力後，需明確定義此成本如何落於既有三角色或工作 parent；若要修改角色集合，必須另提精確修約。未完成此項之前，B1 尚不能視為可完整接受或部署。

接受 B1 **不會**自動接受 B2/B3/B4。請逐條記錄 ACCEPT／REJECT／需修改，並綁定上述精確 JSON SHA256；上述未分配成本的定義修正須新 hash 及獨立審查。不接受時可以維持原 A，改選具備完整控制邊界的其他平台。此文件本身不要求現在批准或執行。
