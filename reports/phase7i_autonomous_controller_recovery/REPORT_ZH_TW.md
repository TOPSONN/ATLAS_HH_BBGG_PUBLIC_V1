# Phase7I 自主工程修補完整報告

本輪完成可安全執行的來源修補、實際離線回歸、獨立審查與完整 Git preflight。結論為 **LEVEL A：來源工程驗證通過；LEVEL B／C 尚未驗證**。沒有新的 live kernel／service、壓力、mount／quota、build、zero-ME、ME、積分或事件執行。

## 精確來源與交付

| 欄位 | 值 |
|---|---|
| PROJECT | ATLAS_HH_BBGG_PUBLIC_V1 |
| TASK | PHASE7I_AUTONOMOUS_CONTROLLER_RECOVERY |
| BASE_PR | #34，承接已核對的 #33；#33→#34→本 Draft PR |
| BASE_REVISION | 5431e0b2efba20863cddaccc37679af32e13a7f4 |
| EXECUTED_SOURCE_REVISION | 114b5c00341be22982244d3d9548e80adf2d00e5；只指離線測試／唯讀 Git 檢查的精確 bytes |
| DELIVERY_REVISION | 最後 report-only commit，見 Git HEAD、PR metadata、本機 DELIVERY.json |
| COMMIT_HASH | 可執行來源 candidate：114b5c00341be22982244d3d9548e80adf2d00e5 |
| PULL_REQUEST_URL | 新 Draft PR 建立後記於 PR metadata 及本機 DELIVERY.json |

任務起點 #33 b8ae4cc03c0ac408577909847e56f417fc28eba8 與後續 #34 head已重新核對為OPEN／DRAFT。本輪採用經驗證的#34；沒有從main重開、改舊PR、merge、rebase或force-push。後續報告commit只新增有界證據，不改frozen candidate。精確21檔見source_manifest.json。

## Root-cause matrix

| 項目 | 類別／證據 | 本輪實作與限制 |
|---|---|---|
| 舊Pre：UNACCOUNTED_WRITABLE_MOUNT | 真實失敗 | 舊完整rw inventory缺失，不能宣稱false positive；新capture先於拒絕 |
| 舊StopPost：226/NAMESPACE、/dev/mqueue EPERM | 真實失敗 | 改單一ExecStart內部八階段；舊失敗保留，沒有實測重跑 |
| Network／IPC訊息、Main／child未進入 | 歷史觀察 | 三個Private*=yes保留；source逐一驗owner/type/map/namespace/child |
| sibling-userns與cached net／IPC FD的owner衝突 | systemd／Linux來源推論 | 缺舊syscall/owner trace及exact Ubuntu patched-source，仍為假說 |
| all-rw判斷不足分類、拒絕前診斷遺失 | 來源可確認缺口 | machine-readable policy＋獨立verifier＋bounded RAM capture |
| child PID／namespace／guard可被拼接 | 獨立負例確認 | Popen PID、parent、aggregate、重建current namespace、guard origin/count嚴格綁定 |
| cleanup覆蓋timeout／output failure | 實際mock負例確認 | 保留原reason，cleanup附UNKNOWN；terminal保留額度只輸出一次 |
| RAM保存完整不代表原始capture完整 | 實際red→green | 分開兩個completeness，巢狀／serialized partial也傳播不完整 |
| 全組CPU kill、完整wall／cleanup、持久容量 | 未閉合contract | 不以rate/timer/FSIZE/flags替代kernel證明 |

已比較#24 Route-A、#32 backend/worker/allocation/archive、#33 full-controller及#31 Phase13F。#31只作參考：host provisioning/monitoring/write的較窄邊界、missing CPU/peak→0、wait_empty(None)與13.5秒容差，均不能移植為Phase7I PASS。exact source pointers／比較收據保留本機SHA鏈。

## 控制器架構與實作

CONTROLLER_ARCHITECTURE_SELECTED = B_SINGLE_EXECSTART_SAME_AGGREGATE_CONTROLLER_AND_BOUNDED_CHILD

Candidate A仍需證明每次Exec namespace、Pre失敗後StopPost、descriptor handoff及全流程計帳；舊226未解。Candidate B把preparation、完整Git、dependency hashing、worker/monitoring、inert preparation、receipt、postflight、failure cleanup放在同一Main/aggregate，避免跨Exec sibling-userns重用。理由是減少不同namespace／計帳邊界；安全等價的runtime證據仍待真實測試。

CONTROLLER_IMPLEMENTATION_STATUS = SOURCE_AND_OFFLINE_VALIDATED_RUNTIME_UNVERIFIED

- mount policy分6類，解析全部mountinfo欄位、octal escaping、nested/bind/parent graph/propagation。未知persistent rw、source覆蓋、多義mount拒絕；無/proc或/dev無條件rw白名單。
- namespace owner/type的7個只讀nsfs ioctl在新filter前完成；其後所有ioctl拒絕。child憑相同namespace ID與parent context繼承immutable owner/type，明記繼承而不捏造child ioctl。
- S4 guard保留歷史拒絕，另限制namespace/network/clone3。固定6類invalid-target呼叫，Main/child/post最多18次；本輪未安裝或呼叫。EPERM只表示filter stack拒絕，不能唯一歸因於本BPF，也不是任意真實device/proc寫入測試。
- child stdout/stderr在執行中分塊讀，各≤65536/8192 bytes，每次≤4096，child≤1秒。重複JSON key、nonfinite、偽造FULL、超量及incomplete LF皆拒絕。
- 每輪public stdout65536、raw private RAM131072、record32768、terminal reserve2048 bytes。大proof只輸出hash reference；原始capture保留有界volatile RAM，無持久性承諾。
- handoff以固定capped tmpfs regular file、same-FD fstat、O_NOFOLLOW、owner/nlink/size/schema/parent核對。沒有把source或工作repository改成可寫。
- 完整兩次check_revision(full=True)保留，沒有換成scoped fixture。
- typed live launch、full-campaign、BUILD_ONLY gate持續拒絕。describe-volatile-workflow僅產生待審argv，不dispatch、不建立授權。

## Storage routes與邊界

PERSISTENT_STORAGE_STRATEGY = S3_FIXED_SLOT_LOGICAL_TRANSPORT_PLUS_S4_VOLATILE_DIAGNOSTIC

PERSISTENT_HARD_CAPACITY_STATUS = BLOCKED

| Route | 實作／可行性 | 容量機制與最小條件 |
|---|---|---|
| S1 quota-backed | active quota UNKNOWN，未執行quota syscall | 需不可繞過block+inode hard limit既有domain／固定volume；若需activation/root，管理員另處理 |
| S2 bounded FUSE | helper/lib/device存在，無reviewed bounded driver | 需exact driver、固定outer allocated capacity、inode/metadata/crash/daemon邊界；沒有install/mount或大型FS實作 |
| S3 fixed transport | 實作並接到tmpfs；獨立decoder＋23離線測試 | 固定slots、canonical manifest、length/hash/commit trailer+EOF；不能限制caller sink的blocks/inodes/metadata |
| S4 volatile-only | 正常八階段單次方案備妥，未執行 | 另核准後可縮小namespace/cgroup問題；不能升為persistent/full/build PASS |

通用codec payload73728、manifest4096、wire131072 bytes。controller實際3slots為controller24576、namespace16384、mount16384；protocol overhead全數納入的保守logical wire上界 **61531 bytes**，小於65536 file cap。獨立算術與decoder核對完成；不能推導allocated extents、inode或持久性。

| Storage boundary | 計帳／現況 |
|---|---|
| volatile work／private tmpfs | 提案8MiB＋1MiB、RAM512MiB/swap0；尚無實際mount/statvfs |
| build scratch／compiler output | 本輪0build；未來5GiB完整envelope未建立 |
| archive／persistent binary | 無native binary slot、無持久archive capacity claim |
| exported receipts／controller loss | RAM/tmpfs可隨loss消失，沒有安全持久出口保證 |
| Git/source | frozen read-only identity；工程authoring/test clone不冒充service內計帳 |
| manager／journal／terminal evidence | control-plane persistent bytes/inodes須明定上限／歸屬，目前未證明，不能默默排除 |
| metadata／journal／allocated extents | S3 logical bound不涵蓋，BLOCKED |

fallocate/ioctl/xattr/dup/rename/hardlink/sparse-growth不在codec API，只縮小logical操作集合；guard拒絕不是disk quota。Crash trailer可辨認不完整transport，不能恢復遺失volatile bytes。

## CPU／RAM／wall／cleanup

| 欄位 | 本輪結果 |
|---|---|
| REAL_MAIN_EXECUTED | false |
| REAL_EIGHT_PHASE_WORKFLOW_COMPLETED | false |
| ACTUAL_KERNEL_TESTS | 0，本輪新增invocation計數 |
| RESOURCE_MATRIX_STATUS | 原47案，0案執行，語意未刪改 |
| AGGREGATE_CPU_SECONDS | null |
| AGGREGATE_WALL_SECONDS | null |
| PEAK_RAM_BYTES | null |
| SWAP_BYTES | null |
| ALLOCATED_DISK_BYTES | null |
| KERNEL_CGROUP_IDENTITY | null |
| ORPHAN_CLEANUP_STATUS | UNKNOWN，無新manager postmortem |

CPUQuota30%／cpu.max=3000 10000是bandwidth rate；LimitCPU=2是per-process。兩者都不是全組累計4秒kill。source欄位quota_duration_CPU_upper_seconds只是**假設timer準時的conditional nominal arithmetic**，不是無條件upper bound。新獨立verifier分開cumulative delta、partial lower bound、rate、missing endpoints；觀測cumulative>4秒即FAIL，但事後verifier不會在達4秒瞬間終止整組。

RuntimeMax8秒＋start1秒＋stop0.5秒＋估計kill0.5秒也不是activation→cleanup硬即時13秒保證。缺manager cleanup時whole-wall UNKNOWN；Main仍活不得自稱cgroup已空。controller kill/OOM/timeout/orphan/setsid須真實negative campaign另核准，不能從正常一案推廣。

memory.max/current/peak/swap/events與aggregate有strict schema/readback source；本輪kernel數值均null，missing peak不補0。21個數值tests包括CPU4s+1usec、wall13s+1ns、RAM+1byte、counter reset/缺值/錯cgroup/缺cleanup；純JSON一致性不能認證raw origin／授權。

## 完整Git preflight實測

fresh normal .git、clean detached 114b5c00341be22982244d3d9548e80adf2d00e5、official origin，實跑完整tracked-worktree檢查兩次：

| 次數 | tracked／critical | host wall秒 | host CPU秒（parent+Git children） |
|---|---|---:|---:|
| 1 |1495／322|0.492243776|0.239773353|
| 2 |1495／322|0.470140185|0.213819068|

合計wall 0.962383961秒、CPU 0.453592421秒。只表示Git本身這次host成本小於名目4/13預算；不含啟動/import、額外dependency hashing、activation、receipt/cleanup，不保證限速cgroup全流程通過。CI mock不是這項測量。實際-I -B describe已執行，checkout維持clean；只證明describe imports，未驗filter下Git/compiler/native loader相容性。

## 測試、獨立review與歷史保存

| 欄位 | 結果 |
|---|---|
| OFFLINE_TEST_RESULTS | 449 unique，0fail/error/skip，source前後一致 |
| SAFE_LEGACY_RESULTS | 選定81，0fail/error/skip，implementation snapshot一致 |
| INDEPENDENT_SOURCE_REVIEW | PASS_SOURCE_OFFLINE_ONLY；mount/guard、child identity、I/O、storage、CI/publication、CPU/wall/argv |
| INDEPENDENT_NUMERICAL_REVIEW | 純verifier21及獨立算術；沒有kernel metrics |
| HISTORICAL_SHA256_PRESERVATION | 50169內容觀測、3588706711 bytes（含重複）、122symlink；0變更/error/race |
| REAL_HH_BUILDS | 0 |
| REAL_ME_CALLS | 0 |
| REAL_INTEGRALS | 0 |
| NEW_EVENTS | 0 |

舊292 IDs完整包含於449；原45 controller方法、九個舊source/profile bytes不變。獨立129 targeted是449子集，不相加。runner允許真實Git fixture，拒絕native/physics/非Git dispatch；safe legacy另含5個固定harmless Python與1個固定sleep fixture，無HumanReview建構。audit只涵蓋reviewed固定測試；directory-FD targets、stat/readlink/symlink aliases不是一般sandbox完整保證。

真實red→green包含literal-newline SyntaxError、錯schema key、cleanup覆蓋、child identity缺口、capture completeness，以及依來源證明錯誤的UID-map error文字預期。失敗原件留本機並以SHA鏈引用；沒有刪失敗、調高限制或更改acceptance。evidence.json保留bounded原始收據identities。

保存範圍是既有protected campaign／舊closure outputs/receipts/source清單，不是全主機。B100/C1000、StageA/STOP92、PDF/alpha_s/RNG/native estimator/weights/ME rows與舊安裝未變。

附件guard pin誤植63hex：404dfd1fb81a3fa9ad7cf18d511caf063674a325c2622785e7fca1d5f4ba123。實際未變64hex：404dfd1fb81a3fa9ad7cf18d511caf063674a325c2622785e7fca1d5f4fba123。physics contract仍a8a093e2ec47283dd9cb503b2c83fe95b89df4761df5fb7afc623fa291c937cb。沒有默認換綁或產生授權；下一次人類核准須明用實際64hex。

## Gate與最小外部動作

FULL_CONTROLLER_RESOURCE_ENFORCEMENT_IMPLEMENTED=false

FULL_LAUNCH_ENVELOPE_VERIFIED=false

FORMAL_BUILD_ONLY_AUTHORIZED=false

| 分類 | 結論 |
|---|---|
| GATES_PASS | LEVEL A source/offline、review、負例、safe regressions、identity、scoped保存 |
| GATES_FAIL | 最終固定suite無失敗；歷史kernel失敗保留，沒有本輪重測 |
| GATES_BLOCKED | 新kernel授權、persistent hard backend、whole-job cumulativeCPU/wall強制閉合、正式build/physics |
| GATES_UNKNOWN | 實際Main/child/cgroup/namespace/tmpfs/peak/swap/disk、manager cleanup、active quota、compiler相容性 |
| FINAL_VERDICT | LEVEL_A_SOURCE_ENGINEERING_VALIDATED_LEVEL_B_C_NOT_VERIFIED |

剩餘gate逐項解除：

1. **S4 limited kernel**：來源與104-token argv固定在proposed_kernel_scope.json。附件第7B節要求新exact-source人類核准，不能重用one-shot。單一正常workflow＋child，沒有47案/stress/build。須審查fresh unit/tmpfs、輸出/control-plane scope；首次失敗停止並保留原件，不替代重跑。成功也只有S4限定結果。
2. **Persistent capacity**：S1/S2無verified backend。最小外部前提是單一預先建立並獨立驗證、不可成長的block+inode hard-capacity domain，明定metadata/journal/control-plane/failure-reserve；可能需管理員配置，本輪無sudo/remount/activation/install。之後針對具體backend整合、凍結source、核准容量與繞過負例。
3. **全生命週期／cleanup**：已拆開Main/managerpostmortem，verifier不虛構endpoints。仍須activation→cleanup counters與controller/worker/OOM/timeout/setsid負例，另核對cumulativeCPU限制機制；rate×timer不是解除條件。不能改true旗標解決。
4. **LEVEL C／下一物理關卡**：B全部成立並完成future4h/2GiB/5GiB相容性review後，才準備正式BUILD_ONLY exact-source/input/toolchain/dependencies/fresh-output/binary proposal。四build、八zero-ME、四entry-denial另核准；再經BINARY_REVIEW與PHYSICAL_RESTART才能積分。

MINIMUM_EXTERNAL_ACTION_IF_BLOCKED：審查exactS4 package及限制後另行明確核准限縮診斷；FULL/formal另須上述單一真實persistent backend及全組強制／cleanup證據。

NEXT_RECOMMENDED_STEP：完成exactS4 package與capacity prerequisite審查；本輪不dispatch、不提出正式BUILD_ONLY或物理授權。

GitHub只發布source/tests/CI與bounded報告，每次push前審查index及每個outgoing intermediate payload；無PDF/PNG、binary、raw events、private captures/config。CI只代表固定offline/safe legacy/publication，不能冒稱WSL kernel驗收。最終delivery CI實際readback列PR與本機報告，與舊head結果區分。

## 公開原始規格

CPU rate／period與cgroup cumulative counter、hierarchical membership及populated語意參照[Linux6.6 cgroup v2](https://www.kernel.org/doc/html/v6.6/admin-guide/cgroup-v2.html)與[CFS Bandwidth Control](https://www.kernel.org/doc/html/v6.6/scheduler/sched-bwc.html)。systemd屬性參照[systemd255 resource control](https://www.freedesktop.org/software/systemd/man/255/systemd.resource-control.html)及[exec isolation](https://www.freedesktop.org/software/systemd/man/255/systemd.exec.html)。這些文件支持來源設計／語意解讀，不能代替目前WSL effective readback，也沒有證明舊失敗的唯一根因。
