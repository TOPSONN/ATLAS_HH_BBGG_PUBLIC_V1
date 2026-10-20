# 待明確授權：單次 namespace／mount inspection

**NOT_AUTHORIZED — 本輪未執行。**

本次附件第5節明確禁止新的kernel attempt/stress，要求先交付exact source/argv/resource/output/stop conditions。因此這是下一次執行的審查請求，不是授權收據或token；不會由Codex代為核准。

- Source：`133f14e6f3f05189c706e183eb5dc86bde339376`。
- Clean detached checkout：`/home/btu/projects/atlas_hh_phase7i_ns_inspection_133f14e`；official origin、regular.git，兩次真正full tracked preflight PASS。
- Controller SHA256：`fb7ace1034f396f32107fffc2dabea91e24013d538efa7debf68ea3eb53e8656`。
- 14-file identity：`52fdbddb97108aa1c89a0f7f022bf736b485974d20d9e0ff48bd3f62ab0d0dcb`。
- Exact Linux argv：本目錄`proposed_kernel_scope_01.json`／GitHub`proposed_kernel_scope.json`中的104-token argv；只用single ExecStart的namespace-inspection，46項properties，沒有Pre/StopPost自訂命令。
- 固定unit：`atlas-hh-phase7i-namespace-recovery-01.service`。只允許1次，不替換／不retry。
- Fresh output：`C:\HH\.local\phase7i_namespace_storage_recovery_v1\kernel_inspection_01`，目前不存在。原始stdout/stderr、mount bytes／frames、manager/journal/cgroup證據只存本機；不自動push。
- 固定caps：CPU4s、wall13s、RAM512MiB、swap0、work8MiB、private1MiB、disk16MiB，1job/worker。參數不重新審問、不提高。Runtime timer8s、activation1s、stop/final kill各0.5s，nominal10s／3.003CPU s。
- 行為：readonly mount/cgroup/rlimit readback、5個nsfs type及2個owner readonly ioctl、UID/GID map／CapEff/NNP/seccomp／lo核對、有界local raw capture及safe projection。**沒有child、八階段workflow、compiler/loader/MG5/model/ME/integration/events。**
- 隔離：保留PrivateUsers/PrivateNetwork/PrivateIPC=yes、RestrictNamespaces、capability空集合、NNP、readonly source/cgroup及tmpfs caps。
- 界線：persistent hard quota尚未建立，這次只能作partial diagnostic；stdout與事後manager讀回是明列的診斷control plane，不能拿來宣稱完整disk／full-job enclosure。預定stdout protocol有界，原始capture超16KiB或projection超16KiB即INCOMPLETE/FAIL。

立即停止條件：任何啟動／namespace fallback、mount parser/guard、cgroup/effective limits、owner/maps、receipt completeness、資源／output、清理異常或讀回缺失。保存第一次原始證據；只做exact-unit必要清理與唯讀取證。不換user、不放寬flag、不sudo/install/remount、不追加或替代attempt。沒有這次成功證據前，不執行47案/stress；即使成功也不解除persistent或正式physics gate。

還需確認輸入pin：附件guard是63碼；歷史正確且未變的64碼為`404dfd1fb81a3fa9ad7cf18d511caf063674a325c2622785e7fca1d5f4fba123`。後續明確授權必須指向這個真實值及上述exact source。Physics contract仍為`a8a093e2ec47283dd9cb503b2c83fe95b89df4761df5fb7afc623fa291c937cb`。

typed `launch-live-diagnostic`仍拒絕；`describe-diagnostic`只產生提案，沒有暗中啟動。任何真正systemd invocation只能在新的明確人類授權後，逐項核對上述argv/source/fresh output再執行。
