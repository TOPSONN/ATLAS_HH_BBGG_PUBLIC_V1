# 有界原生積分 bridge：新 revision 待核准

2026-10-16 收到的人工授權只綁定 PR24 的 `1f3c5fc4efa141a0e3e6831aa3b44c0e6bd32ee7`，並要求 implementation 改變時先核准新 revision。該版本沒有可執行物理積分的路徑：Python 固定拒絕，native 第一個 ME 前固定 STOP80。本目錄是隔離的修正；**目前沒有執行 genuine ME、survey 或積分**。

舊 F/G STOP80/STOP86、closure CLI、B/C/D、cards、weights、報告及失敗證據都不修改。本 bridge 的原生 computational bodies 不移除 candidate/write/store/clear、RNG、grid、停止或誤差估計；只有入口／I/O 邊界、唯讀觀測及明示失敗 gate。

## 審查與操作

在既有 WSL Ubuntu、repo root 使用已安裝的工具，不重裝：

```bash
python3 -B -m simulation.hh_signal.final_closure.integration_runtime.run verify-build \
  --output "$HOME/simulations/hh_final_closure/authorized_bridge_review_05"
python3 -B -m simulation.hh_signal.final_closure.integration_runtime.published
python3 -B -m unittest simulation.hh_signal.final_closure.integration_runtime.test_runtime -v
```

如需另做無 ME 建置審查，使用不存在的目錄：

```bash
python3 -B -m simulation.hh_signal.final_closure.integration_runtime.run prepare-review \
  --output "$HOME/simulations/hh_final_closure/my_bridge_review_01"
```

這會編譯四份真正 native binary，但只執行每份 adaptation／measurement 的 pre-ME input/config exits，以及沒有 supervisor capability 時的 exit80。`init_good_hel` 的原始 body 已檢查為無 ME 初始化；probe 在 mapping、phase-space sampling、ME 前離開。不同建置若有不同 binary hash，不會被本次已凍結的 executable receipt 默認接受。

**以下是取得包含新完整 SHA 的獨立人工核准後，才可執行的命令。現在不得執行。**

```bash
python3 -B -m simulation.hh_signal.final_closure.integration_runtime.run execute-reviewed \
  --output "$HOME/simulations/hh_final_closure/authorized_bridge_review_05" \
  --reviewed-revision APPROVED_40_HEX_SHA
```

`--reviewed-revision` 只核對乾淨 checkout 的 identity；不是授權 token。操作人／Codex 必須先在可信對話確認該 exact revision 確已獲准。環境變數、editable JSON、文件或此範例都不構成人工核准。程式另核對已提交 source、公開凍結 build identity、所有 executable／immutable source／shared library hashes；native 入口要求不可修改、匿名的 supervisor memfd，這只證明受監控，不證明人類授權。

## 固定的科學設定

Physics contract SHA256 固定為 `a8a093e2ec47283dd9cb503b2c83fe95b89df4761df5fb7afc623fa291c937cb`。CTEQ6L1、αs(MZ)=0.130／one-loop、13TeV、finite mt/mb、κλ=κt=1、μR=μF=mHH/2。原模型／參數卡／native libraries 逐一綁定。

新 input 明示 `multichannel=0`、exact helicity sum0、configuration1。舊準備的 multichannel1 會走 native `AMP2(SUBDIAG)/sum(AMP2)` 分支；這可能是 MG 合法分割的一部分，不能僅憑 flag 宣稱歷史 B/C 錯誤，更不能重縮放它們。新目標明確使用完整 coherent amplitude，須和新 revision 一起審查。

Adaptation：250 initial nonzero target、固定4輪、accuracy0、grid mode2、moffset0。
Measurement：250 initial target、固定3輪、accuracy0、grid mode0、moffset1。
原生每輪 point target 加倍；不假設每輪只有250個嘗試。每個 replica 都從無 grid 開始；measurement 僅接受同 seed adaptation 的 exact ftn26 SHA，複製為自己的 ftn25。八組 RANMAR base/offset/ij/kl 需與原公式一致且不碰撞。

## 監控與停止

只允許 910001、910019、910037、910061，依序執行，無 seed／events／workers／budget override。seed910001 adaptation 的真正 Stage A 必須通過才可前進；第一個 replica 完成後以實測成本、1.5倍保守倍率檢查剩餘三個的預算。失敗不換 seed、不重開 campaign、不自動 resume。

CPU 與 wall 共用整個 physical invocation 的各4h上限，保留提前停止餘裕；計入 controller CPU、已結束 children 及 active native CPU。review/build資源另列，磁碟仍一併計入。所有 physical children 只有一個 affinity CPU、禁止 fork、thread limit1、2GiB address-space sublimit、32 FD、64MiB/file、禁止 core dump。退出／例外／超限都清理整個 process group；kernel parent-death SIGKILL防止supervisor意外死亡留下native orphan，另有實際非物理回歸。

Linux Landlock ABI3以上在 native exec 前套用：source、模型與 library 不可寫；只能寫三個已存在的數值 output inode，以及私有 scratch 目錄。沒有為 physical sample filename 提供可寫路徑。三個 output 是 results.dat、ftn26、grid_information；先建立空 results.dat 會走原 driver 的 EOF/default twgt 分支，不是匯入舊積分。原 MadLoopParams 已是 WriteOutFilters=false、HelicityFilterLevel0，不另改數值或 cache 模型。

匿名 scratch 仍使用經7H測試的 Fortran formatted write/read/rewind 與 descriptor lease。會有 transient bytes，也可能短暫有 libgfortran 建立後立即 unlink 的名稱；不宣稱無 transient writes。監控 `/proc/PID/fd` 的 unlinked regular inode／size，重複 FD 不重複計算，最多9個 inode 的保守 envelope；另含 supervisor memfd。

磁碟計入本輪所有 authorized_bridge_review_* workspace（包含失敗建置）及64MiB source/Git預留；2GiB即保守停止，對人類5GiB上限保留3GiB餘裕。這是 kernel write envelope、per-file/FD 限制加 polling watchdog，**不是 filesystem quota 或零延遲證明**；polling與暫存名稱觀測有時間解析度限制。真正 runtime 的完整行為仍須 Stage A 驗證。

原始 stdout/stderr 只在記憶體 hash 後丟棄，避免 MadLoop 警告打印的四向量被保留。只保存有界 HI_/H_IO scalar protocol、STOP／Fortran runtime error。每個 outer ME entry/return 即時觀察，但只保留最新 counter；完整 per-iteration 值、return-code histogram、tail 診斷及 endpoint 留在 JSON。internal reduction/rescue subcalls 不冒稱獨立 ME entries。

逐點檢查真實 MU_R、q2fact、G 與 gluon densities；不為驗證額外呼叫 RNG、ME、scale setter 或 alpha_s routine。NaN、無法核對的 seed、錯 PDF/αs/scales、exceptional loop failure／pole警告、非零 exit、writer／output／resource gate failure 立即停止。保留 partial receipt，不能把不完整 stage 稱 COMPLETE。

## 輸出與科學限制

每個 stage 保留數值 protocol、native error、iteration history、candidate/tail counters、own-grid hashes、raw-stream hashes、資源與 zero-retention postcondition。native anonymous unweight count 不等於 retained source events；不得發佈 scratch records、physical LHE、Pythia／Delphes output。

四個完成後才計算 mean、sample SD、SE=SD/2 與 Student-t(3)95%區間；其獨立性／近似常態假設需明示。native internal errors 分列，不和 between-run dispersion 盲加。沒有已核准的 calibrated precision/coverage criterion，本版本即使完成也保守標示 INCONCLUSIVE_CONVERGENCE，不自動判定收斂成功或加跑。修正 SM1000、Pythia／Delphes 均不在此次授權內。
