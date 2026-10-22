# G2真實工具身分綁定與單次診斷審查

**PASS：三個使用者回報SHA256已綁定。完整diagnostic仍BLOCKED。** 本輪完成source-only工程、既有資料唯讀分析與離線／CI測試；沒有執行Ubuntu版本查詢、systemctl diagnostic或任何物理計算。下列containing commit與delivery CI是報告建立前快照，建立後由PR metadata與本機最終交付補上。

使用者回報的systemctl、python3、timeout SHA256與UID/GID1000、Python3.12.3、root-owned ELF64 x86-64及python symlink已版本化保存。normalized statement SHA僅標識本輪整理的使用者陳述；沒有原hash-only probe bytes，因此原raw SHA=null。這解除expected tool hash缺值，不構成獨立host attestation；TOOL_IDENTITY_VERIFIED=false。timeout僅綁定身分，不執行。

原diagnostic_capture.py、diagnostic_contract.py、diagnostic_tools.py、diagnostic_validate.py四份SHA256逐一相等，PR44三條systemctl argv與closed env完全不改；system/user bus僅既存socket、固定user@1000.service、禁止autostart/pager/password及fallback約束保留。實際socket與manager狀態未重新讀取，均UNKNOWN。source-family255文件不能證明installed版本。

新增獨立version-only候選，唯一child argv是/usr/bin/systemctl --version。它先拒絕未批准scope，再核exact source、實際tool hashes、Python3.12.3及UID/GID，檢查私有parent，pin systemctl FD及ELF hash，再重用既有bounded child。它不查bus／manager／cgroup，也不呼叫timeout。額外ELF parser只處理同一已讀binary bytes；PT_INTERP/DT_NEEDED格式解析不代表loader或transitive libraries閉合。實際ELF、stdlib與動態依賴未取得，維持UNKNOWN。

child5s、cleanup1s、adapter30s、每child8192 bytes、aggregate32768 bytes、receipt131072 bytes、lineage8層、0700 directory、0600 exclusive receipt均保留。這些是soft watchdog；不宣稱kernel hard CPU/RAM/wall envelope或power-loss持久性。receipt validator只驗另行取得的原bytes，檢scope/source/tool/人類reference/時序/partial-state/replay；synthetic正例不是實際能力。

本機212項為209 PASS與3 POSIX skip；Linux CI保留612/612 offline、81/81 legacy，affected212為211 PASS與1 Windows-only skip；Windows151為148 PASS與3 POSIX skip，含26 in-memory CIM。集合有重疊，不相加。C++20 inert arithmetic原source8例PASS，binary留local。source和CI不會呼叫新version collector，沒有kernel stress或新manager觀測。

精確source與新external statement建獨立run，6個source-only stage、12 ledger events；status/verify/resume-safe均exit0，resume沒有新child。舊PR44與更早completed run不重綁。1800份baseline中1796 byte-identical，4份只有CI routing/history相容更新；1019 frozen inputs中1018 scientific bytes原樣，唯一CI routing例外精確審查。原科學資料／工具安裝／historical failures不改。

交付8份指定文件，另有7份source／preservation／tests報告。本機精確命令包保存pending full/version scope、來源SHA、scope SHA及mapped Ubuntu路徑；public文件使用封閉entry contract，不發布private host/guest topology。兩份scope的human authorization_reference=null、execution_authorized=false；沒有產生或重用授權。

下一個可審的OS動作是單次版本查詢；仍需使用者另批准exact scope/source與安全parent，不能直接裸跑systemctl略過wrapper。完整diagnostic需先補installed family、依賴閉合、bus fallback／socket與private-parent證據並另批准；沒有憑本輪hash或日後version通過就自動接受B-V2／G3–G7。現在保存checkpoint並停止。

獨立審查指同agent的獨立parser及另worker/process；沒有第二位人類或外部host attestation。FAIL無現存source測試失敗；最初sandbox預設temp目錄拒寫已保留失敗歷史，改成測試程序內workspace temp，沒有elevation／host setting變更。全部未實測native數值維持null。

## 精確結果

- **TOOL_IDENTITY_OBSERVED**: true

- **TOOL_IDENTITY_VERIFIED**: false

- **INSTALLED_SYSTEMD_VERSION_VERIFIED**: false

- **DIAGNOSTIC_SOURCE_READY**: true

- **DIAGNOSTIC_EXECUTION_AUTHORIZED**: false

- **DIAGNOSTIC_ACTUALLY_EXECUTED**: false

- **G2_MANAGER_STATE_VERIFIED**: false

- **G2_CGROUP_DELEGATION_VERIFIED**: false

- **G2_ARCHITECTURE_ACCEPTED**: false

- **FULL_LAUNCH_ENVELOPE_VERIFIED**: false

- **PROJECT**: ATLAS_HH_BBGG_PUBLIC_V1

- **TASK**: PHASE7I_G2_REAL_TOOL_IDENTITY_BINDING_AND_SINGLE_USE_DIAGNOSTIC_REVIEW

- **BASE_PR**: 44

- **BASE_HEAD**: a0176ad0c684ea3f8a2d879090a1649485f225a4

- **PREVIOUS_TESTED_SOURCE**: d1a92efdace4c8e0ab480db6c5ab5dd9b7d11121

- **EXACT_SOURCE**: 55777dd8a21964dd87c7294550bd51cef73e5fa8

- **DELIVERY_COMMIT**: PENDING_CONTAINING_REPORT_COMMIT

- **PR_URL**: https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1/pull/45

- **CHECKPOINT_RUN**: 3bc2b439-3182-4bbe-a667-1f7405691028

- **ACTUAL_SYSTEMD_VERSION**: null

- **ACTUAL_DYNAMIC_DEPENDENCIES**: null

- **ACTUAL_MANAGER_STATE**: null

- **ACTUAL_DELEGATION**: null

- **ACTUAL_CPU**: null

- **ACTUAL_RAM**: null

- **ACTUAL_WALL**: null

- **ACTUAL_DISK**: null

- **ACTUAL_VERSION_QUERY_RECEIPT**: null

- **ACTUAL_DIAGNOSTIC_RECEIPT**: null

- **NEW_ME_CALLS**: 0

- **NEW_INTEGRALS**: 0

- **NEW_EVENTS**: 0

- **FORMAL_BUILD_ONLY_AUTHORIZED**: false

- **NEW_EXTERNAL_INPUT**: DIRECT_USER_NORMALIZED_STATEMENT_NOT_ORIGINAL_CAPTURE

- **NORMALIZED_STATEMENT_SHA256**: 6b50a8f8f70e475860c9293bfab6d2374f8a1c18101ed206a7dc24af412cd9e1

- **ORIGINAL_PROBE_RAW_SHA256**: null

- **GATES_PASS**: ["PR44_EXACT_SOURCE_AND_ANCESTRY","THREE_REPORTED_EXPECTED_TOOL_HASHES_BOUND","ORIGINAL_FOUR_MODULES_UNCHANGED","ORIGINAL_FIXED_THREE_ARGV_AND_ENV_PRESERVED","PENDING_SCOPE_REJECTS_BEFORE_LIVE_READ","EXACT_SHA_REPLAY_NEGATIVE_AND_PARTIAL_STATE_TESTS","INDEPENDENT_PURE_VALIDATOR_TESTS","REGRESSIONS_AND_LINUX_WINDOWS_SOURCE_CI","FRESH_SOURCE_INPUT_RUN_AND_RESUME","HISTORICAL_HASH_PRESERVATION"]

- **GATES_FAIL**: []

- **GATES_BLOCKED**: ["INDEPENDENT_LIVE_TOOL_ATTESTATION_NOT_OBTAINED","INSTALLED_SYSTEMD_FAMILY_UNKNOWN","DYNAMIC_DEPENDENCY_CLOSURE_UNKNOWN","CURRENT_BUS_SOCKET_AND_USER_MANAGER_CONDITIONS_UNKNOWN","PRIVATE_PARENT_UNVERIFIED","EXTERNAL_SINGLE_USE_APPROVAL_ABSENT"]

- **GATES_UNKNOWN**: ["PYTHON3123_ON_CURRENT_MACHINE_STDLIB_AND_EXTENSIONS","ACTUAL_ELF_INTERPRETER_AND_TRANSITIVE_LIBRARIES","CURRENT_MANAGER_VERSION_STATE","DURABLE_FAILURE_CAPTURE"]

- **CI_RESULTS**: {"source":"SUCCESS_FOUR_DECODED_LOGS","delivery":"PENDING_REPORT_COMMIT"}

- **FINAL_VERDICT**: PASS_SOURCE_AND_REPORTED_TOOL_BINDING_WITH_LIMITS; BLOCKED_ACTUAL_VERSION_DEPENDENCIES_AND_DIAGNOSTIC_APPROVAL

- **NEXT_ACTION**: Separately review exact version-only scope: one systemctl --version under existing 5s/1s soft wrapper; full diagnostic remains blocked. No action executed in this task.
