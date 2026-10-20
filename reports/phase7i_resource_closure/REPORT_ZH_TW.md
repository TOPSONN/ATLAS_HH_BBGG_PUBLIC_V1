# Phase7I 非物理資源修補驗收報告

判定：**BLOCKED_PENDING_RAM_REVIEW_AND_LIVE_RESOURCE_VALIDATION**。來源修補、無害離線回歸與歷史保存已通過；完整資源服務尚未實測。沒有正式HH build、zero-ME configuration preflight、ME、integral、events、Pythia、Delphes或Phase7I物理啟動。

## 範圍與來源

從PR24 exact b80e16775bf141e45f4048c7197a8a99befaed51建立獨立分支codex/phase7i-resource-closure；舊PR／舊失敗收據／原安裝與物理資料保留。使用者只授權Phase7I source/tests資源修補、無害測試及stacked Draft PR。新增RAM profile依既有提案仍須先明確審核；已提出fixture512MiB/swap0及未執行正式提案2GiB/swap0，尚未收到回覆。

完整source binding與30項resource snapshot見source_binding.json；精確commit由Git提交後與PR本身提供。Source commit A e98c1600fd5a9d7763e0072b8b23423fbb988014 的完整Git preflight已通過：1415tracked／294critical、0.881s wall／0.345s CPU。後續僅測試HOME可攜性、CI checkout及報告修補；30項production bytes未變，03獨立補件確認。最終PR head仍須再做乾淨exact-head preflight，結果由PR描述與本機交付補充。

## 實作與獨立來源審查

1. Compiler TMPDIR/TMP/TEMP固定到獨立有byte／inode quota的private /tmp；work亦為受限tmpfs，host保持唯讀。
2. ldd改走bounded child runner；原本較寬的CPU／AS／FSIZE不再提高外層hard limit。
3. Service容納business imports、Git／source／toolchain preflight、copy、compile、loader、receipt、postflight與export。單一readonly global flock保障1job；compiler流程逐一執行，一核心，native workers仍1。
4. cgroup整組memory／swap、CPU quota、runtime、全組kill與empty/unpopulated readback；controller失去後仍需kernel runtime後援。啟動／觀測控制面及systemd manager另列，不能把payload計數說成整台主機計數。
5. 邏輯FSIZE不能限制fallocate KEEP_SIZE實際配置。新inherited allocation filter拒絕fallocate、寫入ioctl、xattr、AIO／io_uring等繞路；actual allocated blocks與filesystem假設另核對。沒有把純BPF測試當kernel證據。
6. 固定FD chunks/index保存strict USTAR；只驗證、不host extraction／execution。Bounded lossless checkpoint journal留在固定日誌，失敗不覆寫舊workspace；未完成的volatile scratch不宣稱完整保存。
7. CLI成功必須有完整unit／zero-ME／cleanup證據；未證實counter維持null。被封鎖的physical CLI不寫歷史收據。

獨立agent審查記錄作者分工：archive／allocation guard由該agent撰寫並自審，root-owned worker與adapters等由其獨立重新讀取。這不是外部人類binary或physics review。

## 實際測試證據

| 項目 | 狀態 | 證據／限制 |
|---|---|---|
| 新離線單元測試 | PASS | 138/138，0fail/error/skip；audit僅155次Git，0service/filter install/live probe/RAM stress/HumanReview/native；另13/13 alternate-HOME測試 |
| 固定安全legacy | PASS | 81/81；551次Git、5次固定Python、1次固定sleep；0forbidden imports／HumanReview；來源前後一致 |
| 歷史保存 | PASS | 50,169筆regular-path觀測、122symlink、3,588,706,711bytes重新SHA256，0變更；非all-host保證 |
| 獨立來源審查 | PASS（static） | independent_source_review_02.json；runtime gates仍BLOCKED |
| 真實資源matrix | BLOCKED | 47案，實際執行0案；RAM先審要求未解除 |
| 正式HH build／zero-ME | BLOCKED／UNKNOWN | 本次未授權、未執行，不能由fixture推論成功 |
| Genuine ME／integral／events | BLOCKED | 本次新增皆0，截面與誤差null |

完整47案包含正常六階段、各階段CPU/RAM/wall/disk/異常退出、aggregate CPU、controller loss、orphan、PID、namespace／來源／cgroup寫入、stdout、tmpfs bytes／inodes、export、missing approval、archive、allocation bypass及separate-open-description job-lock反例。每案必須真實執行且證明cleanup；目前均未執行。

## FAIL、BLOCKED與UNKNOWN

FAIL歷史保留：最初unit harness有2個relative-import錯誤；保存harness誤判122個既有symlink。兩者修正後實際重跑通過，原紀錄留本機且harness_history.json列明。來源審查曾發現的兩個CLI缺陷已修補、加入負例，最後138與81項均在修補後重跑；再修正test-only HOME路徑後，138項及13項alternate-HOME亦實跑通過。CI checkout明確使用actual PR source head，避免把GitHub synthetic merge當來源history。

BLOCKED：RAM profile明確審核、47案本機實測、filesystem allocated-overhead實證、之後另行exact BUILD_ONLY授權。新archive binary review reader與physical enclosure尚未完成遷移；physical CLI保持阻擋。

UNKNOWN：本機新service／syscall filter是否實際可用、正式compiler／loader／八zero-ME／四denial的行為、genuine HH積分與收斂。沒有新cross section，沒有借用舊B/C/D或其他source的歷史數值。

## 不變科學契約與發布

Corrected scientific guard仍404dfd1fb81a3fa9ad7cf18d511caf063674a325c2622785e7fca1d5f4fba123；physics contract仍a8a093e2ec47283dd9cb503b2c83fe95b89df4761df5fb7afc623fa291c937cb，bytes與b80一致。四seeds、CPU/wall各14400s、1job/worker、5GiB、retained physical LHE0保留。RNG/integrator/grid/weights/estimator沒有科學修改。

來源、tests與bounded文字證據可發布；PDF／PNG、native binaries、chunks/index、原安裝、events、私有完整manifest均不推送。每次push前檢查staged index與所有outgoing intermediate commits。PR保持Draft，不merge或force-push。

CI新resource job只跑離線方法與固定81項。舊closure full job對本分支明確SKIPPED，因其中包含自動測試授權物件／native methods；不標示該job通過。歷史readiness仍驗證原固定snapshot。CI通過也不能代替本機kernel資源實測。

下一關：先明確審核fixture RAM512MiB/swap0，再執行全新namespace的47案無害matrix；通過後才另提exact revision/output/完整scope的BUILD_ONLY審核。之後依序binary review、PHYSICAL_RESTART；Phase7J/K/L仍BLOCKED。

本報告的CI／final-head狀態為提交當時快照。最新exact head、read-only Git preflight與CI結論另列PR描述及本機交付；來源／方法成功仍不解除RAM與47案實測BLOCKED。
