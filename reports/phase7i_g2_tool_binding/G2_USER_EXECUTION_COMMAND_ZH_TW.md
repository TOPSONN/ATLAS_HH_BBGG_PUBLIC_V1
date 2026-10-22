# 單次Ubuntu操作方案（等待獨立批准，現在不可執行）

三個expected binary hashes已由使用者回報填入；完整diagnostic的installed version、dependency closure、bus及private parent仍BLOCKED。此文件不是授權。沒有產生human reference。

## 最小下一個版本query

真正child argv固定為：

```text
/usr/bin/systemctl --version
```

這行不是可略過wrapper的建議：必須使用本PR已審tool_binding_version_probe，先驗exact source、三個ELF hash、UID/GID、Python3.12.3及私有parent，pin ELF FD後以原5s/1s wrapper執行。獨立批准後的entry point：

```bash
/usr/bin/python3 -I -B -c 'import sys;sys.path.insert(0,sys.argv[1]);from simulation.hh_signal.final_closure.master.tool_binding_version_probe import main;raise SystemExit(main(["--scope",sys.argv[2]]))' "$REVIEWED_EXACT_SOURCE" "$INDEPENDENTLY_APPROVED_VERSION_SCOPE"
```

兩個變數目前不是已核准值；本機另有完整exact-path命令與pending scope，authorization_reference=null，因此原樣執行會在任何live read之前BLOCKED。scope外部批准與source hash須另核，不能手填任意hash假裝人類授權。原/usr/bin/timeout不執行。

## 原三條完整diagnostic

保留PR44固定argv/env，entry point為同樣exact source中的diagnostic_capture --scope。候選pending scope已在本機exclusive保存，UID/GID與三個tool digest及原四source digest固定；authorization_reference=null、execution_authorized=false。installed family、依賴閉合、sockets及private parent核實之前，不提供會跳過這些門檻的批准方案。

```bash
/usr/bin/python3 -I -B -c 'import sys;sys.path.insert(0,sys.argv[1]);from simulation.hh_signal.final_closure.master.diagnostic_capture import main;raise SystemExit(main(["--scope",sys.argv[2]]))' "$REVIEWED_EXACT_SOURCE" "$INDEPENDENTLY_APPROVED_DIAGNOSTIC_SCOPE"
```

這是等待資料與獨立批准的精確entry contract，不是execution-ready命令。原三條argv見G2_FIXED_ARGV_ENV_COMPARISON.json；真tool/source values見G2_ACTUAL_TOOL_BINDING.json。執行前必須保留此exact source revision `55777dd8a21964dd87c7294550bd51cef73e5fa8`；任何來源/輸入變更用fresh run。
