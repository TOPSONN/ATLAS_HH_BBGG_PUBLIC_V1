# B1–B8 逐條人類決策

三份原文件不改；全部未接受。

## B1_BOUNDARY

physical_meaning：所有執行與外部control-plane成本的計帳範圍。

gives_up_vs_A：放棄所有host/guest/VMM成本同一硬pool；async歸屬尚不能完整表達。

protections_unchanged：保留job descendants、歷史資料、device保護及每個live gate另審；不擴張原資源或物理授權。

actual_safety_implications：放寬原A成本邊界；job descendants與寫入不排除。

performance_reproducibility：外部負載與未歸帳尾量會影響重現性，不能算0。

missing_runtime_evidence：EFFECTIVE_CONFIGURATION_AND_ACTUAL_JOB_ENFORCEMENT_UNVERIFIED; async CPU ownership UNKNOWN

recommendation：B1暫不接受，先審新async草案；其餘逐條條件式審查，不集體默認接受。

exact_acceptance_decision：是否接受manager_journal、launcher、host_backing三項外部歸屬及VM residual明列？

accepted：False

## B2_CPU

physical_meaning：可用CPU rate限制、parent累計counter與提前停止。

gives_up_vs_A：不再保證原子零超額；最後超額只能拒絕結果。

protections_unchanged：保留job descendants、歷史資料、device保護及每個live gate另審；不擴張原資源或物理授權。

actual_safety_implications：允許非即時停止語義，不能稱零overshoot。

performance_reproducibility：early-stop安全餘量與counter/cleanup尾量需實測，會降低可用計算量。

missing_runtime_evidence：EFFECTIVE_CONFIGURATION_AND_ACTUAL_JOB_ENFORCEMENT_UNVERIFIED; async CPU ownership UNKNOWN

recommendation：B1暫不接受，先審新async草案；其餘逐條條件式審查，不集體默認接受。

exact_acceptance_decision：是否接受observed-overrun拒絕而非原子總量零超額保證？

accepted：False

## B3_WALL

physical_meaning：由admission到collector退出及外部最後readback的生命週期。

gives_up_vs_A：不保證普通scheduler零延遲或有限最壞停止時間。

protections_unchanged：保留job descendants、歷史資料、device保護及每個live gate另審；不擴張原資源或物理授權。

actual_safety_implications：外部observer與receipt尾成本須明列。

performance_reproducibility：不同負載會改變牆鐘尾量；RuntimeMaxSec alone不足。

missing_runtime_evidence：EFFECTIVE_CONFIGURATION_AND_ACTUAL_JOB_ENFORCEMENT_UNVERIFIED; async CPU ownership UNKNOWN

recommendation：B1暫不接受，先審新async草案；其餘逐條條件式審查，不集體默認接受。

exact_acceptance_decision：是否接受普通scheduler及指定final-readback端點，不要求零延遲？

accepted：False

## B4_RAM

physical_meaning：parent memory.max與swap.max=0，檢查peak/events。

gives_up_vs_A：放棄literal零暫態超額保證，OOM/超峰仍須拒絕。

protections_unchanged：保留job descendants、歷史資料、device保護及每個live gate另審；不擴張原資源或物理授權。

actual_safety_implications：放寬literal零transient overshoot；OOM/peak overcap拒絕。

performance_reproducibility：tmpfs resident與runtime競爭RAM；2.25GiB ceilings不能同時填入2GiB。

missing_runtime_evidence：EFFECTIVE_CONFIGURATION_AND_ACTUAL_JOB_ENFORCEMENT_UNVERIFIED; async CPU ownership UNKNOWN

recommendation：B1暫不接受，先審新async草案；其餘逐條條件式審查，不集體默認接受。

exact_acceptance_decision：是否接受Linux記憶體語義，並要求先補resident allocation及實測？

accepted：False

## B5_DISK

physical_meaning：真正獨立固定容量whole device含metadata/journal/failure evidence。

gives_up_vs_A：此項不放寬root/history保護，不能改用sparse/root VHD。

protections_unchanged：保留job descendants、歷史資料、device保護及每個live gate另審；不擴張原資源或物理授權。

actual_safety_implications：root/history保護不放寬；不能用C-drive VHD/shared-root代替。

performance_reproducibility：ENOSPC/inode exhaustion及journal配置會影響可用payload與失敗收據。

missing_runtime_evidence：EFFECTIVE_CONFIGURATION_AND_ACTUAL_JOB_ENFORCEMENT_UNVERIFIED; async CPU ownership UNKNOWN

recommendation：B1暫不接受，先審新async草案；其餘逐條條件式審查，不集體默認接受。

exact_acceptance_decision：是否保留此不放寬的device安全門檻，另行提供合格device？

accepted：False

## B6_EVIDENCE

physical_meaning：collector分離死亡域、同budget、固定失敗slot。

gives_up_vs_A：outer loss只能保留committed checkpoint與UNKNOWN，非power-loss保證。

protections_unchanged：保留job descendants、歷史資料、device保護及每個live gate另審；不擴張原資源或物理授權。

actual_safety_implications：outer失效可留下UNKNOWN，不承諾power loss。

performance_reproducibility：slot commit與observer成本必須計入，失敗時可重現性有界。

missing_runtime_evidence：EFFECTIVE_CONFIGURATION_AND_ACTUAL_JOB_ENFORCEMENT_UNVERIFIED; async CPU ownership UNKNOWN

recommendation：B1暫不接受，先審新async草案；其餘逐條條件式審查，不集體默認接受。

exact_acceptance_decision：是否接受outer loss時僅保留committed checkpoints與UNKNOWN？

accepted：False

## B7_CLEANUP

physical_meaning：collector離開後由外部observer核對parent及slot。

gives_up_vs_A：observer不能自證自身exit，需接受明列非零外部成本。

protections_unchanged：保留job descendants、歷史資料、device保護及每個live gate另審；不擴張原資源或物理授權。

actual_safety_implications：observer自身termination不能自證；外部非零成本需接受。

performance_reproducibility：排程、observer/collector尾量會改變wall與CPU解讀。

missing_runtime_evidence：EFFECTIVE_CONFIGURATION_AND_ACTUAL_JOB_ENFORCEMENT_UNVERIFIED; async CPU ownership UNKNOWN

recommendation：B1暫不接受，先審新async草案；其餘逐條條件式審查，不集體默認接受。

exact_acceptance_decision：是否接受該exact post-exit observer supplement及成本歸屬？

accepted：False

## B8_RELEASE

physical_meaning：條款、設備、kernel、S4、build、physics分開批准。

gives_up_vs_A：不放寬release gate，接受架構不授權任何下一步執行。

protections_unchanged：保留job descendants、歷史資料、device保護及每個live gate另審；不擴張原資源或物理授權。

actual_safety_implications：不放寬release與歷史保護。

performance_reproducibility：每階段exact source/input/receipt保留使重現與審查可追溯。

missing_runtime_evidence：EFFECTIVE_CONFIGURATION_AND_ACTUAL_JOB_ENFORCEMENT_UNVERIFIED; async CPU ownership UNKNOWN

recommendation：B1暫不接受，先審新async草案；其餘逐條條件式審查，不集體默認接受。

exact_acceptance_decision：是否同意條款決策與每個後續execution approval嚴格分開？

accepted：False
