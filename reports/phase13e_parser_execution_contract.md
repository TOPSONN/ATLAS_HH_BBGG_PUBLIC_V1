# Phase13E：未來 parser 合約與目前禁止派發的原因

本次只完成來源工程、私有 runtime 複製及無害 fixtures。MG5 未啟動，模型未 import，process parser／diagram enumeration 均未執行。結論為 **BLOCKED_PHASE13_RESOURCE_ENFORCEMENT**；目前不具備向使用者請求 parser 啟動核准的完整條件。

## 精確 scope

`metadata/phase13_parser_review_contract.json` 和 `analysis/phase13/source/parser_contract.py` 的 SCHEMA 逐欄相等才有效。未來提案包含三項 semantic commands，接 `quit` 作為安全終止：

```text
import model sm
define p4 = g u u~ d d~ s s~ c c~
generate p4 p4 > b b~ a a QCD=2 QED=2
quit
```

`generate` 在提案中明確包含 symbolic process/diagram enumeration；**不含 code generation**。`QCD=2`、`QED=2` 是 amplitude-order 上界，不是已驗證 diagram set。禁止 numerical ME、`check`、`output`、build、integration、`launch`、events、Pythia、Delphes、Stage A，以及任意 shell／install／save／set 命令。不能把這份提案當 massive 4F cross section 或 physical pilot 的核准。

## 入口與機械 gate

準備工具 `scripts/prepare_parser_package.py` 只讀來源及既有 receipts，產生 `parser_only_approval_package.json`。它列入完整 reviewed source revision、逐檔 source hashes、精確 process/scope、原／隔離 runtime manifest、原始 configuration identity、僅變更 private `mg5_path` 的未啟用提案 identity、model/restriction、fresh output、Python identity、resource evidence 及停止條件。

PDF 依賴分類是 `NOT_REQUIRED_FOR_SYMBOLIC_PARSER`；數值 MG5/LHAPDF binding 為 `UNVERIFIED`。沒有執行 MG5，不得從 standalone Phase12 LHAPDF 結果提升為 MG5 binding PASS。缺少 static `libLHAPDF.a` 是未來數值介面的阻擋，與 symbolic parser 的 scope 分開。

未來介面形狀如下；**本次不得執行正向 parser request**：

```bash
python3 -B analysis/phase13/scripts/run_parser_review.py \
  --package /home/btu/simulations/hh_phase13/run_01/parser_only_approval_package.json \
  --approval /path/to/new_explicit_user_parser_approval.json
```

這是一個可檢查的 blocked command contract，不是已能成功解析的操作承諾。當前 `FULL_LAUNCH_ENVELOPE_IMPLEMENTED=False`，launcher 和 direct child 都硬性停止。即使有人建立 approval JSON／FIFO token，也無法讓目前版本進到 MG5。修正完整資源 envelope 後必須重新評審新 exact source，再另行取得使用者明確授權。

後續若具備完整 containment，提案才允許：精確新授權檔綁定 package SHA256、source revision、scope hash、fresh output，使用者在實際 TTY 輸入 exact challenge，然後再驗 Git/source/runtime/config/dependencies。不能自動產生 human approval，不能使用舊 Phase7I BUILD_ONLY。程式只能檢查檔案與 terminal 字串一致性，不能密碼學上證明人的意圖。child pipe token 只是 parent/child handoff consistency，不是 human authorization 證明。

Git 支援 reviewed source commit 的原始 HEAD，或其後僅三個指定 delivery 檔案改變的報告 HEAD；所有 reviewed source bytes 必須逐檔等於原 commit、tracked worktree/index 必須乾淨。報告變動不代表 executable revision 變動。

## 已實測的 child guard

Linux x86_64、Landlock ABI 3。readonly allow-roots 外不能讀；任何 write-mode open／fork／clone／exec／network 及未列入 allowlist 的 syscall 以 seccomp `KILL_PROCESS` 停止。無任意 executable dispatcher。stdout/stderr 必須是兩個不同、預先開啟的 regular logs。`-B` 與獨立 HOME/TMP/XDG 路徑避免共用 cache/config；任何 MG5 隱含寫入都必須 STOP，不能以成功啟動作預設。

13 項固定無害 fixtures 已實際執行：approved read、原設定 write、copied config write、symlink escape write、fork、exec、network、CPU spin、wall sleep、memory overflow、stdout/stderr overflow，以及 leader 已離開後的 orphan process-group cleanup。原/copy config 前後都是 9302 bytes／e4567fd5…；完整 hashes 見 receipts。

新提案的 child limits 是 CPU 2s、wall watchdog 3s、RLIMIT_AS 512 MiB、每個 log 64 KiB、合計 logs 128 KiB、0 child descendants、0 file creations。RLIMIT_AS 是虛擬位址上限，不是 cgroup RSS 宣稱。CPU 與 polling 有 kernel 粒度：實測 CPU-spin 約 2.02432 CPU s，wall sleep 約 3.00986 wall s。沒有借用未核准的 Phase12 300s envelope。

## 為何完整工作仍阻擋

這些 fixtures 只驗證 **guarded single child**。目前 supervisor 的 Git/preflight/full-tree hashing、configuration activation、parent receipt writing 與最後重掃描，仍沒有完整實作並測試：

- supervisor 自身 CPU hard cap；
- supervisor 自身 RAM hard cap；
- 從 preflight 到 postflight 的 total-wall watchdog；
- parent/preflight/receipt 的 aggregate disk hard bound。

cgroup controller 可見但未委派 writable cgroup；不能據此宣稱 RAM containment。`resource_enforcement_review.json` 明列 `enforcement_verified=true` 的 scope 僅 child，`full_launch_envelope_verified=false`。package 的 `execution_eligible=false`，不能只更改報告文字或 receipt 欄位繞過來源常數。

## 收據與停止

未來 receipt schema 完整記在 JSON 合約中，包含 source/package/approval SHA、runtime before/after、exit/signal/resource stop、wall、log hashes、symbolic completion、零物理生產 counters。任何 source/config/path/approval/limit mismatch、unexpected write/child/network、資源超限、非零 exit 或 postflight drift 都停止。原 copy 的 9302-byte config 保持未啟用；只有另行核准後才可能在 private copy 激活 exact 9305-byte `mg5_path` 提案。原 installed config 永不改寫。

本次物理 counters 全為 0；沒有執行正向 parser。實際 CLI 負例只驗 missing approval 與 direct-child hard block。相關 unit 與 Phase12/11 offline regressions 的最終數量列在 final report。
