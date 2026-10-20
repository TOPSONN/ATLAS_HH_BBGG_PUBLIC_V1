# 待審：S4單次volatile controller；本文件不是授權

精確來源：114b5c00341be22982244d3d9548e80adf2d00e5。21檔SHA256見source_manifest.json；exact104-token argv與限制見proposed_kernel_scope.json。

來源離線449＋81通過，另有獨立來源/數值review。kernel/service/filter/probe均未於本輪執行。附件第7B節要求新的exact-source人類明確授權；不重用舊one-shot，不產生或輸入HumanReview/token。

提案只含一個正常single-Main八階段workflow與一個inert child；initial7只讀nsfs ioctl、一次guard安裝、最多18個fixed invalid-target呼叫。沒有stress、47案、compiler、loader、MG5/model、zero-ME、ME、integral、events、Pythia/Delphes。

CPU4秒、wall13秒、RAM512MiB、swap0、work8MiB/private1MiB、disk16MiB、onejob/worker不提高。CPUQuota是rate、LimitCPU是per-process；timer算術不是aggregate cumulative hard kill或完整wall證明。整組CPU/wall/cleanup與persistent control-plane容量未實測，正常一案成功也不能推為FULL。

需fresh service-private tmpfs。提議本機evidence directory尚未建立，並非controller argv的一部分；無custom host writer，持久capture須先具備另審capacity-backed出口。capture只在bounded volatile RAM，controller死亡可能遺失；不承諾durable failure receipt。systemd/journal/terminal不能默默排除persistent計帳。

Review須確認exactsource/21hashes/argv未變、unit/tmpfs不重用、scope/limits不放寬、無未知rw、control-plane/capture邊界明確。若要求source/backend變更，凍結新revision重新review，不執行此舊argv。

第一個source/namespace/mount/resource/I/O/cleanup gate失敗即停止相依流程、保存bounded partial、無retry/substitute。managercleanup只能靠獨立bounded readonly postmortem，Main仍活不能自稱empty。

後續S4成功只得volatile限定證據；persistent blocks/inodes/metadata/control-plane、全組CPU與wall/cleanup負例未閉合時B/C/formal仍BLOCKED。本文件不提出BUILD_ONLY核准、不改科學契約、不dispatch。完整報告見REPORT_ZH_TW.md。
