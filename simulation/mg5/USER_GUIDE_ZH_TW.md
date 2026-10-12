# MG5 使用者自行產樣操作手冊

這套命令重用已註冊的 MG5 3.5.16 與獨立 compiler environment，不需要 Codex。
一般產樣保存在 Linux 使用者目錄，不會自動 commit、push 或建立 GitHub Release。
目前是 parton-level LO tree-level 研究，沒有 Pythia8、Delphes 或 ATLAS detector simulation。

本次 V2 執行新 100-event smoke、1000-event reference，另以 100 events、14 TeV
完成最終 CLI 操作測試；全部只用 100/1000 級小樣本，不計入 production target。
下列 10000、100000、1000000 commands 供使用者日後自行啟動，本次沒有執行。
`PRODUCTION_1M_STATUS = NOT_EXECUTED_BY_DESIGN`；大型 Release 發布為 `NOT_EVALUATED`。

## 1. 進入 Ubuntu WSL

在 Windows PowerShell 執行：

```powershell
wsl -d Ubuntu --cd 'C:\HH'
```

以下 commands 全部在 Ubuntu terminal 執行：

```bash
cd /mnt/c/HH
bash simulation/mg5/scripts/generate_sample.sh --help
python3 -B simulation/mg5/scripts/validate_sample.py --help
```

本機 MG5 entry `/home/btu/opt/mg5amcnlo` 指向已驗證的 release-mode installation；
toolchain 在 `~/.local/share/atlas-hh-phase6a/toolchain`。repository 的
`.local/mg5_installation.json` 保存本機設定，被 Git 忽略。ROOT 6.40.04 不需要改動。

## 2. 開啟互動式 MG5

```bash
bash simulation/mg5/scripts/mg5_cli.sh
```

在 `MG5_aMC>` 輸入 `help`、`help generate` 或 `tutorial`；以 `quit` 離開。
wrapper 核對 installation，在 Git 外啟動原生 CLI。任意互動式 process 不會自動
得到本工具的 `PASS`；固定 profile 建議使用下列產樣及驗證命令。

## 3. 一個命令產生 100 events

```bash
bash simulation/mg5/scripts/generate_sample.sh \
  --process pp_bbgg --events 100 --seed 12345 --energy 13000 \
  --output /home/btu/simulations/mg5_runs/my_bbgg_100
```

成功要求 manifest 為 `status: PASS`，實際 events=100。output 已存在時拒絕覆寫；
換新目錄或依第 11 節使用相同 request 的 `--resume`。

| 選項 | 行為 |
|---|---|
| `--process` | `pp_bbgg`、`pp_diphoton`，或內容與已驗證 profile 相符的 process card |
| `--events` | 正整數；100、1000、10000、1000000 或自訂數目 |
| `--seed` | 明確整數，範圍 1 到 30081²；核對 banner 實際 seed |
| `--energy` | 總碰撞能量 sqrt(s)，單位 GeV；13000 表示兩束各 6500 |
| `--output` | Git 外的新目錄；省略時使用 `~/simulations/mg5_runs/` |
| `--run-card` | 完整 run card；命令列 events、seed、energy 優先 |
| `--param-card` | 完整 parameter card；必須符合已驗證 massless model/profile |
| `--jobs` | CPU workers 上限，不得超過可用 CPU |
| `--max-hours` | 每次產樣時間上限；超時保留 partial attempt |
| `--max-disk-gb` | 當次 output 大小上限；超限保留 partial attempt |
| `--dry-run` | 檢查設定、installation 與資源；不產樣、不建立 output |
| `--resume` | 重驗完成樣本，或保存 interrupted attempt 後重新完整產樣 |

已驗證 bbgg process：

```text
import model sm-no_b_mass
define p = g u c d s b u~ c~ d~ s~ b~
generate p p > b b~ a a QCD=2 QED=2
```

這是 continuum αs²αem² tree process；MG5 `QCD=2 QED=2` 是 coupling-order 上限。
不含純 electroweak QED=4、NLO 或 loop-induced contribution。
採 massless b 與五味道 proton/PDF；`maxjetflavor=4` 為 b-specific cut 分類，初態仍是五味道。

## 4. 更改 events、seed、碰撞能量

```bash
bash simulation/mg5/scripts/generate_sample.sh \
  --process pp_bbgg --events 1000 --seed 12346 --energy 13000 \
  --output /home/btu/simulations/mg5_runs/my_bbgg_1000

# 使用者日後自行啟動，本次沒有執行此 10000-event command。
bash simulation/mg5/scripts/generate_sample.sh \
  --process pp_bbgg --events 10000 --seed 12347 --energy 14000 \
  --output /home/btu/simulations/mg5_runs/my_bbgg_10000_14tev
```

換能量須重新積分及產樣，不能直接改舊 LHE header。不同 batches 使用不同 seed；
相同 seed 不保證跨平台、版本或平行排程的 bitwise reproduction。

## 5. 修改 generation cuts 與 cards

```bash
mkdir -p $HOME/simulations/my_mg5_cards
cp simulation/mg5/cards/smoke_100/run_card.dat $HOME/simulations/my_mg5_cards/run_card.dat
cp simulation/mg5/cards/smoke_100/param_card.dat $HOME/simulations/my_mg5_cards/param_card.dat
nano $HOME/simulations/my_mg5_cards/run_card.dat
```

例如將 `25.0 = pta` 改成 `30.0 = pta`，將 `2.5 = etaa` 改成 `2.4 = etaa`。
其他相關欄位：`ptb`、`etab`、`draa`、`drab`、`drbb`。reference cuts 是 photon
pT≥25 GeV、|eta|≤2.5，b pT≥20 GeV、|eta|≤5，各種 ΔR≥0.4。
維持 `maxjetflavor=4`；`ptgmin=0` 表示沒有 smooth-cone isolation。有限 pT/eta/ΔR
cuts 排除 soft/collinear singular regions。generation cuts 與 reconstructed ATLAS
selections 是不同分析步驟。

```bash
bash simulation/mg5/scripts/generate_sample.sh \
  --process pp_bbgg --events 100 --seed 12348 --energy 13000 \
  --run-card $HOME/simulations/my_mg5_cards/run_card.dat \
  --param-card $HOME/simulations/my_mg5_cards/param_card.dat \
  --output /home/btu/simulations/mg5_runs/my_cuts_100
```

新增 masses、PDF 類型、decays 或更換模型時，先擴充對應 physics validation。
不能把舊 profile 當成任意新模型已驗證的依據。

## 6. 找到 LHE、cards 與截面

完成 run 的目錄包含：

```text
sample.lhe                    原始解壓 LHE bytes
sample.lhe.gz                 deterministic gzip，mtime=0
run_manifest.json             狀態、counts、截面/誤差、資源、SHA-256
cards/proc_card_mg5.dat        banner exact process card
cards/run_card.dat             banner actual run card
cards/param_card.dat           banner exact parameter card
attempts/attempt_001/          MG5 process、integration logs 與原始 events
```

```bash
python3 -m json.tool /home/btu/simulations/mg5_runs/my_bbgg_100/run_manifest.json
tail -n 40 /home/btu/simulations/mg5_runs/my_bbgg_100/attempts/attempt_001/event_generation.log
sha256sum /home/btu/simulations/mg5_runs/my_bbgg_100/sample.lhe.gz
gzip -t /home/btu/simulations/mg5_runs/my_bbgg_100/sample.lhe.gz
```

截面單位 pb；誤差為當次 numerical integration 估計，不是完整 model/PDF/scale
uncertainty。reference 採 built-in CTEQ6L1 ID10042、PDF αs(MZ)=0.130，固定
muR=muF1=muF2=125 GeV，`ickkw=0`、`event_norm=average`、`systematics_program=none`。
`IDWTUP=-4` 的正 constant raw XWGTUP 近似截面；histogram 使用 XWGTUP/N，
不能直接把 N 個 raw weights 相加當總截面。MG5 完成後可能將 mutable working card
的 iseed 重設成 0；以已保存的 LHE banner card 判定實際 seed。

## 7. 獨立驗證樣本

```bash
python3 -B simulation/mg5/scripts/validate_sample.py \
  --run /home/btu/simulations/mg5_runs/my_bbgg_100 \
  --report /home/btu/simulations/mg5_runs/my_bbgg_100/independent_validation.json

python3 -B simulation/mg5/scripts/validate_sample.py \
  --file /home/btu/simulations/mg5_runs/my_bbgg_100/sample.lhe.gz \
  --events 100 --profile bbgg --beam-energy 6500
```

`--run` 核對 manifest、source identity 與 exact cards；單獨 `--file` 檢查 LHE，
不能取代完整 provenance。只用 standard library，streaming 檢查每個 event、CRC、
XML、generator/model、finite values、PDG/status、mass shell、four-momentum、cuts、
weights、actual counts 與 SHA-256；失敗拒絕整份，不刪除或修補 events。
本機 input 預設 cap20 GiB、解壓 cap100 GiB，可用 `--max-file-gb` 與
`--max-decompressed-gb` 調整。Git references 另有較小 bounds；大型 validator
支援不表示 1M 已驗收。

## 8. resource preflight

```bash
free -h
df -h "$HOME/simulations"
nproc
bash simulation/mg5/scripts/generate_sample.sh \
  --process pp_bbgg --events 1000000 --seed 12345 --energy 13000 \
  --jobs 2 --max-hours 24 --max-disk-gb 20 \
  --output /home/btu/simulations/mg5_runs/pp_bbgg_1m --dry-run
```

dry-run 不產生 events，顯示 installation、CPU/RAM/free disk、output limits 與 request。
小樣本有 process build/integration 固定成本，不能據此聲稱 1M performance。
未測量的 1M runtime、disk、events/s 保持 `UNKNOWN`。resource limits 是停止門檻，
不是時間/磁碟預測；output 包含中間 grids/build，監測間隔內可能暫時超限，須保留空間。

本次實測 100-event reference command 完成約 12.17 s（8.22 events/s），1000-event
command 約 27.36 s（36.55 events/s），包含 setup、integration、export 與 validation。
兩份 gzip 分別 22449/166712 bytes，完整 output 約 37.23/38.28 MB；這些是小樣本
實測值，不能作為 1M 預測。MG5 installation 約 133.90 MB，toolchain 約 1.25 GB。

## 9. 日後單一完整 1M run

**本次沒有執行下列 command；使用者決定正式產樣時才自行執行。**

```bash
cd /mnt/c/HH
bash simulation/mg5/scripts/generate_sample.sh \
  --process pp_bbgg --events 1000000 --seed 12345 --energy 13000 \
  --jobs 2 --max-hours 24 --max-disk-gb 20 \
  --output /home/btu/simulations/mg5_runs/pp_bbgg_1m
python3 -B simulation/mg5/scripts/validate_sample.py \
  --run /home/btu/simulations/mg5_runs/pp_bbgg_1m
```

要求 `PASS` 且 actual_events=1000000。reference 100/1000 不計入 production target。

## 10. 日後 10 × 100000 獨立完整 batches

先閱讀 plan，不產樣：

```bash
bash simulation/mg5/scripts/generate_batches.sh --action plan \
  --process pp_bbgg --events-per-batch 100000 --batches 10 \
  --seed 12345 --energy 13000 --jobs 2 --max-hours 24 --max-disk-gb 20 \
  --output /home/btu/simulations/mg5_runs/pp_bbgg_1m_batches
```

**以下 `--action run` 本次沒有執行。** 它依序啟動各 batch，使用不同 seed；每份
有自己的 exact cards、LHE、SHA-256、截面與 actual counts。

```bash
bash simulation/mg5/scripts/generate_batches.sh --action run \
  --process pp_bbgg --events-per-batch 100000 --batches 10 \
  --seed 12345 --energy 13000 --jobs 2 --max-hours 24 --max-disk-gb 20 \
  --output /home/btu/simulations/mg5_runs/pp_bbgg_1m_batches
bash simulation/mg5/scripts/generate_batches.sh --action status \
  --output /home/btu/simulations/mg5_runs/pp_bbgg_1m_batches
bash simulation/mg5/scripts/generate_batches.sh --action validate \
  --output /home/btu/simulations/mg5_runs/pp_bbgg_1m_batches
```

不能 `cat *.lhe` 或盲目接合 gzip。保留各批 init/header，逐份驗證後加總 actual
counts，避免重複計入相同 event content。十次同 process 截面是同一物理截面的
獨立估計，不能相加；合併分析需明確定義各批 normalization 與截面估計方式。

## 11. 監看、安全停止與恢復

第二個 WSL terminal 可執行：

```bash
cat /home/btu/simulations/mg5_runs/my_bbgg_100/run_manifest.json
tail -f /home/btu/simulations/mg5_runs/my_bbgg_100/attempts/attempt_001/event_generation.log
du -sh /home/btu/simulations/mg5_runs/my_bbgg_100
```

單一 run 建立 STOP request，等待 wrapper 保存 partial 狀態：

```bash
touch /home/btu/simulations/mg5_runs/pp_bbgg_1m/STOP
cat /home/btu/simulations/mg5_runs/pp_bbgg_1m/run_manifest.json
```

用**相同完整 request** 恢復：

```bash
bash simulation/mg5/scripts/generate_sample.sh \
  --process pp_bbgg --events 1000000 --seed 12345 --energy 13000 \
  --jobs 2 --max-hours 24 --max-disk-gb 20 \
  --output /home/btu/simulations/mg5_runs/pp_bbgg_1m --resume
```

`--resume` 重驗完成 run，或保留 attempt_001，在新 attempt 重新完整產樣；不續接
半份 MG5 integration。partial events 不計入 final count。不能更換 request 或 cards
後聲稱是原 run 的續跑。時間上限適用於新 attempt，disk budget 包含保留的舊 attempts；
若需要提高 limits，保留舊 output 並建立新 output。batch 停止、重驗並只恢復未完成 batches：

```bash
bash simulation/mg5/scripts/generate_batches.sh --action stop \
  --output /home/btu/simulations/mg5_runs/pp_bbgg_1m_batches
bash simulation/mg5/scripts/generate_batches.sh --action resume \
  --process pp_bbgg --events-per-batch 100000 --batches 10 \
  --seed 12345 --energy 13000 --jobs 2 --max-hours 24 --max-disk-gb 20 \
  --output /home/btu/simulations/mg5_runs/pp_bbgg_1m_batches
bash simulation/mg5/scripts/generate_batches.sh --action validate \
  --output /home/btu/simulations/mg5_runs/pp_bbgg_1m_batches
```

final target count 只包含完整 independent validation 通過的 batches，不含 references。

## 12. 已驗證的其他 process 與安全新增 process

```bash
bash simulation/mg5/scripts/generate_sample.sh \
  --process pp_diphoton --events 100 --seed 12349 --energy 13000 \
  --output /home/btu/simulations/mg5_runs/my_diphoton_100
python3 -B simulation/mg5/scripts/validate_sample.py \
  --run /home/btu/simulations/mg5_runs/my_diphoton_100
```

diphoton 是 `p p > a a QCD=0 QED=2` tree process，不含 loop-induced gg；不取代 bbgg。
新 process 先查證 model、orders、flavour、PDF、masses、decays、infrared-finite cuts；
建立新 card，在 generator registry 與 validator 實作 PDG/status/mass/charge/cut
檢查，完成真正小樣本與 physics review 才註冊。未知 card 會拒絕，不能只改標籤。

## 13. 失敗與 partial files

| 狀態 | 處理 |
|---|---|
| output 已存在 | 新 output；相同 request 才使用 resume |
| source hash 不符 | 查明修改/版本原因，不跳過 identity check |
| invalid card/profile | 修正副本，以 dry-run/100 events 檢查 |
| PARTIAL_STOPPED | 保存 STOP 後的 logs；resume 完整重跑 |
| PARTIAL_TIMEOUT | 時間上限；不計入 production count |
| PARTIAL_DISK | output/free disk 門檻；清理自己的無用 files 後重新規劃 |
| FAILED / validation FAIL | 查 logs、CRC/XML/cards/count/physics；不刪 events 來達 PASS |
| Release preflight FAIL | 修正 input/counts/private paths/size；沒有上傳 |
| draft upload 未驗證 | 查看 local receipt 與 GitHub partial draft，不自動覆寫或發布 |

## 14. 只用 Git PR 公開選定 references

只有 `reference_samples/mg5/pp_bbgg_sm_lo_13tev/smoke_100.lhe.gz` 與
`reference_1000.lhe.gz` 在 allowlist。個人大樣本保存在 Git 外。
更新 reference 先保留原件，重新產樣、驗證、同步 manifest/cards/reports：

```bash
python3 -B simulation/mg5/scripts/validate_lhe.py --repository .
python3 -B -m unittest discover -s simulation/mg5/tests -v
git diff --cached --name-status
python3 -B simulation/mg5/scripts/audit_payload.py --staged
python3 -B simulation/mg5/scripts/audit_payload.py --outgoing origin/main
```

只 stage 明確 source/report/card/reference paths，不用 `git add -A`。每次 push 前檢查
staged 與每個 outgoing commit。PDF/PNG 必須先取得使用者對 exact paths、SHA-256、
caption/provenance 的明確 approval；CTest/CI/QA 不代表 approval。不 force-push、
不自動 merge；push 後核對 remote blobs/counts/hash 與實際 Actions 結果。

## 15. 日後選定大型樣本的 GitHub Draft Release

本次只測 preflight/mock，沒有建立或上傳 production Release。需要 completed runs、
已登入 GitHub CLI 與 repository write access。
[GitHub 官方限制](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)：
每 asset **嚴格小於 2 GiB**、每 Release 最多 1000 assets；本工具檢查限制。
不啟用付費 LFS，不上傳 private environment paths、全部 logs、builds 或 MG5 source。

預設為本機 read-only preflight，不需 GitHub authentication，不建立 Release：

```bash
bash simulation/mg5/scripts/publish_release.sh \
  --run /home/btu/simulations/mg5_runs/pp_bbgg_1m \
  --tag mg5-bbgg-1m-v1 --expected-events 1000000 --dry-run
```

batch 模式重複 `--run` 指定每個 completed batch。拒絕重複 event content，核對 actual
total，逐批保留截面。preflight 列出 LHE.GZ、exact cards JSON、sanitized metadata、
release manifest、SHA256SUMS 的 names/sizes/hashes，供使用者審查。

確認後，以下 explicit command 才建立並上傳 **draft**。SOURCE_COMMIT 必須為已推送
GitHub 的完整 40-digit source SHA，不能拿未推送的 local commit 使用。

```bash
gh auth status
SOURCE_COMMIT=$(git rev-parse HEAD)
bash simulation/mg5/scripts/publish_release.sh \
  --run /home/btu/simulations/mg5_runs/pp_bbgg_1m \
  --tag mg5-bbgg-1m-v1 --expected-events 1000000 \
  --target "$SOURCE_COMMIT" --publish
```

全數 remote names/sizes 與下載 SHA-256 通過才回報 `DRAFT_UPLOADED_VERIFIED`。
失敗可能留下 partial draft，保存 local receipt 並回報 failure，不自動 delete/clobber
或 publish。使用者審查 draft 與 scientific provenance 後才自行在 GitHub UI 發布。
依據 [GitHub CLI 官方 draft/create 文件](https://cli.github.com/manual/gh_release_create)。

## 16. 新 clone 重用已安裝工具

只註冊現有 installation，不重新安裝：

```bash
python3 -B simulation/mg5/scripts/configure_local.py \
  --mg5 /home/btu/opt/mg5amcnlo \
  --toolchain "$HOME/.local/share/atlas-hh-phase6a/toolchain" \
  --conda-sh "$HOME/miniforge3/etc/profile.d/conda.sh"
```

固定 official source tag `v3.5.16`、commit `3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7`。
release-mode 採 upstream `bin/create_release.py` packaging recipe，保留 4658 source
files hashes，每次產樣核對，不更改 physics source。其他電腦重建請查 `README.md`
與已保存 toolchain lock/evidence，保留既有 ROOT environment。
