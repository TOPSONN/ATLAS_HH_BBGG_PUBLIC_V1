# Phase7E 使用方式

只稽核既有 B/C/D。新物理事件禁止；新積分為 `NOT_AUTHORIZED`。

在 repository 根目錄，沿用既有 WSL／Python／MG5 環境：

```bash
python3 -B -m simulation.hh_signal.integration_audit.validate
python3 -B -m unittest simulation.hh_signal.integration_audit.test_audit -v
python3 -B -m simulation.hh_signal.integration_audit.audit_payload
```

第一個命令獨立求解 αs RGE、重算所有 6000 權重的 ESS／dominant events、比對原 log 數字與全部證據 SHA。程式 PASS 表示正確偵測問題；**C 的 declared/effective PDF gate 仍 FAIL**。舊報告不會改寫。

本機原生只讀交叉驗證（每次用新 output）：

```bash
python3 -B -m simulation.hh_signal.integration_audit.native_checks \
  --output "$HOME/simulations/hh_integration_audit/native_check_user_01"
```

此命令使用原生 αs function 與原 1100 個尺度、原生 card writer；不評估新相空間、PDF、ME 或 integral。它需要保留的 campaign_01 本機原檔與 `.local/mg5_installation.json`，CI 只驗證已綁定的 bounded evidence。沒有重裝工具。

準備獨立積分的卡片／include／manifest：

```bash
bash simulation/hh_signal/integration_audit/prepare_integration_only.sh \
  --output "$HOME/simulations/hh_integration_audit/user_plan_01"
bash simulation/hh_signal/integration_audit/prepare_integration_only.sh \
  --output "$HOME/simulations/hh_integration_audit/user_plan_01" --validate
```

`--seeds`、`--points`、`--iterations`、`--accuracy`、`--max-hours` 可在有界範圍內指定；超出 pilot cost 上限會拒絕。**準備不執行積分**。`--execute` 永遠 exit 2；原生 survey 會寫 scratch candidate，不能僅設 nevents=0 就宣稱零保留。zero-retention runtime guard／integral backend 必須另外審查與授權。

完整限制與收斂設計見 [積分準備計畫](../../../reports/phase7e_integration_only_plan.md)，更正與物理使用限制見 [來源稽核](../../../reports/phase7e_source_identity_audit.md)。本次 source/evidence-only；無 PDF/PNG。
