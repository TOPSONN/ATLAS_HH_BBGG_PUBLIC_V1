# 重味來源鑑識與新背景準備：繁體中文操作指南

本階段只讀既有事件、做來源鑑識與數值診斷，並以已安裝 MG5 解析候選
process cards。沒有新增 bbγj、ttH 或 ZH 事件；沒有重做 shower／detector
tagging、改寫 source997、移除罕見事件或把三份 pilot 合成官方背景。
full LHE／HepMC／ROOT 留在原位置。公開證據為小型 derived JSON／CSV。

在 PowerShell 輸入 `wsl -d Ubuntu`，以下指令在 WSL 執行：

```bash
cd /mnt/c/HH
python3 --version
```

## 1. 重查 source997 的原始身分及圖譜

需要既有已驗證 ROOT6.40.04、Delphes3.5.1 字典與完整本機 Phase6B／6C
資料。工具依 `.local/delphes_installation.json` 找到已驗證的完整 jjgg
來源；不需要重裝 generator，也不需要重新啟用 conda shell：

```bash
python3 -B simulation/heavy_flavour_forensics/scripts/source997.py \
  --output "$HOME/simulations/heavy_flavour_forensics/source997_check_01"
```

輸出 `source997.json` 及本機 readback log。使用新的輸出目錄，保留每次
檢查版本。來源編號997 是 one-based；對應原始 LHE 第997個 event block、
ROOT entry996／Event.Number997。工具核對 LHE／ledger／HepMC／ROOT／
Phase6D pilot 的實際 hash、權重、四向量／關係，並在讀取前後確認原檔
byte hashes 未變。只靠 `Jet.Flavor=5` 不足以判定 g→bb；需要真實
Pythia／HepMC parent/daughter 圖。原 native flavour 不可被診斷標籤覆寫。

這個 read-only CLI 已實際通過既有 source997 驗證；它不是新的物理事件。
`HARD_PROCESS_FLAVOUR`、`SHOWER_PARTON_FLAVOUR`、`HEAVY_HADRON_FLAVOUR`
與 `DELPHES_ASSOCIATED_FLAVOUR` 必須分開讀，無法唯一判定的 origin 留 UNKNOWN。

## 2. 重算保留全部事件的 influence 診斷

```bash
python3 -B simulation/heavy_flavour_forensics/scripts/influence.py \
  --pilot-dir simulation/rare_backgrounds/evidence/pilot \
  --output "$HOME/simulations/heavy_flavour_forensics/influence_check_01"
python3 -m json.tool "$HOME/simulations/heavy_flavour_forensics/influence_check_01/influence.json"
```

各程序仍使用全部1000 source events、原權重及原分母。leading tagged-pair
的 bb／bc／b-light／cc／c-light／light-light 分解，與事件是否含≥2個
native-b tags 的分解是不同 partition，不可相加或互換。它們是固定
reconstruction 下的條件式期望，不是新 tag 抽樣或校正效率。

source997 的 leave-one-out／剩餘999個事件、top5／top10、concentration
與 variance 是診斷。全部事件的結果仍為 authoritative；不能把刪除
source997 當修正後物理預測，也不能把 concentration 或重複tag計算
宣稱新增 independent hard statistics。罕見的 native-b mixture 不代表
light-jjgg 是純 light-mistag 樣本；重味來源須另看鑑識證據。

## 3. 只解析新的 process cards

```bash
python3 -B simulation/heavy_flavour_forensics/scripts/parse_process_cards.py \
  --output "$HOME/simulations/heavy_flavour_forensics/process_parse_01"
python3 -m json.tool "$HOME/simulations/heavy_flavour_forensics/process_parse_01/process_parse_receipt.json"
```

這個指令只接受已審查的 import／define／generate，會在記憶體建立
tree diagrams、記錄真實 coupling orders，禁止 `output`／`launch`／
model merge／install／width calculation。已實際執行六項檢查：三張
canonical production cards、Z→bb、單一 e+ charge 的 top/W 衰變鏈，以及
普通 SM H→γγ 無 tree diagrams 的預期拒絕。結果是 `PASS_PARSE_ONLY`，
事件數0，截面 UNKNOWN；不等於 physical simulation PASS。

候選卡是：

- `simulation/mg5/cards/bb_gamma_j_candidate.mg5`：一個 Born photon，
  extra `j4` 包含 charm、不含 bottom；不是校正好的兩光子 fake 背景。
- `simulation/mg5/cards/tth_candidate.mg5`：MG5 保留穩定 t／tbar／H。
- `simulation/mg5/cards/zh_candidate.mg5`：tree qqbar ZH，MG5 保留穩定 Z／H；
  不包含 loop-induced ggZH 或 NLO/EW precision normalization。

這些不加入舊 `generate_sample.py` 的 validated profiles；舊 self-service
generator 拒絕候選卡是正確行為。不能偽裝成 bbgg／ccgg／jjgg profile。

## 4. Higgs 衰變與 BR 帳本

普通 SM tree model 沒有 HAA vertex。`hgg_plugin` 有 effective HAA，但
不是完整獨立 SM；本階段未 merge／import 此模型或計算 H→γγ width。
versioned `config/higgs_decay_contract_v1.json` 保留兩個待驗證選項：
stable-H production 後由 Pythia 強制γγ，或另審 effective-model chain。
任何 adopted partial／total width、physical BR 與 external-LHE forced
decay weight closure 目前均 UNKNOWN／NOT_EXECUTED。

不能因 `25:onMode=off`、`25:onIfMatch=22 22` 可解析，就假定所有輸出
權重已含正確 physical BR。未衰變 production σ 要乘缺少的 BR 一次；
若實際 integrated exclusive chain σ 已含該 decay，不得再乘。
ttH 的 top／W channels、tau、CKM、spin／width 及一個 charge 或兩個
charge union 均須明示。純數值 `higgs_contract.py` 拒絕 UNKNOWN、重複
BR、truthy字串驗證旗標及不一致的 exclusive W fractions；synthetic
unit tests 不提供物理 BR 或 closure 證據。

## 5. 未來100-event pilot 指令：本階段禁止執行

使用者本任務第8節明確要求新 bbγj／ttH／ZH production 必須另有
**separate explicit pilot authorization**。以下為準備好的 executable
production-only 範例，沒有在 Phase6E 執行。取得特定程序的100-event
pilot 授權並完成 param／run-card、scale／cut／PDF 與資源審查後，才可
執行最後的 `timeout ... mg5_cli.sh`。它不生成 Higgs diphoton decay。

先選一個 candidate；將第一行改為 `tth` 或 `zh` 可建立相應 proposal：

```bash
candidate=bb_gamma_j
case "$candidate" in
  bb_gamma_j) seed=20261101 ;;
  tth) seed=20261102 ;;
  zh) seed=20261103 ;;
  *) echo "Unknown candidate" >&2; exit 2 ;;
esac
proposal_dir="$HOME/simulations/mg5_proposals/phase6e_${candidate}_100"
process_dir="$HOME/simulations/mg5_runs/phase6e_${candidate}_pilot100"
test ! -e "$proposal_dir" && test ! -e "$process_dir" || exit 2
mkdir -p "$proposal_dir"
{
  cat "simulation/mg5/cards/${candidate}_candidate.mg5"
  printf '\noutput %s -nojpeg\nlaunch %s -m --name=pilot100\n' "$process_dir" "$process_dir"
  cat <<EOF
shower=OFF
detector=OFF
analysis=OFF
madspin=OFF
reweight=OFF
done
set nevents 100
set iseed $seed
set ebeam1 6500
set ebeam2 6500
set pdlabel cteq6l1
set lhaid 10042
EOF
  if [ "$candidate" = bb_gamma_j ]; then
    cat <<EOF
set ptj 20
set ptb 20
set pta 25
set etaj 5
set etab 5
set etaa 2.5
set drjj 0.4
set drbb 0.4
set drbj 0.4
set draj 0.4
set drab 0.4
set maxjetflavor 4
set ptgmin 0
EOF
  fi
  printf 'done\nquit\n'
} > "$proposal_dir/pilot100.mg5"

# RUN ONLY AFTER SEPARATE EXPLICIT PILOT AUTHORIZATION AND CARD/RESOURCE REVIEW
timeout --signal=TERM --kill-after=30s 2h \
  bash simulation/mg5/scripts/mg5_cli.sh "$proposal_dir/pilot100.mg5" \
  > "$proposal_dir/pilot100.local.log" 2>&1
```

2h 是範例行政上限，不是實測 runtime estimate。ttH／ZH 的 scale／cuts
不得把 continuum125 GeV 當已驗證選擇；上例保留 MG5 新 output 的 defaults，
必須事前審查並在實際 run 中保存 effective cards。各新程序 runtime／RAM／
disk 的估計為 `INCONCLUSIVE_100_EVENT_RESOURCE_ESTIMATE`；既有三組
1000-event 實測及各自範圍列於 [資源評估](../../reports/phase6e_new_process_cards.md)。
它們不能直接除以十預測新程序。應先批准本機 budget、監測和停止
方案，再做100-event pilot，不能直接外推10000／100000／1000000 events。

預期 LHE 位置是 `process_dir/Events/pilot100/unweighted_events.lhe.gz`，
但只有實際生成與檢查後才能確認。未來需記錄完整 event count／init
截面／原始 signed weights／SHA256／cards，並建立適用的新 process／
decay validation，才能標記 physical PASS。舊兩個 Born photons 的
validator 不適用於一光子或 stable-H，不得繞過它宣稱通過。
timeout／failed／partial files 留本機，不當作正式樣本或自動推 GitHub。

## 6. 回歸、公開與科學限制

```bash
python3 -B -m unittest discover -s simulation/heavy_flavour_forensics/tests -v
```

解析六項檢查與 source997 physical readback／數值測試／GitHub 最終 HEAD
CI 是不同證據。閱讀三份準備報告：
[process cards](../../reports/phase6e_new_process_cards.md)、
[Higgs contract](../../reports/phase6e_higgs_decay_contract.md)、
[overlap](../../reports/phase6e_background_overlap.md)。Born 名稱不同不證明
shower 後 physical final states 互斥，SCALUP 也不是 matching／merging。
沒有校正過的 photon fake transfer，不填入假機率、不發明 stitching weights。

個人檢查結果留本機；只有選定且驗證的小型 source／config／derived
evidence／reports 發布。full original physical files 不複製進 Git，
generator source 不 vendoring，不 merge PR／force-push。未核准的 PDF／PNG
保留本機，tests 或 visual QA 不能代替精確版本／caption 的使用者核准。
本階段不宣稱 OFFICIAL_ATLAS_BACKGROUND、CALIBRATED_BTAGGING、
PHYSICAL_PHOTON_FAKE_RATE 或 HH_SIGNAL_SENSITIVITY。
