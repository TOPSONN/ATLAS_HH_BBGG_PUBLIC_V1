# Phase12A：runtime configuration 漂移與新基線提案

實測目前檔案為 **9302 bytes**，原始 SHA256 為 `e4567fd50d47a317407eb10cca76387053cdf06631949773296314702f77dca1`。三個不同 PID 的循序唯讀觀察一致；這只支持觀察區間內的穩定，沒有辨識歷史 writer，也沒有通過舊 Phase11 原始 byte gate。

`RUNTIME_SNAPSHOT_STATUS=THREE_SEQUENTIAL_SNAPSHOTS_STABLE_WITH_LIMITS`。
`RUNTIME_WRITER_IDENTIFIED=NO`；`ACTUAL_WRITER=UNKNOWN`。
`PROPOSED_BASELINE=phase12-proposed-runtime-v1`；`NEW_BASELINE_APPROVED=NO`。
舊 gate 保持 `BLOCKED_EXTERNAL_RUNTIME_CONFIGURATION_DRIFT`。

## 1. 實際觀察與檔案身分

目標為 `/home/btu/opt/mg5amcnlo/input/mg5_configuration.txt`，解析後為 `/home/btu/.local/share/atlas-hh-phase6a/mg5-release-v3.5.16/input/mg5_configuration.txt`。

| 觀察 | Linux PID | UTC 開始時間 | bytes | raw SHA256 |
|---|---:|---|---:|---|
| 1 | 129230 | 2026-10-19 09:37:28.868331 | 9302 | `e4567fd5…f77dca1` |
| 2 | 129231 | 2026-10-19 09:37:28.924130 | 9302 | `e4567fd5…f77dca1` |
| 3 | 129232 | 2026-10-19 09:37:28.975678 | 9302 | `e4567fd5…f77dca1` |

控制程序 PID=129229；三次觀察於 09:37:28.976165 UTC 結束，涵蓋約 0.108 秒。整個 CLI 工作的記錄 walltime 為 2.019 秒，包含獨立字串差異與 serializer 重現；它不是三次 snapshot 各自耗時。

證據來自本工作 Python 子程序以 `O_RDONLY`／`O_NOFOLLOW` 開啟已確認的解析路徑、讀取 bytes，再以同一 descriptor 的前後 fstat 及路徑身分檢查比對。不是推測、舊 screenshot 或 cache 命中率測試。檔案及 filesystem 觀測如下。

| 項目 | 三次共同觀測值 |
|---|---|
| filesystem | ext4，mount source `/dev/sdd`，mount point `/` |
| filesystem ID | 4468005691283509779 |
| device | 2096，major:minor = 8:48 |
| inode | 243763 |
| mode／uid／gid／links | 0644／1000／1000／1 |
| mtime_ns | 1792401400044969536 |
| ctime_ns | 1792401400044969536 |
| atime_ns | 1792401401468967382 |

三次 snapshot 中，device、inode、length、mtime、ctime、解析路徑與 raw SHA 相同；每次 descriptor 的前後 metadata 也相同。完整 ns 與 filesystem 記錄在 `runtime_raw_snapshots.json` 及 [runtime identity metadata](../metadata/phase12_runtime_identity.json)。

這些程序共享同一主機與檔案快取，沒有執行 cold-cache reset，也不能稱為獨立 cold-cache 實驗。約 0.108 秒內沒有觀測到變動，不證明更早、之後或其他工作期間沒有寫入。

## 2. 舊 A／B／C 與目前值的 exact diff

| 歷史 identity | bytes | SHA256 | 與目前長度差 |
|---|---:|---|---:|
| A | 9212 | `83d48923f215d20565931e8e0eb6ee986b34658d0bbe6f2e7a75e0400b4d7f85` | +90 |
| B | 9239 | `9132f5ddcab8eb45ee00830d3ed9b7582bda67058180288d3f93222a96f74506` | +63 |
| C | 9266 | `82a6d1943d0acd139704910dfd0510ee2bd86d06f94a410b5f28e68a45bc3f5a` | +36 |

A／B／C 的舊 bytes 不是本次從過去時間讀回的檔案。程式在記憶體中逆推有限的 padding 候選，僅在完整 bytes 的長度和 SHA256 同時精確符合已知 identity 時接受，並清楚標成 `EXACT_KNOWN_HASH_RECONSTRUCTION_NOT_A_LIVE_OR_BACKUP_READ`。它們不可冒稱原始備份。

三份重建與目前 bytes 的每份 raw diff 都有 3 個改動區段，僅涉及 `fortran_compiler`、`cpp_compiler`、`auto_update` 行的註解尾端空格與後續空白行。changed bytes 都是 whitespace；所有有效 key/value 比較為相同，changed setting count=0。完整有效設定的 canonical SHA256 為 `63ffabb654213dac4909bb3c9b6d64780976629620a83970f06c17658b927004`。

公開的非敏感 allowlist 值為：fortran compiler=`x86_64-conda-linux-gnu-gfortran`、C++ compiler=`x86_64-conda-linux-gnu-g++`、auto_update=`0`。另一個 active setting 的完整值只留在本機 private semantic copy；完整設定身分仍由上述 canonical hash 與原始 SHA 綁定。沒有用這些設定推導任何新的 PDF、alpha_s、cuts 或物理預設值。

**語意相同不等於原始 bytes 相同**。本次沒有 normalization、回復安裝檔、改寫舊收據或用 semantic SHA 取代舊 raw SHA。因此 A02／Phase11 的 exact-source 失敗依舊保留。

## 3. Serializer 行為可以重現；writer 仍未知

唯讀檢查的 MG5 來源為 `madgraph/interface/extended_cmd.py`，129870 bytes、SHA256 `6a4f1616ffd7910850e6776ae3f922965a757a7dee9130990e0a579b3ad70c56`。第 2006 行逐行讀取 basefile，第 2018 行保留 `#` 後的 comment，第 2040 行重新組字串，第 2055 行是該 serializer 的 writer open。此處只讀原始碼，沒有 import 或執行 MG5。

獨立的字串運算在記憶體重現該 formatting 規則：對三個設定各作一輪，總長度增加 9 bytes。以精確重建 A 為起點，第 3 輪得到 B、第 6 輪得到 C、第 10 輪得到本次 9302-byte 值；每一步都比對完整 raw SHA。

因此結果為 `SERIALIZER_BEHAVIOR_REPRODUCED`。這證明已知 transformation 可逐 byte 重現差異，不證明某個特定歷史程序、測試或人實際呼叫了它。可用的 23 份已授權 Phase11 task execution receipts 只提供任務執行身分及結果，沒有直接 filesystem write attribution；本次沒有用時間接近或 transformation 相符來猜測 writer。

`runtime_writer_attribution.json` 保留 `ACTUAL_WRITER=UNKNOWN`。沒有讀取 shell histories、credentials、無關程序，也沒有掛 tracing。這項 source audit 與實際 snapshot 的證據類別分開保存。

## 4. Versioned baseline 只是一份未核准提案

新 ext4 Phase12 review workspace 下，保留了 `phase12-proposed-runtime-v1` 的獨立 private byte copy。它的 SHA256 與三次觀察相同；來源是本次已讀取並驗證的 snapshot，而非修改安裝檔後冒充新基線。

本機位置：`/home/btu/simulations/hh_phase12/run_01/runtime_01/private/phase12-proposed-runtime-v1.raw.txt`。本機另保留三份 snapshot raw copy、A／B／C 的標記重建、完整 semantic settings 與 full diff。這些 bytes 不會進入 GitHub；公開輸出限 hashes、metadata、差異範圍與分類。

`runtime_baseline_proposal.json` 同時記錄舊 A／B／C、新 identity、提案理由、可公開有效設定、UNKNOWN writer 以及獨立審查要求。基線核准為 false，physical authorization 為 false，dispatcher 為 null。新提案不得改成「舊 Phase11 gate 已 PASS」。

在後續獨立審查之前，必須核對新 private copy 的完整 SHA、現有 external dependency closure、精確新來源 revision 與使用範圍。任何 parser、Route-A build、積分或事件生產仍需要另外的 exact-source 授權。

## 5. 實作、測試與驗收限制

實際命令：

```bash
python3 -B analysis/phase12/scripts/audit_runtime.py \
  --output-dir /home/btu/simulations/hh_phase12/run_01/runtime_01
```

輸出位置必須全新；不得以這個命令覆寫本次資料夾。controller 固定啟動三個循序 Python snapshot workers，每個 timeout 為 30 秒，單次 configuration read 上限 65536 bytes。輸出限新 Phase12 結果根目錄，安裝位置及其 write guard 不可經 policy 靜默改成可寫。

26 個合成／method fixtures 已通過：exact raw 與 semantic 分離、whitespace drift、duplicate keys、已存在檔案保留、path containment、installed-write guard、尺寸上限、解析路徑、distinct PID、inode 改變、未授權 dispatcher／baseline approval，以及 serializer 逆推／正推。這些 fixtures 使用 temporary synthetic configuration，不能取代上面已實際執行的三個 installed-file observations。

本項新增 MG5 process、ME、integral、hard event、Pythia event、Delphes event 全部為 0；沒有執行 Phase7I，也沒有把自動測試當成外部人類審查。Phase7I 是否受此檔案影響，僅由 Phase12B 的精確 dependency contract 另行判定。