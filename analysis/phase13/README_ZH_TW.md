# Phase13：獨立 MG5 runtime 與 parser 準備

**目前狀態：BLOCKED_PHASE13_RESOURCE_ENFORCEMENT。** 本階段沒有啟動 MG5、import model、解析 process、數值 ME、積分或產生事件。13 項無害 kernel fixtures 證明單一 child 的限制，但完整 supervisor/job envelope 尚未驗證；目前 launcher 與 direct child 都會拒絕派發。

程式與報告在新的 ext4 checkout `/home/btu/projects/atlas_hh_phase13_v1`。原 Phase7I–12 checkout、原 MG5 config、既有 PDF 與科學資料維持原樣。branch 為 `codex/phase13-isolated-mg5-parser-readiness`，以 PR29 的 `d95ca4c98352f460af955a1bad5372f63cfcee4a` 為 base。保留所有舊失敗 receipts，不執行自動 merge／force push。

## 已建立的本機資料

`/home/btu/simulations/hh_phase13/run_01/runtime_01/private/mg5` 是完整來源複本，4733 regular files／133901130 bytes；無共享 hardlink。45 個相對 symlinks 都解析在新 tree，兩個原本 broken internal links 明確保留。raw config 保持 9302 bytes、SHA256 `e4567fd50d47a317407eb10cca76387053cdf06631949773296314702f77dca1`；歷史 writer 仍 `UNKNOWN`。9305-byte `mg5_path` 提案另存 private/config_proposals，**未啟用、未核准**。

public identities 在 `isolated_runtime_identity.json`、`installed_runtime_preservation.json`；full tree manifest／設定內容／binary／既有測試 LHE fixture 僅在本機 private 目錄，不進 Git。

PDF 沿用 Phase12 已下載的 `NNPDF30_lo_as_0130_nf_4` member 0／ID263400／DataVersion2，沒有新下載。`pdf_backend_review.json` 與 `alpha_s_reference_review.json` 僅做來源、metadata 與現有 native04 證據的當前 byte closure；不重做 native PDF evaluation。MG5 數值 binding 保持 `UNVERIFIED_NOT_EXECUTED`。原 strict alpha_s diagnostic `2.626248635282933e-6 > 1e-6` 保持 FALSE，不放寬或改寫舊判定。

## 可重跑的 offline tests

在新 checkout 執行以下命令只做 synthetic/source tests；不使用 MG5：

```bash
cd /home/btu/projects/atlas_hh_phase13_v1
python3 -B -m unittest discover -s analysis/phase13/tests -v
python3 -B -m unittest discover -s analysis/phase12/tests -v
python3 -B -m unittest discover -s analysis/phase11/tests -v
```

實際 kernel fixtures 只接受固定 harmless enums。已執行的 `resource_01` 不可覆寫；任何補測須另立 fresh output 並保留 aggregate source-job ledger。不要把 unit tests 或 synthetic fixtures 當作 MG5 parser 驗證。

## 未來 parser 審查

精確命令與 scope 由 [parser contract](../../metadata/phase13_parser_review_contract.json) 和 [report E](../../reports/phase13e_parser_execution_contract.md) 定義。三個 semantic commands 為 model import、p4 alias、symbolic generate，另有 quit terminator；沒有 output/codegen/build/check/launch/ME/integration/events。

本機 `parser_only_approval_package.json` 將綁定本次完整 source commit、逐檔 source bytes、runtime/config/model identities、process、fresh output 與 resource blockers。**目前不是可啟動的核准申請**：`execution_eligible=false`。新授權檔也不能越過未完成的 whole-job resource gate。下一步應先做最小 containment 修正及無害全工作測試，公布新 exact source 再評審。通過後才能另向使用者請求綁定 source/scope/limits/fresh output 的授權；不能使用 Phase7I 消耗過的 BUILD_ONLY。

## 科學限制

`sm` default restriction MB4.7、MC0；p4 不含 bottom。QCD/QED 標記是 amplitude bounds，process 未解析。maxjetflavor4 的 b 不屬於 is_a_j；不能宣稱此 Frixione implementation 自動涵蓋 b。所有候選 numerical cuts 均標 `PROPOSED_NOT_PHYSICALLY_VALIDATED`；未定 mmaa／acceptance／scales／matching 維持 null blockers。不存在 ATLAS fixed-cone equivalence、physical total background、significance 或 CLs 結果。

Phase7I 的 `NOT_BOUND_BY_REVIEWED_CONTRACT` 只描述 exact Route-A b80 的靜態 binding，沒有提升為未執行 runtime 的 PASS。本階段沒有 build、Stage A 或 HumanReview。

## 發布

只發布 source、config proposals 的 identity、tests、bounded receipts、Markdown reports。私有設定原文、PDF grid、binary、events 與未核准 PDF/PNG 都不發布。`scripts/check_publication.py` 檢查 index 和 base 到 HEAD 每一個 outgoing commit payload，包括中間版本；CI 僅 offline source/method regression。Draft PR 不自動 merge。
