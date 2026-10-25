# 下一次Manager獨立批准：目前BLOCKED草案

Version-only批准已消耗；禁止重用其reference或retrospective record。新的批准必須在新exact source、原三argv/env、10-file closure、native scope/source storage與runtime manifest完整核對後，綁新的pending canonical scope SHA。record provenance只可USER_PROVIDED_VERBATIM_APPROVAL_REPORTED；沒有原message ID/簽章就不捏造身分認證。

目前沒有scope/source實際FS identity，也沒有child動態解析closure provider，不能直接批准後執行。下一步應先另審最小native資料staging/identity與runtime closure採集範圍；本任務不授權建立Linux目錄或採集。若provider需要新source，必須再次exact-source review，不能用外部JSON旗標繞過現有BLOCKED。

未來單次診斷提案只含固定manager三查詢與原snapshot、必要private attempt/receipt；5s/1s/30s soft及所有bytes/lineage上限不變。不接受B-V2、不准service/cgroup/device寫入、quota、mount/format、install、WSL啟動/重啟、sudo、kernel stress、S4、BUILD或physics。失敗保留證據，不換output/retry。
