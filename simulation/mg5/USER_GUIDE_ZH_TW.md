# 使用者自行產生 MG5 Monte Carlo 樣本

本工具在 Ubuntu WSL 中重用已安裝的 MG5 3.5.16。一般產樣不會重新安裝，
不需要 Codex，不會自動提交或推送任何個人樣本。這是 parton-level LO 研究；
沒有 Pythia8、Delphes 或官方 ATLAS detector simulation。

## 1. 進入目前已安裝的工作目錄

目前這台電腦的 Phase 6A 位於獨立 worktree。從 Windows PowerShell 執行：

```powershell
wsl -d Ubuntu --cd 'C:\HH\.local\phase6a-worktree'
```

以下命令均在這個 Ubuntu terminal、repository 根目錄執行。工作目錄內的
`.local/mg5_installation.json` 已設定實際安裝位置；它包含本機路徑並被 Git 忽略。
先確認命令介面：

```bash
bash simulation/mg5/scripts/generate_sample.sh --help
```

## 2. 開啟互動式 MG5 CLI

```bash
bash simulation/mg5/scripts/mg5_cli.sh
```

在 `MG5_aMC>` 提示符可輸入 `help`、`help generate`、`tutorial`；以 `quit` 離開。
互動式 CLI 是 MG5 原生介面。正式樣本建議使用下列 wrapper，它會保存卡片並
執行獨立檢查。不要在互動模式啟動 shower、detector 或 `install`。

## 3. 一個命令產生有效 bbgg 樣本

```bash
bash simulation/mg5/scripts/generate_sample.sh \
  --process simulation/mg5/cards/bbgg.mg5 \
  --events 100 --seed 20261012 --energy 13000 \
  --output .local/user-samples/my_bbgg_100
```

這會產生真正的 `p p > b b~ a a QCD=2 QED=2` tree-level events。
`--energy` 是總碰撞能量 sqrt(s)，單位 GeV；13000 代表兩束各 6500 GeV。
成功時顯示 `PASS`、實際事件數、積分截面及 compressed SHA-256。
`FAIL` 時保留原始 process、logs 和任何已產生的 events，不刪除失敗事件。
輸出目錄若已存在，程式會拒絕覆寫；重跑時請換新目錄。

| 選項 | 意義與預設 |
|---|---|
| `--process` | 已驗證的 process card，預設 `cards/bbgg.mg5` |
| `--events` | 正整數，預設 1000；支援 100、1000、10000 或自訂數目 |
| `--seed` | 明確整數，範圍 1 到 30081^2，預設 20261013 |
| `--energy` | sqrt(s) in GeV，預設 13000；兩束能量均為此值的一半 |
| `--output` | 新的本機目錄；預設 `.local/user-samples/<profile>_<events>_seed<seed>_<time>` |
| `--run-card` | 可選：完整 run card；未提供則使用實際 MG5 card 加上已記錄研究設定 |
| `--param-card` | 可選：完整 param card；未提供則使用選定模型的實際預設 card |

命令列的事件數、seed 和 energy 優先於 supplied run card 中這三項。
目前 process profiles 均要求 massless hard particles；改質量或模型前必須新增對應
驗證設定。不要只把新的模型名稱填入舊 card。

## 4. 更改事件數、seed 或能量

```bash
bash simulation/mg5/scripts/generate_sample.sh --events 1000 --seed 20261013 \
  --energy 13000 --output .local/user-samples/my_bbgg_1000

bash simulation/mg5/scripts/generate_sample.sh --events 10000 --seed 20261015 \
  --energy 14000 --output .local/user-samples/my_bbgg_10000_14tev

bash simulation/mg5/scripts/generate_sample.sh --events 37 --seed 20261016 \
  --output .local/user-samples/my_bbgg_37
```

10000-event 命令展示支援的選項，**未在本次驗收中實際生成 10000 events**。
事件數增大會增加時間及儲存需求；先以 100 events 檢查設定。固定 seed 不保證
跨版本、compiler、平台或平行排程的 bitwise reproduction。

## 5. 修改 generation cuts、使用自己的 cards

先複製已有的完整實際卡片，保留參考原件：

```bash
mkdir -p .local/my-cards
cp simulation/mg5/cards/smoke_100/run_card.dat .local/my-cards/run_card.dat
cp simulation/mg5/cards/smoke_100/param_card.dat .local/my-cards/param_card.dat
nano .local/my-cards/run_card.dat
```

例如把 `25.0 = pta` 改為 `30.0 = pta`，把 `2.5 = etaa` 改為 `2.4 = etaa`。
其他相關欄位：`ptb`、`etab`、`draa`、`drab`、`drbb`。
維持 `maxjetflavor=4` 才會把 b 分入 b-specific cut 類別；初態五味道仍由
process card 的 proton 定義決定。`ptgmin=0` 代表未使用 smooth-cone isolation。
不要把 pT 或分離 cuts 全部關閉：massless b/photon 的 soft/collinear 區域需要
有限 generation phase space。這些 cuts 不是 reconstructed ATLAS selections。

```bash
bash simulation/mg5/scripts/generate_sample.sh \
  --process simulation/mg5/cards/bbgg.mg5 \
  --events 100 --seed 20261017 --energy 13000 \
  --run-card .local/my-cards/run_card.dat \
  --param-card .local/my-cards/param_card.dat \
  --output .local/user-samples/my_modified_cuts
```

## 6. 找到 LHE、截面與當次真正使用的 cards

成功的 output 目錄包含：

```text
sample.lhe                   解壓後的原始 generator LHE bytes
sample.lhe.gz                deterministic gzip，mtime=0、沒有 filename
run_manifest.json            事件數、截面/積分誤差、權重檢查及 SHA-256
generator_banner.txt         真正產樣 banner
cards/proc_card_mg5.dat       banner 中的實際 process card
cards/run_card.dat           banner 中的實際 run card（含真正套用的 seed）
cards/param_card.dat         banner 中的實際 parameter card
cards/post_run_run_card.dat  MG5 產樣後的工作 card，iseed 可能被重設為 0
cards/me5_configuration.txt  generator settings
process_generation.log      diagrams/output 過程
event_generation.log        integration、unweighting 與 cross-section summary
process/                    完整本機 process/build/原始 events；不要提交到 Git
```

```bash
grep -A4 'Results Summary' .local/user-samples/my_bbgg_100/event_generation.log
python3 -m json.tool .local/user-samples/my_bbgg_100/run_manifest.json
sha256sum .local/user-samples/my_bbgg_100/sample.lhe.gz
gzip -t .local/user-samples/my_bbgg_100/sample.lhe.gz
```

截面單位為 pb，是這組模型/PDF/scales/generation cuts 的 LO 積分估計。
不等於 inclusive ATLAS background normalization。`IDWTUP=-4`、
`event_norm=average` 時 raw XWGTUP 近似截面；histogram normalization 用 XWGTUP/N，
不能直接把 N 個 raw weights 相加當成總截面。

## 7. 獨立驗證新樣本

```bash
python3 -B simulation/mg5/scripts/validate_lhe.py \
  --file .local/user-samples/my_bbgg_100/sample.lhe.gz --events 100 \
  --report .local/user-samples/my_bbgg_100/independent_validation.json
```

驗證器不載入 MG5；逐事件檢查 gzip、XML、cards、粒子、finite values、mass shell、
four-momentum、generation cuts 與權重。不會刪除或修補 event。
要檢查 MG5 原始 gzip（含正常 timestamp）可加 `--generator-original`；公開參考檔
不接受這個 timestamp 例外。diphoton 樣本必須明確加 `--profile diphoton`。

## 8. 換一個已驗證 process，以及安全新增 process

已提供另外的純 diphoton profile，可直接使用：

```bash
bash simulation/mg5/scripts/generate_sample.sh \
  --process simulation/mg5/cards/diphoton.mg5 \
  --events 23 --seed 20261014 --energy 14000 \
  --output .local/user-samples/my_diphoton_23

python3 -B simulation/mg5/scripts/validate_lhe.py \
  --profile diphoton --events 23 \
  --file .local/user-samples/my_diphoton_23/sample.lhe.gz
```

此 profile 是 `p p > a a QCD=0 QED=2` 的 LO tree process，不含 loop-induced gg
contribution。它是獨立 CLI 測試，不取代 bbgg reference。

任意新 physics process 不會被靜默接受。新增時要：

1. 建立獨立 process card，查證 model、coupling orders、初態 flavour、PDF、masses。
2. 在 `generate_sample.py` 的 `PROFILES` 與 `validate_lhe.py` 實作對應 final-state、
   charge/mass/decay/status 與 infrared/cut 檢查；不能只改 process 名稱。
3. 先用少量真正 MG5 events 檢查 diagrams、完整 banner、積分與數值；失敗保留 logs。
4. 通過 physics/profile review 才註冊為可重用的 self-service process。

## 9. 跨 clone 重用此安裝，或重建固定版本

新 clone 可重新註冊**既有**工具，不會安裝：

```bash
python3 simulation/mg5/scripts/configure_local.py \
  --mg5 "$HOME/.local/share/atlas-hh-phase6a/mg5-release-v3.5.16" \
  --toolchain "$HOME/.local/share/atlas-hh-phase6a/toolchain" \
  --conda-sh "$HOME/miniforge3/etc/profile.d/conda.sh"
```

只有另一台 Linux x86_64 電腦需要重建時才使用以下步驟。需要既有 conda；全部位於
新使用者目錄，沒有 sudo、系統安裝或修改 ROOT environment。既存目錄要換新 prefix。

```bash
git clone --depth 1 --branch v3.5.16 https://github.com/mg5amcnlo/mg5amcnlo.git \
  "$HOME/.local/share/atlas-hh-phase6a/mg5-v3.5.16"
git -C "$HOME/.local/share/atlas-hh-phase6a/mg5-v3.5.16" rev-parse HEAD
# 必須等於 3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7

conda create --yes --prefix "$HOME/.local/share/atlas-hh-phase6a/toolchain" \
  --file simulation/mg5/evidence/toolchain-linux-64.explicit.txt

python3 simulation/mg5/scripts/prepare_release.py \
  --checkout "$HOME/.local/share/atlas-hh-phase6a/mg5-v3.5.16" \
  --destination "$HOME/.local/share/atlas-hh-phase6a/mg5-release-v3.5.16"

python3 simulation/mg5/scripts/configure_local.py \
  --mg5 "$HOME/.local/share/atlas-hh-phase6a/mg5-release-v3.5.16" \
  --toolchain "$HOME/.local/share/atlas-hh-phase6a/toolchain" \
  --conda-sh "$HOME/miniforge3/etc/profile.d/conda.sh"
```

本地包裝採用固定 upstream `bin/create_release.py` 的 directory recipe，移除
developer utilities 及重命名 README/compile utility；不改任何 physics source。
Launchpad release endpoint 在本次連線逾時，因此使用官方 Git tag 的 source-only
包裝，沒有冒稱下載了 Launchpad release tarball。

## 10. 只公開選定的 reference

個人 sample 預設在 `.local/`，被 Git 忽略。wrapper 沒有 push 功能。
本次公開範圍只有 `reference_samples/mg5/pp_bbgg_sm_lo_13tev/` 的兩個指定檔。
要更新 reference，先保留舊版本比較，重新產生 100/1000、保留所有 cards/logs，
獨立驗證並更新 manifest/reports；確認 compressed 每檔<=5 MiB、合計<=10 MiB。

```bash
python3 -B simulation/mg5/scripts/validate_lhe.py --repository .
python3 -B -m unittest discover -s simulation/mg5/tests -v
git check-ignore -v reference_samples/mg5/pp_bbgg_sm_lo_13tev/smoke_100.lhe.gz
git check-ignore -v reference_samples/mg5/pp_bbgg_sm_lo_13tev/reference_1000.lhe.gz
```

`git check-ignore -v` 應指出 exact `!` allowlist，而不是泛用 `*.gz` ignore。
僅明確 stage 已核准的樣本、對應 cards、manifest、reports 和 source paths。
禁止 `git add -A`。提交前查看 `git diff --cached --name-status`、`--stat`，
再用 `audit_payload.py --staged`；每次 push 前檢查 `--staged` 與
`--outgoing origin/main`。PDF/PNG 需要使用者對最終 paths、SHA-256、caption/provenance
另行明確核准；測試成功不等於圖像核准。push 後驗證 GitHub tree、遠端檔案 hashes
及實際 Actions 結果，建立獨立 PR；不 force-push，不自動 merge，不改 PR #8。
