# Route A 正式 build 操作說明

本次只啟用 source。**尚未批准或執行正式 build、真正 HH ME、積分、Stage A 或事件產生。**
目前使用已審查的 `HH_ROUTE_A_GUARD_BUILD_REVIEW_V1`；物理條件仍為 MG5 3.5.16
`loop_sm` 的 `g g > h h [noborn=QCD]`、完整有限 mt/mb LO、13 TeV、CTEQ6L1、
alpha_s(MZ)=0.130 一圈、native muR=muF=mHH/2、model MU_R reference=91.188 GeV。
此修正不能套用到其他 model 或 NLO。

## 先取得獨立 BUILD_ONLY 批准

交付報告的 `NEW_ACTIVATED_SOURCE_REVISION` 是唯一候選。使用者須另行明確批准這個完整
40 字元 SHA 的 BUILD_ONLY 工作。這份文件、任何 JSON、環境變數、CLI 參數都不是批准。
舊的單次物理批准已消耗，不能重用。

以下命令**僅供將來已取得批准後**，由使用者在有 controlling terminal 的 Ubuntu/WSL
終端機操作。本次沒有執行。先在 repository 目錄的 Windows Terminal 開啟：

```powershell
wsl -d Ubuntu -u btu --cd .
```

在 Ubuntu 執行唯讀核對；將完整 SHA 設為交付報告中的值：

```bash
export PYTHONDONTWRITEBYTECODE=1
REV=$(git rev-parse HEAD)
git status --short --untracked-files=no
printf '%s\n' "$REV"
python3 -B -c 'from simulation.hh_signal.final_closure.integration_runtime.contract import check_revision,git; print(check_revision(git("rev-parse","HEAD"),full=True)["git_preflight"]["status"])'
```

確認 REV 與使用者批准的 SHA 完全相同，所有 tracked 檔案乾淨。不能自動改成其他 HEAD。
Git precheck 只做核對，沒有 build 或積分。

## 將來取得批准後的正式 build

選一個從未使用過的 output。既有目錄即拒絕，失敗後保留原目錄，不自動重試：

```bash
OUT="$HOME/simulations/hh_final_closure/route_a_build_01"
test ! -e "$OUT"
python3 -B -m simulation.hh_signal.final_closure.integration_runtime.run prepare-review \
  --output "$OUT" --reviewed-revision "$REV"
```

程式會在 `/dev/tty` 顯示完整 BUILD_ONLY scope，包括 revision、output、source identity、
四個 seeds 和資源上限。只有在外部明確批准後，使用者才可親自輸入畫面上的
`APPROVE BUILD_ONLY <scope SHA256>`。請勿 pipe、自動回答或代寫批准檔案。
這只是操作者與程式間的邊界，不能防禦能任意執行 Python 或修改帳號內程式的攻擊者。

正式 build 只允許四個新 binary 的編譯／連結、八個零 ME configuration preflight、
四個未受監督入口拒絕測試。保留實際 PID、時間、CPU、source、toolchain、dynamic library
及完整 immutable inventory。不執行 mapping、survey、真正 ME 或事件產生。
只有 `HH_PREFLIGHT_ONLY=1` 的受限初始化與預期 exit80 的入口拒絕可啟動新 binary。
所有 child sequential、單 core，監控 aggregate wall/CPU/disk，失敗即停。

## 唯讀驗證與兩種 identity

```bash
python3 -B -m simulation.hh_signal.final_closure.integration_runtime.run verify-build \
  --output "$OUT" --reviewed-revision "$REV"
```

此命令讀取 `review_build.json`、四個 `replica_<seed>/build.json`、實際檔案、依賴及
preflight postcondition，不重新執行 binary。結果只代表 file/protocol checks；尚需獨立
人工 binary review。收據自稱通過或自稱 human approved 都不能代替該審查。

- `FULL_BUILD_RECEIPT_IDENTITY`：完整 JSON 的 canonical SHA256，保留所有真實時間、PID、
  preflight、resource measurements。它不是 JSON 檔案原始 bytes 的 SHA256；原始檔也應保留。
- `IMMUTABLE_BINARY_SOURCE_IDENTITY`：精確 source revision、physics、source/card/toolchain、
  compile plan、四個實際 executable、immutable inventory 及 dynamic dependencies 的 identity。
  準備時間不同不會被誤判為 binary 改變；binary identity 相同也不能替代完整收據。

新 binary 尚未編譯，因此本次沒有任何新的 production executable SHA256。
synthetic receipt 測試通過只屬方法驗證，不能稱為實際 build 通過。

## 歷史資料稽核

歷史收據只允許獨立稽核，不會取得 Route A 執行資格：

```bash
python3 -B -m simulation.hh_signal.final_closure.integration_runtime.run audit-historical \
  --output "$HOME/simulations/hh_final_closure/restart_feasibility_58d39888_01"
python3 -B -m simulation.hh_signal.final_closure.integration_runtime.published
```

PID460 原始失敗收據與舊 binary 不得修改。舊 STOP92 實際分支仍為 UNKNOWN。

## 物理重啟仍須另行批准

完成 build 後先提供完整收據、四個實際 executable hashes、library identities、preflight
與兩個 identity 供獨立審查。未取得新 binary review 及**另一份**明確物理重啟批准前，
不能使用 `execute-reviewed`。BUILD_ONLY 確認不能當作 BINARY_REVIEW 或 PHYSICAL_RESTART。
未批准時不要呼叫任何會要求物理確認的命令，也不要直接啟動 binary。

將來批准的物理 envelope 仍固定 seeds 910001/910019/910037/910061、aggregate wall/CPU
各14400秒、1 job/1 worker、額外 disk 5 GiB、0 retained physical LHE。只可先做 seed910001
Stage A；任何科學、輸出或資源 gate 失敗立即停止，不換 seed、不延長、不重試。
完成一次工作不代表建立收斂或精度；correctedSM1000、Pythia、Delphes 仍未授權。
