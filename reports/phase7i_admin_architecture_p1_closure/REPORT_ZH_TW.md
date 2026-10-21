# Phase7I 管理員架構與 P1 安全來源驗收

本輪完成安全來源修補、實際離線正反測試、三組獨立來源審查及歷史保存核對。**執行准入仍為 BLOCKED；本報告不構成任何管理員、kernel、S4、build 或物理授權。**

Base 為 Draft PR36，HEAD `61b32c0aa86456cf43051aa18a6ea692f9e22c7f`；原工程版本 `74f8dc3dd53502a430676c7327a4eb8801f7afca` 保留。這次精確測試及提交的 source 為 `e8709b27103dd0aa1fad1c7d06192ab1cf1d8d6e`。後續 delivery commit 只新增本目錄報告與數值證據，不改測試過的實作。

## 驗收矩陣

| 項目 | 本輪判定 | 證據與限制 |
|---|---|---|
| P1_DEVICE_GUARDS_SOURCE_VALIDATED | PASS，僅 source／model | device、mount、transaction 一致性及拒絕邏輯，36 個 targeted tests；輸入仍為未認證 JSON |
| ADMIN_ARCHITECTURE_READY_FOR_INDEPENDENT_REVIEW | PASS，設計可審查 | 選定 A 的嚴格目標及 B 的未接受 V2；所有部署與資源證明仍 BLOCKED |
| DURABLE_EVIDENCE_DESIGN_REVIEWED | PASS，設計／普通檔案 fixtures | 真實 reserve／fsync／reopen，19 個 targeted tests；非 protected storage 或斷電持久性證明 |
| RESOURCE_BOUNDARY_GAPS_EXPLICIT | PASS，缺口已列明 | 原上限未改，沒有將外部成本或 watchdog 超調藏入 PASS |
| 真實 device／host topology 與 acquisition adapter | BLOCKED | 沒有管理員提供並認證的完整 host／guest／歷史 storage 清單；本輪未查裝置 |
| P1-C 實機 TOCTOU 封閉 | BLOCKED | 沒有同 FD privileged helper、host writer／hotplug 排他證明；實際操作介面無條件拒絕 |
| 固定持久容量、allocated blocks／inodes | BLOCKED | host backing、metadata、journal、failure reserve 未實證；32KiB logical slots 不能替代硬限制 |
| 整組累計 CPU／完整 wall／RAM／cleanup | BLOCKED | 未部署或實跑完整強制機制；零超限不能宣稱 |
| WSL user-session／journald／rsyslog 實際健康與容量 | UNKNOWN／BLOCKED | 保留原 warning；未重啟服務、改設定或在本輪驗證原因 |
| 架構 B-V2 修約 | NOT_APPROVED | weaker_than_original=true、user_accepted=false，不能替代原合約 |
| S4／正式 BUILD_ONLY／physics | NOT_AUTHORIZED | 本輪實際執行均為 0 |

## 三個 P1 的實質改動

P1-A：新增 `device_policy.py`，以完整 guest 關係圖雙向展開 parent、children、siblings、holders、slaves，與 root 及全部 protected historical storage 的整個 connected component 比較；另綁 host stable identity／ancestors、by-id、major:minor、diskseq、容量與 backing 屬性。alias 衝突、parentless partition、不完整圖、共用來源、thin／sparse／snapshot／expandable 或未知身分均拒絕。只支援簡單獨立 whole disk 候選；partition／dm／loop／stack 保守拒絕。無 signature 不代表可拋棄，另需 provisioning provenance。

P1-B：同一 policy 模組要求 mountinfo 與 findmnt 的 exact／nested／covering 一致，核對前後 namespace／boot／collector、整條 path metadata 及實際 covering mount 的 st_dev。既有或 nested／bind mount、bind ancestor、其他工作 lease、symlink／traversal、ownership／mode／型別變化均拒絕；空目錄不能當未掛載證明。

P1-C：`instance_binding.py` 實作四階段同實例交易模型，要求 acquire→before_operation→after_operation→before_release 持續相同 FD、diskseq、size、host instance、namespace／boot、helper start 與 lease；交叉核對 device／mount policy digests、root 裝置、候選不在任何 mount row，以及所有非 volatile mounted storage 均在 protected inventory。舊 mkfs／mount 重新由路徑開啟的 consumer 類型拒絕。`privileged_operation()` 始終拒絕，沒有部署 helper；不能以模型中的 claim-held=true 代替 kernel／host 排他證據。

獨立審查實際重現後補上的負例包括「candidate 在另一份 snapshot 已是 root」、「protected partition 隱藏 parent」、「postmortem 換 unit／InvocationID」及「A／B 互換標籤」。最終重新測試均正確拒絕。詳見 `independent_reviews.json` 與各本機 raw receipt 的 SHA256。

## 選定架構與完整計帳

選定 **Architecture A** 作為原合約的嚴格工程目標：專用可丟棄隔離環境，guest controller／單 worker 與 VM 外 collector／guardian 分開死亡域；host collector、launcher、manager／logs、虛擬磁碟 backing／metadata 仍全部計入同一 aggregate。VM 本身不會封閉 host 成本，目前沒有可直接准入的部署。

**Architecture B** 保留既有 WSL／systemd，worker、controller、collector 同一受限 aggregate，排除 manager／journal、launcher、host backing 三類既有共享成本。此排除只存在 `BOUNDARY_AMENDMENT_CANDIDATE_V2`，尚未接受。validator 禁止 A／B 只換標籤，或讓每個 role 各領一份原總額。

| 資源 | 不變原合約 | 目前未證明的能力 |
|---|---|---|
| CPU | S4 全組4s；build 全組14400s | 全部 user＋kernel CPU、controller／collector／host 成本的累計停止；CPUQuota 是速率，非累計 hard cap |
| Wall | S4 activation→cleanup13s；build14400s | 啟動前 armed、包含 capture 與 cleanup 的獨立 watchdog；一般排程不能提供零延遲保證 |
| RAM／swap | S4 512MiB／0；build2GiB／0 | 全組含 host 成本；memory.max 的暫時超調語義不能被忽略 |
| Disk | S4 16MiB；build5GiB | 所有 work／private／persistent／logs／host backing／metadata／journal／inodes／failure reserve 的實體硬界線 |
| Job／worker | 1／1 | collector 不能成為免費額外資源；完整 membership、controller-loss 與 orphan cleanup 另需實證 |

S4 已知候選分配為 8＋1＋4=13MiB，3MiB 尚未封閉；build 為2.25＋2=4.25GiB，768MiB 尚未封閉。這是需求帳，不是容量證明。原16MiB／4s／13s及未來5GiB／14400s皆未放寬。

build 的2.25GiB tmpfs是兩個filesystem的容量上限，並非已保留或可同時使用的RAM；在整組RAM2GiB／swap0及controller／collector／guest開銷下，不能承諾兩者同時填滿，ENOSPC／OOM後的故障收據亦未實證。

官方文件核對：[systemd255 CPUQuota](https://www.freedesktop.org/software/systemd/man/255/systemd.resource-control.html) 定義百分比／期間；[Linux6.6 memory.max](https://www.kernel.org/doc/html/v6.6/admin-guide/cgroup-v2.html) 允許特定情況暫時超限；[systemd255 LogNamespace](https://www.freedesktop.org/software/systemd/man/255/systemd.exec.html) 不支援 user service。這些語義不能替代本機部署證據。詳見 `ARCHITECTURE_ZH_TW.md`。

## Durable evidence 的實作與限制

`evidence_slots.py` 只開放 `offline_fixture_only=true`。8個固定4096B槽，checkpoint4／postmortem2／failure2，工作前建立32768B reserve，file／directory／parent fsync及reopen。固定frame含身份、sequence、collector monotonic clock、SHA256與commit marker；先sync body再sync commit，重新open與整組scan通過才ACK。

occupied／torn slot 永不重用；foreign run／boot、duplicate／replay、錯序／clock、型別混淆、缺slot／metadata錯誤均拒絕或UNKNOWN。DEAD為absorbing state，同worker所有postmortem固定cgroup／unit／InvocationID／PID身分。native_result只准null，不存在的數值不補0。已commit但ACK丟失也不覆寫。

worker死亡前的checkpoint、獨立collector事後觀測及無法恢復的資料三者分開。collector若同時死去、outer budget用盡或raw capture丟失，最後只能UNKNOWN。普通檔案的advisory lock不是UID隔離；source沒有建立protected writer權限、真實固定filesystem或硬體flush保證。詳見 `EVIDENCE_PROTOCOL_ZH_TW.md`。

## 真正執行的測試

| 執行 | 結果 | 實際涵蓋 |
|---|---|---|
| audited offline 合併回歸 | 612 PASS，0 fail／error／skip | 保留原542 IDs，新增70；Git fixtures、純模型、普通小型檔案，來源前後一致 |
| exact safe legacy | 81 PASS，0 fail／error／skip | 舊81 IDs完全相同；含固定無害 child timeout／Git fixtures，不是整組kernel資源測試 |
| 獨立 device review | 36 targeted PASS | 另5個純JSON矛盾重播均拒絕 |
| 獨立 evidence review | 19 targeted PASS | ordinary reserve／fsync／reopen與注入故障；E08修正已重驗 |
| 獨立 architecture／CLI／publication review | 15 targeted PASS | A／B重標負例拒絕，靜態CI條件矩陣核對 |
| 安全 CLI | A、B各實際 exit0 | 只檢查proposal一致性，operation／FULL等旗標false |

70個獨立 targeted tests 是合併612的子集，不能重加為另一批覆蓋。audited runner沒有 forbidden attempt；其邊界是已審固定測試，Python audit不提供一般sandbox，stat／symlink alias與directory FD目標仍需來源審查。

normal、SIGKILL、OOM、wall timeout、ENOSPC、collector crash、partial write與replay均有offline模型／fault injection；本輪沒有真的製造OOM、填滿filesystem或執行resource service／stress。早期591項的5個失敗、599項的2個fixture／訊息失敗、602／608項的中間成功及所有獨立缺口重現保留。保存工具兩次失敗（歷史script mode誤判及新clone無Git author）也保留，沒有改測試expected或放寬runtime gates。

## 歷史保存、發布與下一步

核對基底1532 tracked檔案，1526 byte identity不變；6項預期變動為四份CI、offline runner及指定ADMIN文件。原334檔manifest有329份SHA256完全相同，其餘僅四CI與runner。兩份physics contract都仍是 `a8a093e2ec47283dd9cb503b2c83fe95b89df4761df5fb7afc623fa291c937cb`；原build／fixture profile不變。全部原542／81 IDs保留，controller與scientific runtime未修改。

舊ADMIN全文仍在原Git commit，SHA256 `f99dcf197c03b75b26f50e49fb2af8d29e2219b21a721b03367b32393683a83c`。新版撤回可直接貼上的format／mount recipes，拆成G0–G8獨立審核。舊PR36與其checkout未改；外部MC歷史樣本本輪未讀、未重掃或寫入，不能由tracked驗證宣稱已重新驗證全部外部資料。

發布僅包含明確19個source／tests／config／CI／ADMIN路徑與本目錄bounded報告；publication gate檢查每個outgoing intermediate及index，禁止未核准PDF／PNG、raw captures、events、binary與private設定。此處不產生圖表。GitHub CI執行結果須以實際HEAD job readback另列，不把靜態條件審查當hosted成功。

最小下一步是**另行審核G1限定唯讀inventory＋G2架構能力**：管理員先交出真實完整device／protected storage身分、host writable成本帳本、累計CPU／whole-wall控制能力、collector UID／生存域／raw retention設計，以及user-session warning診斷範圍。若A不可提供，是否審B-V2是獨立決策，不能默認接受。之後才審同FD helper及逐項provision／format／mount；kernel正反測試、S4、BUILD_ONLY與physics各自另授權。

`ADMIN_PROVISIONING_APPROVED=false`；`FULL_LAUNCH_ENVELOPE_VERIFIED=false`；`S4_EXECUTED=false`；`BUILD_ONLY_AUTHORIZED=false`；`FORMAL_BUILD_ONLY_AUTHORIZED=false`；`PHASE7I_PHYSICS_VALIDATED=false`。
