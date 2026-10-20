# Phase7I Kernel Namespace／Storage Recovery 驗收報告

**FINAL_VERDICT：SOURCE_RECOVERY_VALIDATED_RUNTIME_AND_STORAGE_BLOCKED**

本輪完成來源修補、離線正反測試、獨立審查與 exact-source 診斷提案。**依附件第5節，沒有執行任何新的 kernel/service/stress attempt。** 原始 PR33 失敗完整保留；runtime 與 persistent capacity 仍未通過，不宣稱解除 Phase7I 全部阻擋。

| 欄位 | 結果 |
|---|---|
| PROJECT | ATLAS_HH_BBGG_PUBLIC_V1 |
| TASK | PHASE7I_KERNEL_NAMESPACE_AND_STORAGE_RECOVERY_V1 |
| BASE_REVISION | PR33：b8ae4cc03c0ac408577909847e56f417fc28eba8；已即時核對 remote |
| EXECUTED_SOURCE_REVISION | 本輪無新 kernel 執行；歷史失敗來源仍為3c89de1e67def831e5aa69ce56bab427bfc28cbf |
| NEW_SOURCE_REVISION | 凍結的 executable candidate：133f14e6f3f05189c706e183eb5dc86bde339376 |
| MOUNT_ROOT_CAUSE_STATUS | parser／拒絕前診斷缺陷已修；歷史實際 rw mount 清單缺失，false-positive 根因仍 UNKNOWN |
| NAMESPACE_ROOT_CAUSE_STATUS | sibling-userns／cached net+IPC ownership 為有主要來源支持的假說；歷史 syscall／owner 未證實 |
| PERSISTENT_STORAGE_BACKEND | NONE_VERIFIED／BLOCKED |
| KERNEL_TESTS_ACTUALLY_EXECUTED | 0；service0、namespace ioctl0、stress0、retry0 |
| MAIN_ENTERED | 本輪未執行；沒有新 Main runtime 證據 |
| EIGHT_PHASE_WORKFLOW_COMPLETED | runtime NO；mock 流程成功不能替代真實執行 |
| CPU_RAM_WALL_DISK_ENFORCEMENT | 新 runtime UNKNOWN；固定 caps 未提高；persistent hard capacity BLOCKED |
| OFFLINE_TEST_RESULTS | final292/292＋81/81 safe legacy，0 failure/error/skip |
| INDEPENDENT_REVIEW | namespace primary source、mount/publication、最終14檔案、frozen checkout／104-token argv 均完成獨立審查 |
| HISTORICAL_PRESERVATION | before/after各50,169內容觀測、3,588,706,711bytes、122symlink targets；0變更／錯誤／race |
| REAL_ME_CALLS | 0 |
| REAL_INTEGRALS | 0 |
| NEW_EVENTS | 0 |
| COMMIT_HASH | executable candidate133f14e6f3f05189c706e183eb5dc86bde339376；source/evidence delivery head另見PR與本機FINAL_REPORT |
| PULL_REQUEST_URL | publication後填入新的stacked Draft PR；base PR33保持 |

## 來源工程

`mount_attestation.py` 正確解析 mount ID、parent ID、device、root、mountpoint、filesystem、mount flags、superblock flags與optional fields，處理kernel四種octal escapes。per-mount ro與backing superblock rw分開判斷，readonly bind不會因superblock rw而被當成rw。重複ID／模糊mountpoint／malformed／超限資料均拒絕。

controller 在parser或mount guard拒絕前，先輸出有界的私有原始capture、SHA256與完整性標記，再輸出可審查安全投影。capture最多16KiB／256rows、projection最多16KiB；超限保留bounded prefix並標記INCOMPLETE，不能宣稱取得完整表。raw evidence只留本機，新的publication gate拒絕JSON、JSONL、Markdown、uppercase JSON與serialized/escaped wrappers中的private mount／stderr frames。

分類區分kernel pseudo-filesystems、private tmpfs、source、persistent與unknown。**分類不是可寫白名單**：沒有新增rw pseudo exception；除既定兩個private tmpfs，所有rw仍拒絕。private tmpfs還需精確type/source/root、security flags、statvfs byte/inode cap。沒有刪除guard，也沒有無條件放行/dev、/proc、/sys後代。舊raw清單未留存，因此本輪沒有捏造是哪個pseudo mount導致原失敗。

`namespace_attestation.py` 提供未來才可執行的readonly nsfs讀回：5個namespace type、2個net/IPC owner查詢，核對owner為本服務private userns、非initial/full UID/GID maps、cap0、NNP1、seccomp2、lo-only。缺測／拒絕／錯誤type／owner／FD清理錯誤均UNKNOWN或FAIL；manager顯示yes不等於生效。全部測試mock，沒有本輪實際ioctl。

child protocol有kind／byte／record／depth限制；診斷用typed wrapper，偽造Main完成與任何nested FULL claim拒絕。成功terminal也經相同檢查；nonzero child和cleanup錯誤不會蓋掉原錯誤。

controller SHA256：`fb7ace1034f396f32107fffc2dabea91e24013d538efa7debf68ea3eb53e8656`。14檔案獨立manifest identity：`52fdbddb97108aa1c89a0f7f022bf736b485974d20d9e0ff48bd3f62ab0d0dcb`。

## Namespace 根因與等價架構

歷史可確認：Pre exit2；StopPost出現network/IPC EPERM、/dev/mqueue EPERM，最後226/NAMESPACE；Main未進入。上游systemd v255/v255.4各Exec建立不同userns，但同service可快取net/IPC namespace FD；Linux target-owner capability要求支持sibling-userns setns不符的假說。紀錄缺少實際syscall和owner，不能寫成已證明的唯一根因。安裝版本255.4-1ubuntu8.17已核對binary SHA，exact Ubuntu patched source未取得，差異保留UNKNOWN。

新方案只用**單一ExecStart**，將pre/post/failure-finalization留在Main，child繼承其namespace；不再由另一個Exec命令重入manager快取。PrivateUsers／PrivateNetwork／PrivateIPC=yes以及所有既有cap／NNP／readonly／namespace限制都保留。ExecStartPre／ExecStopPost標記NOT_USED_BY_PROPOSED_ARCHITECTURE，不能說舊StopPost已實測修復。

此設計避免跨Exec的sibling-userns依賴，沒有停用隔離。一般例外可走有界finally；SIGKILL/OOM後Python不能完成收據，需保留INCOMPLETE，由manager/kernel清理另行判讀。這不等於已通過abrupt termination、orphan或controller-loss實測。

## 三類persistent storage候選

| 候選 | 目前無特權可用性 | 管理／額外軟體 | 真正容量界線與缺件 |
|---|---|---|---|
| A dedicated filesystem/project quota | 尚未核實active hard block/inode限額 | 已配置的volume可能可直接使用；啟用／分配通常需另行管理授權；工具目前缺席 | 須獨立核對live block/inode hard caps、charged metadata及shared journal/VHDX範圍；mount flags缺席不是quota不存在證明 |
| B fixed-capacity backing filesystem | FUSE device/libraries存在，但沒有已審查可用driver/backend | driver或volume provisioning可能需另審安裝／管理 | 須核對完整backing容量、outer extents/metadata/journal、稀疏／fallocate bypass與crash/partial-write；fuse2fs來源不支持journal writing，不能假定crash-safe |
| C fixed descriptors/files | 可作有界transport | 單純固定FD可不需管理／安裝 | FSIZE／logical EOF／事後st_blocks/filter不能單獨證明persistent allocated blocks、inodes與共享metadata；不能作完整backend |

逐候選詳細matrix明列tmpfs、extent/journal、ioctl/xattr、controller-loss、disk-exhaustion收據與正式build適用性，見evidence.json的storage_candidates。沒有sudo、remount、enable quota、安裝或主機設定變更。最小缺件是經獨立驗證的已配置hard block+inode容量區，或已審查且連outer allocation都界定的固定容量volume；本輪未自行取得這些權限。

## 實際來源核對成本與固定預算

乾淨regular.git／detached execution checkout：`/home/btu/projects/atlas_hh_phase7i_ns_inspection_133f14e`，official origin、133f14e、14檔案與manifest完全相同。

兩次真正的readonly `check_revision(full=True)`均PASS1474tracked／307critical：wall0.480885s與0.445631s，CPU0.227748s與0.192357s；host總wall0.954800s、guard CPU0.420105s。CPU除30%為1.400352s，只是計算指標，**不是受限service內的實測成本或完整budget保證**。沒有用mock代替這兩次完整source核對，也沒有把它們稱作native zero-ME。

Fixture caps保持CPU4s/wall13s/RAM512MiB/swap0/work8MiB/private1MiB/disk16MiB。單Main timer設計合計10s，30%quota加period carry計算3.003 CPU s；仍非realtime/kernel驗收。未來formal caps維持14400s/2GiB/swap0/1job-worker/5GiB/retainedLHE0，未執行。

## 測試、保存與輸入pin差異

final292項涵蓋原207 IDs、新mount26、namespace25、controller recovery19、publication15；另81 safe legacy。原45controller IDs完全保留，僅fixture與4個架構介面斷言調整，41個原test bodies未改；47固定resource fixtures與科學source保持。strict offline audit只出現157次允許的Git，真實namespace/mountinfo/cgroup讀取、ioctl、非Git子程序、physics imports均0。safe legacy audit為551Git＋5fixedPython＋1fixedsleep，HumanReview/forbidden imports0。

第一輪280項有2個舊介面斷言失敗，原始收據保留；更新record上限／cleanup record查找並保留原安全語意後，最終292通過。後續source審查補入private-frame publication繞過、terminal FULL claims與ID-map endpoint負面案例；最終收據覆蓋相同frozen bytes。沒有把失敗刪掉或改成kernel PASS。

guard實際64碼SHA：`404dfd1fb81a3fa9ad7cf18d511caf063674a325c2622785e7fca1d5f4fba123`；physics contract：`a8a093e2ec47283dd9cb503b2c83fe95b89df4761df5fb7afc623fa291c937cb`，皆保持歷史bytes。**附件guard字串是63碼，不能作SHA256 pin**；input_identity_review.json記錄原字串與真實值，未改檔案或默認建立執行重綁。後續授權需明確使用正確64碼。

before/after各核對50169內容觀測、3588706711bytes、122symlink targets，變更/錯誤/race0。這是既定historical baseline範圍，非all-host。STOP92原因仍未完全確立；B/C/D、StageA、events/cards/weights/binaries/收據未改。

## Gates與交付

**GATES_PASS**：source修補、292 offline、81 safe legacy、獨立來源及proposal審查、14檔案binding、真實完整Git核對、historical SHA256、physics bytes保存、未執行未授權kernel。

**GATES_FAIL**：附件scientific guard pin為63碼；歷史Pre mount拒絕及StopPost226失敗仍原樣保留。最終offline無未修復failure；本輪沒有新kernel結果可判FAIL/PASS。

**GATES_BLOCKED**：新service/ioctl/stress授權、persistent容量、full launch驗收、正式BUILD_ONLY/native zero-ME/ME/integration/events、binary review/physical restart。

**GATES_UNKNOWN**：歷史完整mount清單、確切namespace syscall根因、Ubuntu patched-source差異、WSL exact configuration、active quota、enclosed CPU/RAM/wall/swap與failure cleanup。

FULL_CONTROLLER_RESOURCE_ENFORCEMENT_IMPLEMENTED=false；FULL_LAUNCH_ENVELOPE_VERIFIED=false。

新的stacked Draft PR僅發布source/tests/bounded evidence；raw mount／raw environment／private source receipts留本機，public只有經審查投影及SHA。未推PDF/PNG、ROOT/LHE/HepMC、native binary、cache、private config。每次push前檢查staged/index與每個outgoing intermediate commit；PR24/32/33保持原head及Draft，無merge/force-push。GitHub CI結果在publication後另補，不能作kernel證明。

## NEXT_RECOMMENDED_STEP

先確認63碼輸入差異，再另行明確授權exact source133f14e的**一次namespace/mount inspection**。argv／fresh output／固定caps／stop conditions已獨立審查，見AUTHORIZATION_REQUEST_ZH_TW.md與proposed_kernel_scope.json。第一個範圍不含child、八階段、stress或physics；任何失敗立即停止，不retry／改flags／追加預算。persistent backend及完整lifecycle必須之後另行解決。

需要另行授權的依據為本次附件第5節：「本指令不授權新增 kernel attempt 或 stress run。」本報告與request均不是人類授權物件，也沒有產生或重用授權。
