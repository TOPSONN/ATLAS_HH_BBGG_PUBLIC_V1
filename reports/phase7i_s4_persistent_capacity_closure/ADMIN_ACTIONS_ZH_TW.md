# 管理員操作架構與 P1 安全關卡

**NOT_APPROVED — 不得執行磁碟附加、provision、format、mount、quota、service修改、S4或build。**

本版取代PR36中的可貼上操作recipe。舊文件完整保留在[61b32c0版本](https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1/blob/61b32c0aa86456cf43051aa18a6ea692f9e22c7f/reports/phase7i_s4_persistent_capacity_closure/ADMIN_ACTIONS_ZH_TW.md)，SHA256 f99dcf197c03b75b26f50e49fb2af8d29e2219b21a721b03367b32393683a83c。其mkfs/mount片段為歷史NOT_APPROVED資料，不應執行。本版不提供一貼上就會格式化的script，也不自動選空白磁碟。

## 先審完整架構，不先做小磁碟

選定A為滿足原合約的嚴格目標：專用隔離執行環境＋VM外、仍計入總額的可信collector/guardian。B為保留WSL的備選，將shared host成本列為外部信任邊界，必須另送V2修約；weaker_than_original=true、user_accepted=false，不能視為原規格PASS。

完整比較與CPU/RAM/wall/disk帳本見 reports/phase7i_admin_architecture_p1_closure/ARCHITECTURE_ZH_TW.md，證據布局見同目錄EVIDENCE_PROTOCOL_ZH_TW.md。新JSON proposals可用安全CLI檢查一致性，但成功只代表source policy，不是host真實性、管理員批准或操作准入。

## 三個P1的來源修正

P1-A：device_policy.py以完整guest graph雙向展開parent/descendants/siblings/holders/slaves，與root及所有protected historical storage的整個connected component比較；另外比對host stable identity及完整host ancestors。未知/缺graph、alias衝突、host身分不符、未證明backing、任何protected交集均拒絕。目前非單純獨立whole disk的partition/dm/loop/stack一律拒絕，不嘗試猜測安全。signature不存在不是disposable證明，還須獨立provisioning provenance。

P1-B：原始mountinfo與findmnt exact/nested/covering必須一致，目標本身及其下有mount/bind一律拒絕；bind ancestor、其他job lease、namespace/boot/collector身分不符、symlink/path traversal、path前後身分或型別改變、與covering filesystem st_dev不符、ownership/mode不符均拒絕。空目錄不是未mount證明。

P1-C：舊路徑重開的外部mkfs/mount消費者已在新介面無條件拒絕。instance_binding.py要求acquire→before_operation→after_operation→before_release四階段持續同FD／kernel claim／host hotplug排除，綁完整reviewed device+mount policy digest、diskseq、st_rdev、size、by-id target、host instance、namespace/boot、helper start與lease identity。這是可測試交易模型，**不是已部署helper，也未證明kernel TOCTOU已關閉**。privileged_operation()始終拒絕，重比路徑或major:minor不能代替排他性。

所有snapshot屬UNATTESTED_INPUT_CONSISTENCY_ONLY。完整JSON也不能自行證明它涵蓋全部namespace、protected storage或host writer。真正唯讀acquisition adapter及同FD privileged consumer均須另審；本輪不將JSON當能力。

## 獨立核准階段

| 階段 | 可審內容 | 必須先交付 | 不包含 |
|---|---|---|---|
| G0 source/design review | 本輪guard、協定、架構與offline證據 | exact source SHA、review／negative tests | 任何host變更 |
| G1 read-only inventory | 管理員限定host/guest拓撲與namespace acquisition | 需讀的host命令、是否需啟動Ubuntu、raw保存位置及輸出邊界 | disk attach、service restart、quota GETQUOTA |
| G2 architecture decision | A控制能力／實體帳本；或另審B-V2修約 | cumulative CPU及whole-wall enforcer、host backing/log/collector邊界 | 自動接受較弱合約 |
| G3 helper/security review | 同FD consumer與host排他／hotplug邊界 | helper exact source/binary、fd/instance/namespace proof、工具不重開路徑的證明 | 實際mkfs/mount |
| G4 provisioning | 只有明確新裝置與限定變更 | 真實host serial/WWN/backing、guest by-id/MM/diskseq、全protected graph、可拋棄性 | format、mount、S4 |
| G5 formatting | 單一已綁定新裝置 | 新exact source+device instance freeze、G3能力已驗證、明確單次授權 | 自動mount或重試 |
| G6 post-format review | UUID/label/geometry/journal/hash核對 | 原始raw、blocks/inodes、完整新FS身分 | 自動mount |
| G7 mounting | exact新FS與未使用mountpoint | pinned namespace/path/parent/leaf證據、mount後FS root權限與collector writer配置 | S4、壓測或build |
| G8 rollback | exact新job配置／mount的回復 | writers停止、失敗證據已保存、裝置仍同一instance | lazy unmount、刪歷史logs、重新格式化 |

G4/G5/G7/G8都要各自授權，不能因guard成功就往下一步。沒有管理員提供的真實身分即BLOCKED，沒有任何推測/dev/sdX或PHYSICALDRIVE編號。後續無害kernel正反測試、單次S4、BUILD_ONLY、binary/physics另走獨立關卡。

## G1 inventory需要的資料（不是本輪執行命令）

Windows：stable device ID／serial／WWN或等價身份、整個host backing graph、partition/sibling、實體容量、thin/sparse/snapshot/expandable狀態、與Windows root/歷史資料的關係、使用中references。若virtual disk，包含container與其外層filesystem身分、allocated blocks/metadata/journal，不接受logical size或單次du代替hard bound。

Guest：by-id解析前後、exact MM／diskseq、whole-disk parent及所有descendants/siblings/dm/loop/holders/slaves、root與每個protected filesystem backing、所有相關mount namespace及既存mount references。mountinfo/findmnt必須綁定同一collector PID/start/boot與前後namespace readback，不能將多個無關shell的輸出拼成一份attestation。

資料僅存管理員受保護的本機raw區，公開報告只保bounded投影與SHA256。真正的可丟棄性來自host provisioning紀錄，不來自wipefs結果。若本機沒有running distro，啟動Ubuntu及診斷user-session的範圍須先明定；舊warning仍UNKNOWN，不能順手restart、改linger或代換session。

## 同FD helper的必要邊界

持續持有經fstat/ioctl與host身分綁定的裝置FD，確切bytes與diskseq；kernel-backed claim不能只用cooperating-process flock代替。須排除所有host writers與hotplug/re-enumeration，不只guest中的其他mkfs；普通O_EXCL也不能未經分析就視為完整host排他。operation必須消費同一已開啟實例，不可回到路徑重新open。

實際operation前/後的身分、claim、namespace與source/hash均要核對；任何變化/UNKNOWN停止且保存現場，不自動close再開或重選裝置。若installed tools不能安全消費同FD，就維持BLOCKED，另審具體helper或管理員exclusive操作程序。本版沒有實作privileged consumer，沒有可用來apply的CLI。

## 容量、權限與失敗收據

不放寬原S4 disk16MiB、CPU4s、whole-wall13s、RAM512MiB/swap0；未來disk5GiB、CPU/wall14400s、RAM2GiB/swap0亦不變。work8＋private1＋persistent候選4MiB只占已知13MiB，3MiB仍未封閉；build2.25＋候選2GiB是4.25GiB，768MiB亦未封閉。

metadata、journal、inodes與失敗reserve要實際納入固定容量；log rotation/rate-limit、S3 logical slots、tmpfs或新4MiB裝置都不能當完整persistent PASS。外部manager/journal/syslog/terminal/host成本未界定前不能run。

掛載前leaf0700不是掛載後ext4 root權限。需獨立的collector UID、worker不見或readonly evidence mount、無worker evidence FD／unlink／truncate／punch-hole能力；不准臨時chmod放寬。8固定槽事前建立/sync/reopen只是source fixture；真正blocks/inodes/metadata與滿盤後同步、controller死亡後capture及collector自身故障仍需另審實證。

沒有資料就UNKNOWN/FAIL；不得補0、重建native結果、由死亡worker發出新terminal。unit/cgroup不存在不是empty證明。

## 可實際執行的安全source review例子

只在新source checkout內使用已安裝Python；以下不讀真實裝置、不開service、不寫snapshot來源，也不能取得執行權限：

    python3 -B -m simulation.hh_signal.final_closure.resource_closure.admin_review --kind architecture --input simulation/hh_signal/final_closure/resource_closure/config/admin_architecture_A.json

    python3 -B -m simulation.hh_signal.final_closure.resource_closure.admin_review --kind architecture --input simulation/hh_signal/final_closure/resource_closure/config/admin_architecture_B.json

device/mount/transaction模式只檢查另審acquisition提供的bounded JSON；即使回PASS_*_POLICY_ONLY，operation_authorized仍false。CLI沒有apply/format/mount模式。

最小下一授權範圍：G1限定唯讀host/guest inventory＋G2架構能力審查。先取得真正裝置與控制能力，再審helper；目前不請求provision/format/mount批准。
