# 固定槽證據協定與死亡邊界

狀態：SOURCE/OFFLINE FIXTURE IMPLEMENTATION。evidence_slots.py真正實作普通檔案的reserve、write/sync、reopen及strict scan；尚不是已部署的protected filesystem writer。唯一建構模式為offline_fixture_only=true，production模式一律拒絕。沒有device open、mount、service、native/physics dispatch。

## 有界布局

固定8 slots，每個4096B，總logical payload/reserve32768B。checkpoint4槽、postmortem2槽、failure2槽。工作前以O_EXCL建立全部槽、寫滿零、逐檔fsync、directory與新directory的parent fsync、重新讀回。正式部署還須證明allocated blocks/inodes、metadata/journal及ENOSPC後的可寫性；ordinary fixture的st_blocks不是容量後端證明。

每槽frame為固定magic、length、payload SHA256、canonical JSON、zero padding、最後commit marker。資料包含source revision/SHA256、run UUID、stage、collector boot UUID、event UUID、sequence與collector單調時間；postmortem另外綁unit、InvocationID、cgroup path/dev/inode、MainPID、boot及原始資料digest。raw digest只保完整性，不證明來源真實；可信collector必須自行收集、保存raw及peer身分。worker無任意protected write，不能藉source接口取得此權限。

## 提交與恢復

1. 一個collector writer，受instance nonreentrant lock、owner thread檢查與跨cooperating-process advisory lock保護。這不是worker access-control；production須另配UID/mount/FD隔離。
2. 找該lane的全零槽；任何非零或torn槽都永不重用。不刪除、不truncate、不覆蓋已佔槽。
3. 先寫body（無commit），file fsync；再寫commit，file fsync；directory fsync。
4. 關閉writer FD，重新open同一pinned directory內的固定regular file，驗證owner/mode/nlink/size/blocks、frame/hash/identity、全store序號／時鐘／其他槽未變後才回ACK。
5. ACK只代表該普通fixture的sync/reopen syscall成功；不是硬體power-loss、host cache flush、實際容量或worker隔離證明。磁碟或collector故障時可以沒有ACK，即使事後看見完整bytes。
6. retry不得覆蓋「已commit但ACK丟失」的槽。掃描可辨認event id及原frame；同event重送拒絕。外部controller須以event id查詢已存證據，不能重新編造一次native結果。

scan區分全零空槽、完整合法frame、torn/corrupt/foreign/replay。缺slot／symlink／hardlink／metadata不符拋FAIL；損壞frame及無法恢復的時間/身分關聯回UNKNOWN並保raw hash。舊有效checkpoint仍可讀；獨立postmortem或failure可使用各自reserve，整體仍UNKNOWN。不存在的CPU/內存/終結值保持null，不補0。此階段native_result只能為null，任何重建native結果的payload都拒絕。

## 三種不同的事實

| 類型 | 產生者與可宣稱範圍 |
|---|---|
| 死亡前checkpoint | collector在worker仍活時已存的紀錄；不等於之後工作完成 |
| 死亡後postmortem | 仍活著的獨立collector，依有raw binding的死亡/資源觀測產生；不是死去worker的新terminal |
| 不可恢復資料 | 尚未送達、未commit、corrupt、collector/host同時失去或cgroup卸載前未擷取的資料；UNKNOWN/FAIL，不能推估成結果 |

DEAD_OBSERVED對同一run/worker是absorbing state，不接受後續RUNNING checkpoint。同一run的所有postmortem固定綁定同一unit、InvocationID、cgroup path/dev/inode、MainPID及boot；append拒絕切換身分，scan把即使hash合法的切換紀錄判為UNKNOWN。跨boot單調時鐘不可混用。collector本身死後不能自己製造postmortem；重啟/接管需另審同run恢復與原始boot domain，host reboot後只可forensic讀舊證據，不繼續原run。

## 測試與尚待實證

已實作offline正反案例：normal/reopen、32KiB事前reservation、checkpoint lane滿而failure reserve未動、SIGKILL/OOM/wall-timeout語義模型、pwrite ENOSPC與partial、collector commit前crash模型、第一/第二/dir fsync失敗、commit但沒有ACK後retry、hash/sequence/type/clock/foreign-run/boot/replay、重入/foreign-thread及worker resurrection拒絕。它們是普通小型temp files與fault injection；沒有真的kill程序、OOM、填滿filesystem、重開機或執行S4。

正式准入仍需：不同worker/collector UID及私有namespace證明、同FD writer、實體已配置容量、完整控制平面hard bounds、storage flush支援與真的ENOSPC/inode/OOM/timeout/controller-loss/collector-crash正反收據。若outer budget kills所有trusted角色，最後terminal仍可UNKNOWN；不得承諾任何故障下都產生完整最後收據。
