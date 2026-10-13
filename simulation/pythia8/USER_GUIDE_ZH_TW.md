# Pythia8 自助 shower／hadronization 操作手冊

這個工具將已有的 MG5 LHE 交給真正的 Pythia8，再寫出 HepMC3，保存事件身份、
signed weights 與 provenance，並作獨立驗證。個人產樣不會自動推送 GitHub。
本次只處理既有 bbgg、ccgg、light-jjgg，各1000 inputs；沒有重新產生 MG5 events，
沒有 detector simulation、matching/merging 或1M processing。

## 1. 進入 WSL 並重用安裝

PowerShell：

```powershell
wsl -d Ubuntu --cd 'C:\HH'
```

Ubuntu terminal：

```bash
cd /mnt/c/HH
bash simulation/pythia8/scripts/shower_sample.sh --help
python3 -B simulation/pythia8/scripts/validate_hepmc3.py --help
```

本機 preferred prefix 是 `/home/btu/opt/pythia8/`，runs 放在
`/home/btu/simulations/pythia8_runs/`。installation 註冊與 full outputs 都不入 Git。
一般 command 不重新安裝，不修改現有 ROOT 或 MG5 installation。

保留現有`.local/pythia8_installation.json`：其中記錄已驗證的source commits、XML、
headers與libraries signatures，以及實際runner/validator paths。它是local registration，
不是Git中的physics sample。可使用既有verified backup的位置：

```bash
export PYTHIA8_LOCAL_CONFIG="$PWD/.local/pythia8_installation.json"
```

要在同一WSL machine的fresh checkout重用安裝，可先把這份已驗證registration
複製到Git外並指定它（`cp -n`保留已存在的backup）：

```bash
mkdir -p "$HOME/.config/atlas-hh-phase6b"
cp -n .local/pythia8_installation.json "$HOME/.config/atlas-hh-phase6b/existing_verified_installation.json"
export PYTHIA8_LOCAL_CONFIG="$HOME/.config/atlas-hh-phase6b/existing_verified_installation.json"
```

這份registration保留同一machine的resolved paths/signatures，不宣稱能直接跨machine。

需要重建本專案runner時，重用已驗證的isolated prefixes，另用新build directory：

```bash
cmake -S simulation/pythia8 \
  -B "$HOME/.local/share/atlas-hh-phase6b/build/runner-user" \
  -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON \
  -DPYTHIA8_ROOT="$HOME/opt/pythia8" -DHEPMC3_ROOT="$HOME/opt/hepmc3"
cmake --build "$HOME/.local/share/atlas-hh-phase6b/build/runner-user" --parallel 2
ctest --test-dir "$HOME/.local/share/atlas-hh-phase6b/build/runner-user" --output-on-failure
"$HOME/.local/share/atlas-hh-phase6b/build/runner-user/shower_lhef" --build-info
```

這只重建本project C++ targets，沒有重新安裝ROOT/MG5/Pythia或處理shower events。
新registration可從已驗證的existing contract複製，只更新這兩個built-binary paths；
保留所有已驗證source/header/XML/library signatures，不重新「信任」任意現有libraries：

```bash
python3 - <<'PY'
from pathlib import Path
import json, os
source = Path(os.environ.get('PYTHIA8_LOCAL_CONFIG', '.local/pythia8_installation.json'))
record = json.loads(source.read_text())
assert record['pythia_source_commit'] == '83a5c9986f30746cfb390435a9b10ac55a758fca'
assert record['hepmc3_source_commit'] == 'beb66aa1a2ac263066becdee26d18ead83edec95'
build = Path.home() / '.local/share/atlas-hh-phase6b/build/runner-user'
record['runner_path'] = str(build / 'shower_lhef')
record['validator_path'] = str(build / 'validate_hepmc3')
target = Path.home() / '.config/atlas-hh-phase6b/pythia8_verified_registration.json'
target.parent.mkdir(parents=True, exist_ok=True)
with target.open('x') as stream:
    json.dump(record, stream, indent=2)
    stream.write('\n')
PY
export PYTHIA8_LOCAL_CONFIG="$HOME/.config/atlas-hh-phase6b/pythia8_verified_registration.json"
```

CLI會再次核對signatures、實際versions/C++20及loaded libraries，並保存當次binary hashes。
若原verified registration遺失或libraries已改變，先從正式pinned source/build證據重新
建立可信registration；不可只計算任意files的SHA256並把它們標為verified。來源與本次
實際build條件見[environment report](../../reports/phase6b_environment.md)。

## 2. 一個命令處理 bbgg1000

```bash
bash simulation/pythia8/scripts/shower_sample.sh \
  --input reference_samples/mg5/pp_bbgg_sm_lo_13tev/reference_1000.lhe.gz \
  --process bbgg --events 1000 --seed 610201 \
  --output /home/btu/simulations/pythia8_runs/bbgg_1k \
  --settings simulation/pythia8/config/baseline_shower.cmnd \
  --jobs 1 --max-hours 1 --max-disk-gb 5
```

output 必須是新的本機目錄；已存在時換名稱。成功以完整 counters、ReaderAscii 與
independent validation 判定。Pythia 發生拒絕/錯誤時會保留原始 source event 身份；
不會生成 replacement LHE，不能把999寫成1000。

| 選項 | 意義 |
|---|---|
| `--input` | 原始 LHE/LHE.GZ；先驗證 hash、CRC、counts 與硬過程內容 |
| `--process` | `bbgg`、`ccgg`、`jjgg`；必須與 LHE 相符 |
| `--events` | 要處理的 input prefix 數量，不得超過完整 input count |
| `--seed` | Pythia seed1至900000000，明確記錄真正生效值 |
| `--output` | Git 外的新目錄；拒絕 accidental overwrite |
| `--settings` | 指定與已審查 baseline hash 相同的 `.cmnd` card；保存 exact card 與全部 effective defaults |
| `--jobs` | 本 baseline 單一 deterministic stream 使用1；不宣稱多執行緒 bitwise 一致 |
| `--max-hours` | 有界 processing 時間上限 |
| `--max-disk-gb` | 有界 output 空間上限；包含 records 與 sidecars |
| `--dry-run` | 驗證設定/input/resources，完全不處理 physics events |

## 3. 10／100-event input prefix 與三個 processes

```bash
bash simulation/pythia8/scripts/shower_sample.sh \
  --input reference_samples/mg5/pp_bbgg_sm_lo_13tev/reference_1000.lhe.gz \
  --process bbgg --events 10 --seed 610201 \
  --output "$HOME/simulations/pythia8_runs/my_bbgg_10" \
  --jobs 1 --max-hours 1 --max-disk-gb 5

bash simulation/pythia8/scripts/shower_sample.sh \
  --input reference_samples/mg5/pp_ccgg_sm_lo_13tev/reference_1000.lhe.gz \
  --process ccgg --events 100 --seed 610202 \
  --output "$HOME/simulations/pythia8_runs/my_ccgg_100" \
  --jobs 1 --max-hours 1 --max-disk-gb 5

bash simulation/pythia8/scripts/shower_sample.sh \
  --input reference_samples/mg5/pp_jjgg_light_sm_lo_13tev/reference_1000.lhe.gz \
  --process jjgg --events 1000 --seed 610203 \
  --output "$HOME/simulations/pythia8_runs/my_jjgg_1k" \
  --jobs 1 --max-hours 1 --max-disk-gb 5
```

10/100-event outputs 使用原1000-input的 prefix。相同 LHE 重做不同 shower seed
仍共享相同硬事件，不是獨立 MG5 statistics。bbgg、ccgg、jjgg 截面分開保存，不能
混成一個 input stream 或使用共同 sigma。

## 4. dry-run 與 resources

```bash
bash simulation/pythia8/scripts/shower_sample.sh \
  --input reference_samples/mg5/pp_bbgg_sm_lo_13tev/reference_1000.lhe.gz \
  --process bbgg --events 1000 --seed 610201 \
  --output "$HOME/simulations/pythia8_runs/my_bbgg_preflight" \
  --jobs 1 --max-hours 1 --max-disk-gb 5 --dry-run
free -h
df -h "$HOME/simulations/pythia8_runs"
```

dry-run 不寫 physics events。時間、disk、RAM 與實際 throughput 以當次記錄為準；
未測量的 production estimate 必須保持 UNKNOWN。資源門檻不是 performance 保證。
full HepMC ASCII、gzip、ledger、diagnostics 同時保存會佔用額外空間。

本次三個完整1000-run均實際PASS：bbgg/ccgg/jjgg CLI elapsed約14.21/16.99/15.95秒，
完整run directories為250644633/273911296/275587484 bytes；它們包含大量raw diagnostics。
這不是1M benchmark。假設相似events及相同sidecars線性延伸，單個1M run約250–276GB
（decimal）只是規劃估計；phase未執行1M。需額外headroom及當次disk/time監控。

## 5. 查看 output、counters 與事件 ledger

```bash
python3 -m json.tool /home/btu/simulations/pythia8_runs/bbgg_1k/run_manifest.json
python3 -m json.tool /home/btu/simulations/pythia8_runs/bbgg_1k/run_summary.json
head -n 2 /home/btu/simulations/pythia8_runs/bbgg_1k/event_ledger.jsonl
sha256sum /home/btu/simulations/pythia8_runs/bbgg_1k/shower.hepmc3.gz
gzip -t /home/btu/simulations/pythia8_runs/bbgg_1k/shower.hepmc3.gz
```

主要輸出：`shower.hepmc3`／`shower.hepmc3.gz`、`event_ledger.jsonl`、
`source_events.jsonl`、`particle_diagnostics.jsonl`、`run_summary.json`、`run_manifest.json`。
ledger 明確記 source sample/hash、LHE index/hash、attempt、run/seed、status、output
index/hash 與 weights；不能只憑輸出順序推定一對一。
確認 N_input、N_attempted、N_shower_success、N_shower_failed、N_written、N_readback、
N_failed_validation。正常1000-run需要1000 fully valid outputs；partial保持partial。

## 6. settings 與物理限制

`baseline_shower.cmnd` 用 simple pT-ordered showers。ISR/FSR、Lund fragmentation、
applicable short-lived decays ON；MPI、pileup、colour reconnection OFF。
v2保留官方primordial kT模型ON：initiator hard Gaussian width為1.8GeV，remnant為
0.4GeV，並由stock mass/rapidity damping及recoil compensation處理。這是非微擾
beam-remnant模型，不是MPI、ATLAS UE tune或對既有events的數值修補。
從 Monash parameters 開始後改用 CTEQ6L1、αs(MZ)=0.130／one-loop／CMWoff；
這是修改過的 isolated baseline，沒有 full Monash 或 ATLAS tune calibration 宣稱。

v1的額外`primordialKT=off`設定在真正bbgg100-run的event54造成嚴格mass-shell
驗證失敗；原始card保存在`config/diagnostic_collinear_disabled.cmnd`，明確為
**NOT_APPROVED_FOR_REFERENCE**，正常CLI不接受。v2 canonical card的SHA256為
`53ab239a091b179abce8db5d6905a279884c47a0286a422c059265460ec33389`。
這次改變會影響recoil／分布／亂數序列，因此A/B/C全部用新card重跑；QA容差不變，
只有真正run與independent validation通過才可稱為PASS。

frameType4 從原 LHE 讀取2212 beams 與6500+6500 GeV。兩個pTmaxMatch=1尊重
SCALUP125 GeV；這只是 scale convention，沒有 ME/PS matching，可能留下較硬
radiation coverage gaps。既有 MG5 massless c/b hard records保留；shower masses為
1.5/4.8 GeV。完整 effective settings／particle data需一起檢查。

cτ>10mm particles按本 truth convention穩定（source使用strict greater-than）；
b/c applicable decays仍執行。
QED photon radiation與有限 hadron-level QED ON，γ→fermion conversion在此direct-photon
baseline明確OFF，排除該貢獻。並不是為了讓QA通過而修改events。
hadron decays與shower會增加photons、重味道hadrons；hard-process b/c/light flavours
不能直接變成每個後續 b/c-hadron 的來源標籤。ambiguity 保留 UNKNOWN/AMBIGUOUS。

目前`--settings`接受原baseline或其byte-for-byte副本，可改檔案位置；任意修改設定
會被hash gate拒絕。新的physics card須另立版本、審查並更新相應validation，再用
10/100-event prefix實測後完整處理；本版沒有宣稱任意custom設定已驗收。
不能只改manifest／HepMC vectors讓舊輸出通過。

## 7. weights 與截面

MG5策略-4、event_norm=average，此批原始 XWGTUP≈各process sigma[pb]。
Pythia nominal weight也為pb；sigmaGen/sigmaErr API為mb，需要1mb=10⁹pb。
官方converter把cross section轉成pb，但不同API讀值仍需用實際ledger核對。
第一個output weight是`input_contribution_pb`，已等於LHE_XWGTUP/原N；其餘named
columns保留raw LHE／Pythia／converter的pb provenance，不能把多個columns當variation
或互相加總。不得再乘一次MG5 sigma或把第一個weight再除一次N。

單事件 contribution 的原始分母是完整 input N（此處1000），並需account failures。
100-event prefix/公開subset不代表完整截面，更不能把weights重新除100後當新獨立樣本。
若有rejections，輸出count不能直接代替原N來強制恢復sigma；先評估bias與失敗原因。
三種cross sections不相加為完整ATLASbackground。沒有detector/tagging/fake-rate/yield宣稱。

## 8. 獨立驗證與 ReaderAscii

驗證自己的 bbgg1000 output（以下 source hash 是本庫固定 input 的 SHA256）：

```bash
python3 -B simulation/pythia8/scripts/validate_hepmc3.py \
  --file /home/btu/simulations/pythia8_runs/bbgg_1k/shower.hepmc3.gz \
  --events 1000 \
  --ledger /home/btu/simulations/pythia8_runs/bbgg_1k/event_ledger.jsonl \
  --source-file reference_samples/mg5/pp_bbgg_sm_lo_13tev/reference_1000.lhe.gz \
  --source-sha256 bc8f0c4a48a1db512013552afe3ec8091dddaae8b47daf7aae808d7cb767a343 \
  --sample-id bbgg --seed 610201 \
  --report /home/btu/simulations/pythia8_runs/bbgg_1k/user_validation.json
```

換成自己真正使用的 output、input、sample id、seed 及 input SHA256。
這個命令是可攜 Python integrity check；當次 CLI 另會呼叫真正的 C++ ReaderAscii，
其結果保存在 `physical_validation.json`，必須確認 exact file hash 與 counters。
驗證已選定公開 references 與既有 MG5 library：

```bash
python3 -B simulation/pythia8/scripts/validate_hepmc3.py --repository .
python3 -B -m unittest discover -s simulation/pythia8/tests -v
python3 -B simulation/mg5/scripts/validate_lhe.py --background-library .
python3 -B -m unittest discover -s simulation/mg5/tests -v
```

公開驗證器檢查gzip/text structure、events、units、particle/vertex links、weights、ledger
與source/settings hashes。真正HepMC3 ReaderAscii已納入local C++ physical validation；
Python text parsing不能單獨證明library compatibility。global momentum只用physical
incoming beams與stable final state，不能把所有intermediate particles一起相加。

## 9. 安全停止及 partial results

查看當次logs、status與disk usage；要停止可建立STOP request或對foreground wrapper
按Ctrl+C，等待process-group停止並保存partial counters。實際方式以`--help`為準。

```bash
touch /home/btu/simulations/pythia8_runs/bbgg_1k/STOP
du -sh /home/btu/simulations/pythia8_runs/bbgg_1k
```

本版沒有宣稱從partial Pythia event stream續接的resume功能。保留舊output，用新目錄
完整重跑；sharedhardinputs仍不是新增MG5statistics。不得隱藏失敗events或重新產生replacement。

## 10. 日後1M input的操作範本

**本次沒有執行1M processing，也不能用現有1000-input要求讀1M。** 使用者必須先
擁有一份獨立驗證的1M LHE，保存其generator provenance、cards/counts/sigma/hash，
再自行用同一CLI處理。下面路徑是使用者將來的input，不是假造的既有檔案：

```bash
bash simulation/pythia8/scripts/shower_sample.sh \
  --input "$HOME/simulations/mg5_runs/pp_bbgg_1m/sample.lhe.gz" \
  --process bbgg --events 1000000 --seed 610201 \
  --output "$HOME/simulations/pythia8_runs/pp_bbgg_1m" \
  --settings simulation/pythia8/config/baseline_shower.cmnd \
  --jobs 1 --max-hours 24 --max-disk-gb 375 --dry-run
```

確認dry-run／完整provenance與資源後，使用者自行移除`--dry-run`才真正執行。
單一stream的runtime/disk上限由使用者依實測規劃；本次不提供未驗證的1Mthroughput保證。
375GiB是有headroom的使用者budget範例，不是必須佔用量或成功保證。上述重建與將來1M
範本沒有在本次重新執行；正常1000 self-service command已由actual stages完整測試。

## 11. GitHub只公開選定實際outputs

每個process至少公開`shower_100.hepmc3.gz`，從真正驗證的1000-run取前100records，
保留原event number／ASCII bytes及對應ledger；它們是subset、不是獨立物理樣本。
若full1000gzip≤10MiB/份，且full合計≤30MiB，也可公開full版本。
其餘保留local hashes/sizes與`simulation/pythia8/evidence/large_output_release_proposal.json`，
列出真正full assets、event counts、hashes及size，供使用者審查Draft Release方案；
沒有建立或uploadRelease，也不使用GitLFS。

只在三個完整1000-run全部PASS後，可明確執行下列local publication helper。
`--dry-run`先生成temporary candidates並驗證，不改public files；移除該選項才寫出
選定references/evidence。已存在public artifacts會拒絕overwrite。

```bash
python3 -B simulation/pythia8/scripts/publish_shower_references.py \
  --bbgg-run /home/btu/simulations/pythia8_runs/bbgg_1k \
  --ccgg-run /home/btu/simulations/pythia8_runs/ccgg_1k \
  --jjgg-run /home/btu/simulations/pythia8_runs/jjgg_1k --dry-run
```

每個process的完整1000-event ledger也以原始JSONL bytes保存於evidence，讓CI核對
selected lines是該full run的exact members。full HepMC未公開時，Python只驗證此
mapping/provenance；真正full-file library readback的依據仍是有exact hash的C++report。

publication helper不做Git。明確stage cards/source/reports/manifests與exact selected
references；先檢查以下audit，再逐個outgoingcommit核對，不用`git add -A`：

```bash
python3 -B simulation/pythia8/scripts/audit_shower.py --staged
python3 -B simulation/pythia8/scripts/audit_shower.py --outgoing origin/codex/phase6a-backgrounds-1k
```

PDF/PNG仍須使用者核准exact paths、SHA256、captions/provenance；tests不代表approval。
push後驗證remote blobs與finalPRhead真正GitHubActions結果，NO_CHECKS不是PASS。
保持stackedDraftPR，不force-push、不自動merge，不修改既有MG5references。

## 12. Delphes留待下一階段

已查閱官方DelphesHepMC3 source的ASCII E/U/W/A/V/P讀法、GEV/MM與status1處理，
尚未安裝或執行Delphes，不能稱為detector compatibility runtime test。
三個full outputs實測最長ASCII lines為159/166/215bytes，低於被檢查reader的16384-byte
line buffer；這只是格式前提的source檢查，仍不替代Delphes runtime test。
未來需另行驗證reader/card/ROOTbuild、detector response及normalization；本階段truth
hadrons不是calibratedATLASjets，沒有b-tag/mistag/trigger/resolution模型。

物理依據與使用限制請見[README.md](README.md)中的Pythia官方manual、weight、PDF、
decay與Delphessource連結；Pythia引用遵循[8.3物理/使用手冊](https://arxiv.org/abs/2203.11601)
與release附帶license／MCnet guidelines。
