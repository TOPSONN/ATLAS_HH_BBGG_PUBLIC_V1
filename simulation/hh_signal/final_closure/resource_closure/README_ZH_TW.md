# Phase7I 完整資源封裝來源提案

本分支從 PR24 的 b80e16775bf141e45f4048c7197a8a99befaed51 建立。使用者授權的是非物理資源修補、無害正反測試與新 stacked Draft PR。沒有正式 BUILD_ONLY、BINARY_REVIEW、PHYSICAL_RESTART 或事件生成授權。

## 目前狀態

實際 systemd resource matrix 尚未執行，RAM profile 的明確審核仍待回覆。不得把離線單元測試、純 BPF 解譯測試或舊 Phase13F 的成功當作本分支完整資源服務實測。`FULL_LAUNCH_ENVELOPE_VERIFIED` 目前為 false。

固定 matrix 有47案：正常流程、六階段各五種超限／終止，以及 aggregate CPU、controller消失、setsid殘留、PID限制、唯讀來源、cgroup改寫、namespace、stdout、tmpfs容量／inode、固定exportFD、缺少人類審核、archive容量、allocation-bypass與單一工作mutex反例。任一案失敗就停止並保留新 workspace，不補做替代案。

## 資源邊界

受限制的 service 包含 Python business imports、完整 Git preflight、來源／toolchain hashing、copy、compiler child、loader、receipt、postflight與archive export。Host的小型啟動／監測控制程式與systemd manager不納入payload CPU／RAM計數，另記錄其wall與固定metadata範圍；不宣稱整個作業系統受限。

- fixture提案：aggregate CPU4s、wall13s、RAM512MiB、swap0、work8MiB、獨立 `/tmp`1MiB、固定host輸出、aggregate data disk16MiB。這些是待審核的無害測試上限。
- 未執行的正式 BUILD_ONLY提案：aggregate CPU／wall各14400s、RAM2GiB、swap0、1job／1worker、CPU affinity一核心、總data disk≤5GiB。work2GiB、獨立 `/tmp`256MiB、32個64MiB archive chunks、固定index與日誌。2GiB work取代初步1GiB設計，原因是舊build用量約1.13GB；原5GiB總上限未提高。
- TasksMax16允許compiler driver與helper；它不是16個物理workers。編譯工作仍逐一執行。
- namespace保持host唯讀，work與 `/tmp`各有tmpfs byte及inode上限。實際mount readback不符合就拒絕。
- inherited syscall filter拒絕fallocate、寫入ioctl、xattr、AIO／io_uring等allocation-bypass。只保留三種唯讀TTY查詢。filter來源與離線解譯成功不等於kernel實測成功。
- `RLIMIT_FSIZE`只限制logical EOF。allocated blocks、filesystem granularity與metadata／extent overhead另作保守核對；無法證明時保持BLOCKED。
- kernel cgroup負責整組memory／swap、CPU rate、全組終止；RuntimeMaxSec提供controller消失後的終止後援。watchdog不是唯一限制。

## 可以執行的離線檢查

在本分支checkout內使用已安裝的Python，不安裝或啟動MG5：

```bash
python3 -B -m unittest -v \
  simulation.hh_signal.final_closure.resource_closure.tests.test_archive_io \
  simulation.hh_signal.final_closure.resource_closure.tests.test_backend \
  simulation.hh_signal.final_closure.resource_closure.tests.test_fixtures \
  simulation.hh_signal.final_closure.resource_closure.tests.test_worker_adapters \
  simulation.hh_signal.final_closure.resource_closure.tests.test_allocation_guard \
  simulation.hh_signal.final_closure.resource_closure.tests.test_publication
python3 -B -m simulation.hh_signal.final_closure.resource_closure.legacy_regression \
  --output /tmp/phase7i-resource-safe-legacy.json
python3 -B -m simulation.hh_signal.final_closure.resource_closure.publication
```

legacy runner使用固定81項清單，不使用full discovery；會阻擋HumanReview建立、MG5／model import與未列入的subprocess。輸出必須全新，不覆寫前次結果。

## 等待RAM明確審核後的無害matrix

以下不是目前已執行的命令，也不授權正式build。必須先完成RAM profile審核、來源獨立審查、commit乾淨checkout，然後由本次已授權的非物理測試範圍執行。output必須全新：

```bash
python3 -B -m simulation.hh_signal.final_closure.resource_closure.run_fixtures \
  --output /home/btu/simulations/hh_phase7i_resource_closure/matrix_01
```

這個CLI只選固定無害case，沒有任意executable參數，不接受正式確認文字。壓力child入口也必須確認目前在正確限制內，才可執行固定負載。不要在shell直接呼叫壓力函式。

## 未來正式BUILD_ONLY入口

舊 `integration_runtime.run prepare-review` 已改為封裝入口。新入口必須另獲exact新revision、output、RAM與完整scope的明確授權；本次不執行。它會傳遞使用者真正foreground controlling TTY的固定descriptor，worker內由使用者親自輸入顯示的challenge。聊天文字、flag、JSON或環境變數不會建立授權。正式build仍需要四個native executable、八個zero-ME preflight、四個entry-denial與完整hash收據。

Host不解開archive。固定chunk/index FD保存bounded strict USTAR及SHA256索引，service內驗證readback；拒絕path traversal、links、special files、tamper、oversize與非有限JSON。失敗時保留固定日誌／checkpoint journal；尚未export完成的volatile compiler scratch不宣稱為完整build archive。

完成build也不能執行物理積分。Archive的獨立binary reader／review與physical execution完整封裝尚未完成遷移；目前physical CLI明確阻擋。需另行來源審查及BINARY_REVIEW／PHYSICAL_RESTART授權。舊build、舊確認與舊截面不重用。

## GitHub與CI

公開內容僅source、tests、固定profile與bounded文字證據。chunks、index、native binaries、私有收據、events、原安裝與PDF／PNG留本機。Publication guard逐一檢查index與每個outgoing commit，包括中間版本。

新分支的歷史closure full-test job明確SKIPPED，因其中有自動建立測試授權物件／native method案例；並非宣告它通過。新CI另跑無害單元測試與固定81項safe legacy。歷史readiness job仍驗證原本固定snapshot。CI成功只能支持離線來源／方法檢查，不能證明本機systemd資源封裝或物理成功。
