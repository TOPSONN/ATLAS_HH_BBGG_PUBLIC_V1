# Delphes 本機操作指南（繁體中文）

這是獨立的 `FAST_SIM_ATLAS_LIKE / NOT_OFFICIAL_ATLAS` 方法研究。以下在
WSL Ubuntu 執行，沿用已驗證的 Delphes 3.5.1、ROOT 6.40.04 / C++20 與
Pythia 8.317 / HepMC3 3.3.1；一般操作不重新安裝。原始 MG5、Pythia 與
歷史分析資料保留。完整控制器已實際完成 Stage A 10 個 bbgg、Stage B
每程序 100 個及 Stage C 每程序 1000 個事件，原生驗證均為 `PASS`；
另一次獨立 PyROOT 讀回核對全部七個工作。Stage C 的獨立硬事件仍為
三程序各 1000，A/B 前段不另加統計。以下 `my_*` 指令是可執行的新工作
範例，實際驗收目錄為 `stage_a_v2_bbgg_10`、`stage_b_程序_100` 及
`stage_c_程序_1000`；首次失敗工作保留本機，沒有取代後續完整執行證據。
另一次實際重複 10 事件工作之科學內容 SHA256 相同、ROOT 二進位 SHA256
不同；它也不增加硬事件統計。完整執行證據在
`simulation/delphes/evidence/native_runs.json`、`independent_readback.json` 與
`reproducibility.json`。三個選定 100 事件參考檔的本機精確複製與 portable
檢查已實際完成；遠端 blob／最終 HEAD CI 仍待發布驗證。

## 1. 進入專案並檢查安裝契約

Windows PowerShell 可先執行 `wsl -d Ubuntu`，以下指令都在 WSL：

```bash
cd /mnt/c/HH
test -f .local/delphes_installation.json
test -f .local/pythia8_installation.json
test -x /home/btu/opt/delphes/bin/DelphesHepMC3
/home/btu/miniforge3/envs/atlas-hh-root/bin/root-config --version
sha256sum simulation/delphes/cards/atlas_like_bbgg_baseline.tcl
```

ROOT 版本應為 `6.40.04`，卡片 SHA256 應為
`cd91fc7982365af23e4002c6295418fbbc0077ffe381e992e7e6070052eb1f47`。
`.local/delphes_installation.json` 是本機契約，記錄來源、可執行檔、函式庫、
字典、標頭與分析器雜湊。啟動器會重新核對這些檔案、實際 ROOT 版本、
C++20、`ldd` 與原生分析器資訊。只改版本字串或替換函式庫不構成驗證。
Delphes 使用官方內附的 Tcl/FastJet；ROOT 使用這個已驗證的環境。

同一台機器可保留現有契約，方便另一份 checkout 使用：

```bash
mkdir -p "$HOME/.config/atlas-hh"
cp .local/delphes_installation.json "$HOME/.config/atlas-hh/delphes_installation.json"
export DELPHES_LOCAL_CONFIG="$HOME/.config/atlas-hh/delphes_installation.json"
```

這不是跨機器安裝程序；契約指向的 Pythia 契約、來源、程式與函式庫仍須
存在且雜湊相符。重新編譯後必須重新完成來源／ABI／原生驗證與安裝登錄，
不可把任意新程式的雜湊填入契約後自行宣告通過。請參考
[環境報告](../../reports/phase6c_environment.md) 的實際來源與建置證據。

## 2. 先做真正的 dry-run

```bash
bash simulation/delphes/scripts/run_delphes.sh \
  --input reference_samples/pythia8/pp_bbgg_sm_lo_ps_13tev/shower_100.hepmc3.gz \
  --process bbgg \
  --card simulation/delphes/cards/atlas_like_bbgg_baseline.tcl \
  --events 10 \
  --output /home/btu/simulations/delphes_runs/my_stage_A \
  --max-hours 1 --max-disk-gb 5 --dry-run
```

`--dry-run` 核對安裝、來源 sidecar、HepMC3 雜湊、事件身分、原始權重、
實際 `ReaderAscii` 與資源；不執行 Delphes、不產生 detector ROOT，暫存
預檢檔案會移除。`detector_events_processed: 0` 是預檢結果，不能解讀成
10 事件模擬成功。`--events 10` 選原始 ASCII 的真實前 10 個事件區塊；
沒有重新序列化或捏造事件。省略此選項則處理已驗證輸入的全部事件。

## 3. 執行 Stage A 與三個 100 事件樣本

確認 dry-run 成功後，以新輸出目錄執行同一指令，移除 `--dry-run`：

```bash
bash simulation/delphes/scripts/run_delphes.sh \
  --input reference_samples/pythia8/pp_bbgg_sm_lo_ps_13tev/shower_100.hepmc3.gz \
  --process bbgg --events 10 \
  --card simulation/delphes/cards/atlas_like_bbgg_baseline.tcl \
  --output /home/btu/simulations/delphes_runs/my_stage_A \
  --max-hours 1 --max-disk-gb 5

bash simulation/delphes/scripts/run_delphes.sh \
  --input reference_samples/pythia8/pp_bbgg_sm_lo_ps_13tev/shower_100.hepmc3.gz \
  --process bbgg --output /home/btu/simulations/delphes_runs/my_bbgg_100 \
  --max-hours 1 --max-disk-gb 5

bash simulation/delphes/scripts/run_delphes.sh \
  --input reference_samples/pythia8/pp_ccgg_sm_lo_ps_13tev/shower_100.hepmc3.gz \
  --process ccgg --output /home/btu/simulations/delphes_runs/my_ccgg_100 \
  --max-hours 1 --max-disk-gb 5

bash simulation/delphes/scripts/run_delphes.sh \
  --input reference_samples/pythia8/pp_jjgg_light_sm_lo_ps_13tev/shower_100.hepmc3.gz \
  --process jjgg_light --output /home/btu/simulations/delphes_runs/my_jjgg_100 \
  --max-hours 1 --max-disk-gb 5
```

`jjgg_light` 是 `jjgg` 的 CLI 別名；manifest 內記錄 `jjgg`。輸出必須是
尚不存在、位於 Git 與安裝目錄之外的資料夾。省略 `--output` 時預設為
`$HOME/simulations/delphes_runs/程序_時間戳`。卡片可省略，預設採用已固定的
研究卡。`--card` 可指向完全相同的副本，不能用任意改寫卡繞過驗證。
種子固定為 bbgg `610301`、ccgg `610302`、jjgg `610303`；原始卡與只改
種子的有效卡都保留雜湊。目前沒有 `--seed` 或 `--resume` 選項。

## 4. 使用完整 1000 事件輸入或新的驗證樣本

現有 1000 事件 Pythia 輸出留在本機，例如：

```bash
bash simulation/delphes/scripts/run_delphes.sh \
  --input /home/btu/simulations/pythia8_runs/bbgg_1k/shower.hepmc3.gz \
  --source-manifest /home/btu/simulations/pythia8_runs/bbgg_1k/run_manifest.json \
  --process bbgg --output /home/btu/simulations/delphes_runs/my_bbgg_1000 \
  --max-hours 1 --max-disk-gb 5 --dry-run
```

預檢通過後移除 `--dry-run`；ccgg、jjgg 分別使用 `ccgg_1k`、`jjgg_1k`
及對應 process。100 與 1000 的前段共用同一批硬事件，不可相加成 1100
個獨立硬事件。小樣本分析的正規化分母仍是原始 MG5 的 1000。

對使用者新產生的樣本，先依
[Pythia 操作指南](../pythia8/USER_GUIDE_ZH_TW.md) 完成相同研究設定的真實
生成與驗證，再把該目錄的 `shower.hepmc3.gz` 和 `run_manifest.json`
傳給上述 `--input`、`--source-manifest`。原始 MG5 LHE、事件 ledger、
particle diagnostics、source events、settings 與原生 HepMC 驗證檔案都須
保留並相符。單獨一個 HepMC 檔案或自行手寫 manifest 不能建立來源身分。
不同物理模型、卡片或未驗證程序需另做來源研究與 gate，不直接加入此基線。

事件上限不得超過輸入事件數。大工作先提供真正完整且驗證過的大輸入，
做 dry-run，確認磁碟、RAM 與時間預算後再分段測試；不能從 1000 個事件
要求 1000000 而宣稱新增統計。此階段沒有實際百萬事件 Delphes benchmark。

## 5. 查看進度、停止與處理失敗

```bash
python3 -m json.tool /home/btu/simulations/delphes_runs/my_bbgg_100/run_manifest.json
tail -f /home/btu/simulations/delphes_runs/my_bbgg_100/delphes.log
touch /home/btu/simulations/delphes_runs/my_bbgg_100/STOP
```

`--max-hours` 包含預檢與各階段，`--max-disk-gb` 是整個工作目錄的 GiB
上限；RAM 在啟動時預檢，磁碟容量／剩餘空間在工作期間定期監測。單一
程序執行，不自動平行增加記憶體需求。Ctrl-C、STOP、逾時、磁碟不足或
驗證失敗會保留實際 partial ROOT、日誌與已知計數，非零返回碼不等於
可用參考樣本。查閱 `status`、`diagnostic` 及六個事件計數；缺失資料為
未知，不能補零當成功。修正問題後使用新的輸出目錄重新完整執行；目前
不接續 partial ROOT，也不覆寫舊結果。

## 6. 找到 ROOT、切流與 b-tag 結果

```bash
ls -lh /home/btu/simulations/delphes_runs/my_bbgg_100/detector.root
sha256sum /home/btu/simulations/delphes_runs/my_bbgg_100/detector.root
python3 -m json.tool /home/btu/simulations/delphes_runs/my_bbgg_100/native_validation.json
cat /home/btu/simulations/delphes_runs/my_bbgg_100/cutflow.csv
cat /home/btu/simulations/delphes_runs/my_bbgg_100/efficiencies.csv
```

成功須同時有原生驗證 `PASS`、N_input=N_read=N_processed=N_output=要求數、
N_invalid=N_skipped=0，且 ROOT、卡片、輸入索引與 truth 索引雜湊一致。
控制器會實際載入 ROOT/Delphes 字典並獨立讀回 TTree/TClonesArray；JSON
數字或檔名本身不是物理驗證。`reco_events.jsonl` 是來源身分與重建科學
內容的稽核資料，不取代原生 ROOT。重新執行後 ROOT UUID／時間等可能
不同；科學內容相符不能稱為 ROOT 二進位逐位元重現。

b-tag 讀 `(Jet.BTag & 1) != 0`，不是 DL1/GN2 分數。效率分母為事件切割前
全部 pT>25 GeV、|eta|<2.5 的重建 jets，依實際 Flavor 分 b/c/light，不能
把程序名直接當每支 jet 的真值。CSV 保留分母、tag 數、預期 tag 數、
Wilson95 區間及低統計旗標。已經隨機 tag 的事件不可再乘 tag 機率。
`cutflow.csv` 同列 raw count 與 signed source-weight sums，這些權重的
分母已保留原始 MG5 事件數，不再乘 sigma/N，也沒有套用 luminosity。
小樣本、shower 重味與候選 constituent overlap 都保留研究限制；這不是
官方 ATLAS b-tag 校正、完整背景預測或 HH 敏感度結果。

實際 Stage C raw cutflow（input → photons → jets → two tags → mgg）為
bbgg `1000 → 446 → 266 → 91 → 28`、ccgg `1000 → 378 → 241 → 7 → 1`、
jjgg `1000 → 445 → 277 → 0 → 0`；jjgg 零通過不代表背景為零。完整
native aggregate 表位於 `metadata/phase6c_efficiencies.csv`。可獨立重算
固定 pT／eta bins 的數值診斷（輸出使用尚不存在的檔名）：

```bash
python3 -B simulation/delphes/scripts/summarize_btags.py \
  --bbgg-run /home/btu/simulations/delphes_runs/stage_c_bbgg_1000 \
  --ccgg-run /home/btu/simulations/delphes_runs/stage_c_ccgg_1000 \
  --jjgg-run /home/btu/simulations/delphes_runs/stage_c_jjgg_1000 \
  --report /home/btu/simulations/delphes_runs/my_btag_bins.json
```

這個工具核對實際 native/reco/ROOT 雜湊及原生 aggregate CSV，只讀已完成
的 C 樣本，不再做 Delphes。診斷邊界為 pT `[25,50,100,200,+∞]` GeV、
|eta| `[0,0.8,1.6,2.5]`；先做嚴格 eligible cut，各 bin 下界包含、上界
不含。低預期 tag 數會明示統計不足；Wilson 區間未包含事件間相關與
systematics。公開數值檔為 `simulation/delphes/evidence/btag_binned_statistics.json`。

## 7. 獨立重新讀回 ROOT

下例沿用已驗證的環境與原生分析器，另建分析輸出目錄，保留原 ROOT：

```bash
python3 - /home/btu/simulations/delphes_runs/my_bbgg_100 \
  /home/btu/simulations/delphes_runs/my_bbgg_100_recheck <<'PY'
import json, os, pathlib, subprocess, sys
sys.path.insert(0, "simulation/delphes/scripts")
import run_delphes
run, out = map(pathlib.Path, sys.argv[1:])
out.mkdir(parents=True, exist_ok=False)
config_path = pathlib.Path(os.environ.get("DELPHES_LOCAL_CONFIG", ".local/delphes_installation.json"))
config = json.loads(config_path.read_text())
env, _, _, _ = run_delphes.verify_installation(config)
manifest = json.loads((run / "run_manifest.json").read_text())
subprocess.run([config["analyzer_path"], "--input", str(run / "detector.root"),
    "--input-index", str(run / "input_event_index.dat"),
    "--truth-index", str(run / "truth_analysis_index.dat"),
    "--events", str(manifest["events_requested"]), "--process", manifest["process"],
    "--card", str(run / "detector_card.tcl"), "--summary", str(out / "native_validation.json"),
    "--events-jsonl", str(out / "reco_events.jsonl"), "--cutflow", str(out / "cutflow.csv"),
    "--efficiencies", str(out / "efficiencies.csv")], env=env, check=True)
PY
```

原生分析器使用獨立 Delphes adapter，沒有修改既有 ATLAS educational
`analysis` tree 讀取器。Truth 匹配、Photon/GenJet/Jet 響應與 HH-like cuts
以各自報告為準；原始 LHE photons 與 shower 後 hard photons 分開診斷。

## 8. 選擇參考檔與發布前檢查

個人工作不會自動 commit、push 或上傳。只有真正執行且驗證過的 100
輸入工作可選為參考；不是從 1000-entry ROOT 人工裁切或改寫出 100：

```bash
python3 -B simulation/delphes/scripts/publish_references.py \
  --bbgg-run /home/btu/simulations/delphes_runs/my_bbgg_100 \
  --ccgg-run /home/btu/simulations/delphes_runs/my_ccgg_100 \
  --jjgg-run /home/btu/simulations/delphes_runs/my_jjgg_100 --dry-run
```

這個 helper 核對原生證據與全部程序後，才允許複製原始 ROOT／卡片／
ledger／索引／CSV 的精確位元組至固定 reference 路徑。每個 ROOT 上限
10 MiB、三個合計30 MiB；精確三個來源 `input_event_index.dat` 因保留全
粒子的 p4／位置／ct，另採各10 MiB、合計30 MiB 上限，其實際大小約
7.1／7.6／7.4 MB。其餘選定證據各5 MiB；已存在的參考檔不覆寫。
移除 `--dry-run` 只在
本地準備選定檔案，不操作 Git。超限則保留原檔並準備具體 draft-release
proposal，沒有建立 release／上傳資產，也沒有啟用 Git LFS。

```bash
python3 -B simulation/delphes/scripts/validate_references.py --repo .
python3 -B simulation/delphes/scripts/audit_payload.py --staged
python3 -B simulation/delphes/scripts/audit_payload.py --outgoing codex/phase6b-pythia8-shower-1k
```

portable 檢查驗證 ROOT magic／SHA、卡片／來源／索引與原生報告的綁定；
不在 GitHub runner 重新安裝或執行 Delphes/ROOT，不能替代第7節原生讀回。
發布須由使用者選定精確檔案，檢查 staged 及每個 outgoing commit；PDF／
PNG 未獲精確最終版本與 caption/provenance 核准不可加入。普通來源 PR
流程不構成圖檔核准。完整 1000 ROOT 預設留本機。遠端 ROOT blob、雜湊
及最終 PR HEAD 的實際 CI 尚未核對時，發布狀態保持 `NOT_EVALUATED`。
