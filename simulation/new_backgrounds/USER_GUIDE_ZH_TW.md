# B04／B05／B06：本機 1000-event 全鏈操作

本工具重用 WSL Ubuntu 已安裝的 MG5 3.5.16、Pythia 8.317、HepMC3 3.3.1、
Delphes 3.5.1、ROOT 6.40.04／C++20。不需重新安裝。
舊 Phase6F 100-event readiness CLI 保持原樣；這裡使用獨立 controller。

## 執行一個新樣本

輸出目錄必須尚不存在。下列命令會進行真正的物理生成，請先確認所需
磁碟與記憶體；每次只執行一個 process。個人輸出留本機，不自動提交 Git。

```bash
cd /mnt/c/HH
bash simulation/new_backgrounds/scripts/run_background.sh \
  --process zh --events 1000 --seed 20261104 --energy 13000 \
  --output "$HOME/simulations/phase6g_runs/zh_personal_1k_01" \
  --max-hours 4 --max-disk-gb 10
```

另外兩個 process 使用相同工具：

```bash
bash simulation/new_backgrounds/scripts/run_background.sh \
  --process tth --events 1000 --seed 20261105 --energy 13000 \
  --output "$HOME/simulations/phase6g_runs/tth_personal_1k_01" \
  --max-hours 4 --max-disk-gb 10

bash simulation/new_backgrounds/scripts/run_background.sh \
  --process bbgj --events 1000 --seed 20261106 --energy 13000 \
  --output "$HOME/simulations/phase6g_runs/bbgj_personal_1k_01" \
  --max-hours 4 --max-disk-gb 10
```

目前只接受上述三種 process、1000 source events、總碰撞能量13000GeV。
`--seed` 是 MG5 seed，可在1..900000000更改；Pythia seeds固定為
610401/610402/610403，Delphes為610501/610502/610503，實際值寫入manifest。
不同程式的相同 seed 不代表相同物理亂數串流。
時間與磁碟上限不得超過4小時／10GiB；較小正值可以提早停止。
不提供未驗證的stage／事件數／能量選項，也不自動增加統計。

只想檢查設定時，在同一命令加上 `--dry-run` 並指定另一個新目錄。
它只寫文字卡片／計畫，不呼叫integration、Pythia.next或Delphes。
例如：

```bash
bash simulation/new_backgrounds/scripts/run_background.sh \
  --process bbgj --events 1000 --seed 20261106 --energy 13000 \
  --output "$HOME/simulations/phase6g_runs/plans/bbgj_user_dry_01" \
  --max-hours 4 --max-disk-gb 10 --dry-run
```

## 全鏈順序與輸出

每次只有一次 MG5 source integration/unweighting，目標1000原始events。
Pythia先檢查同一來源前10、前100筆，再處理全部1000。
Delphes的10／100前綴取自已驗證的full1000 shower；它們不是新硬事件。
任何物理 validity gate失敗會停止依賴步驟，不以新事件補足目標。

|內容|相對於本次run的路徑|
|---|---|
|實際設定／來源與seed|`execution_plan.json`、`authorization.json`|
|原始完整MG5 LHE.GZ及banner|`mg5/process/Events/zh1000/`、`tth1000/`或`bbgj1000/`|
|完整實際process/run/param cards|`mg5/inputs/`、`mg5/process/Cards/`|
|實際amplitude／coupling檢查|`mg5/amplitude_validation.json`|
|獨立全部LHE QA與source IDs|`validation/lhe_validation.json`|
|全部HepMC3／GZ|`pythia/full1000/shower.hepmc3`、`shower.hepmc3.gz`|
|每次輸入／失敗／原始權重|`pythia/full1000/event_ledger.jsonl`|
|實際ReaderAscii QA／ancestry|`background_hepmc_validation.json`、`hepmc_ancestry.jsonl`|
|實際原始／inclusive／effective decay表|`pythia/full1000/decay_tables_*.json`及XML|
|完整ROOT／native QA|`delphes/full1000/detector.root`、`native_validation.json`|
|reco observables及cutflow|`delphes/full1000/reco_events.jsonl`、`cutflow.csv`|
|獨立統計／weight與BR closure|`validation/cutflow_statistics.json`、`weight_and_BR_ledger.json`|
|全鏈狀態／資源／失敗子程序|`run_manifest.json`、`logs/`|

## 查截面、計數與驗證

```bash
run="$HOME/simulations/phase6g_runs/zh_personal_1k_01"
python3 -m json.tool "$run/run_manifest.json"
python3 -m json.tool "$run/validation/lhe_validation.json"
python3 -m json.tool "$run/validation/weight_and_BR_ledger.json"
python3 -m json.tool "$run/validation/cutflow_statistics.json"
cat "$run/delphes/full1000/cutflow.csv"
sha256sum "$run/mg5/process/Events/zh1000/unweighted_events.lhe.gz" \
  "$run/pythia/full1000/shower.hepmc3.gz" \
  "$run/delphes/full1000/detector.root"
```

截面與integration error以 `lhe_validation.json` 的
`cross_section_pb`／`cross_section_uncertainty_pb` full-precision init值為準。
終端摘要只有顯示精度，不能替代這些值。權重保持原始signed XWGTUP與
完整原始分母1000，不以selected事件數重新normalize、不暗加luminosity。

B04/B05先驗證全部實際Info／converter／raw欄位與初始化H表，才可另列
`MODEL_BR_ONLY` raw-contribution×actual-model-BR；不再乘ZBR、HH factor2，
也不再乘已校正Info的HBR。Phase6F model參考與YR4參考分開保存。
B05為inclusive supported Pythia top/W route，production–decay spin未驗證。

B06只有一個Born photon，其他Photon origin另列。兩個reconstructed Photon
不建立jet→photon fake校準；fake、overlap及官方detector／BR解釋仍有獨立gate。
缺少photon／tagged-jet pair時，對應mass／DeltaR為null。
零survivors不證明背景為零；請讀統計報告的95%interval／upper bound。

## Cuts、失敗與發布

目前cards為版本化固定研究設定。不要直接修改卡片繞過hash保護；新增process
或改能量／cuts應建立新的明列contract、process-specific validators，先用
實際installed MG semantics檢查，再另行授權新的production。

按Ctrl+C或在本次run建立`STOP`可停止。原始失敗檔案、已產生計數與logs保留。
不要刪除失敗事件、改寫原始資料、用另一個seed補事件或把prefix總數當獨立統計。
輸出目錄存在時，工具拒絕覆寫。缺失證據為UNKNOWN，完整target不能假定已達成。
預檢／編譯失敗且實際未啟動integration時，可保留舊紀錄後修正程式並選新目錄；
一旦生成原始來源，就保留它供有界驗證／問題診斷，不重造來源去消除失敗。

本次早期B04命令曾因MG5輸出加入五個官方隱含預設值而停止在LHE比對。
程式已將這五個預設值納入嚴格比較；其他明列設定與未知欄位仍會拒絕。
這個特定、已保存SHA的來源可用下面的有界接續命令。它不呼叫MG5，
不覆寫原始manifest、authority或LHE，不允許重新嘗試已執行的shower。
實際操作是否通過，仍以本任務final decision為準。

```bash
bash simulation/new_backgrounds/scripts/run_background.sh \
  --process zh --events 1000 --seed 20261104 --energy 13000 \
  --resume-source "$HOME/simulations/phase6g_runs/zh_1k_v2" \
  --output "$HOME/simulations/phase6g_runs/zh_1k_downstream_v1" \
  --max-hours 3.9 --max-disk-gb 9.9
```

接續模式將原生成的實測時間與磁碟計入上限；本次另縮小到3.9小時／9.9GiB，
也為先前零事件預檢保留預算。僅接受已審查的特定舊來源與bridge SHA，
不提供任意失敗樣本重跑的開關。一般新樣本請使用前面的完整生成命令。

本次另保存一個reader context錯誤：前10個真實shower已寫出，generic physics
通過，但舊reader用沒有Event context的暫時Particle比對status。修正後的原生
reader已唯讀重驗同一10筆通過。下面的特定接續命令會複製這10筆完全相同的
HepMC、診斷與模型表，重新讀取它們，然後才執行尚未執行的100／1000階段。
它不呼叫MG5，也不重新shower前10筆；失敗資料及authority保留原樣。

```bash
bash simulation/new_backgrounds/scripts/run_background.sh \
  --process zh --events 1000 --seed 20261104 --energy 13000 \
  --resume-chain "$HOME/simulations/phase6g_runs/zh_1k_downstream_v1" \
  --output "$HOME/simulations/phase6g_runs/zh_1k_chain_v2" \
  --max-hours 3.9 --max-disk-gb 9.9
```

此模式也限已審查的精確manifest及來源SHA，使用另一個exclusive接續鎖。
原生成及第一次下游命令的時間／資料一併計入上限；任何新的物理validity
失敗仍會停止依賴步驟，不提供刪除失敗事件或更換seed補足計數的途徑。

個人run從不自動push。只有經完整實測QA、大小／SHA／原始來源檢查的選定
reference會放入 `reference_samples/new_backgrounds/`，先審查精確asset與文字
provenance再stage，檢查每個outgoing commit後更新獨立Draft PR。
full1000大檔留本機；Release只可提出方案，不自動發布。不使用付費Git LFS。
未核准PDF／PNG不stage；不merge、不force-push。

本次選定reference的準備與唯讀驗證命令已實際執行：

```bash
python3 -B simulation/new_backgrounds/scripts/publish_references.py \
  --run "$HOME/simulations/phase6g_runs/tth_1k"
python3 -B simulation/new_backgrounds/scripts/validate_references.py --repo .
```

第一個命令只將已通過full1000 gates的原LHE1000、full shower前100筆HepMC、
原Delphes100-entry ROOT與卡片／證據準備到本機reference目錄，沒有Git操作。
三個選定目錄在本次發布後已存在；再次執行會拒絕覆寫。若要發布另一個個人
樣本，先建立新的版本化reference contract／目錄並審查其來源，保留既有版本。
不要刪除既有reference來避開保護。

在獨立分支明列選定的source／report／reference路徑，提交前與push前分別執行：

```bash
python3 -B simulation/new_backgrounds/scripts/audit_payload.py --staged
git diff --cached --name-only
git commit -m "Add verified selected background reference"
python3 -B simulation/new_backgrounds/scripts/audit_payload.py \
  --outgoing codex/phase6f-zh-pilot-readiness
git push origin HEAD
```

只在audit通過且選定檔案已明列stage後使用上述Git步驟；不得把整個個人run、
vendor/build/cache或未核准figures加入commit。建立Draft PR後核對遠端各樣本SHA
及該head的CI；portable CI核對bytes／counts／bound native receipts，並不重新執行
MG5、Pythia或ROOT。個人生成命令本身永遠不自動發布。

本次B04的第三個停止點是新驗證器對已接受的極小signed jet mass重複套用
更嚴格的summed-pair檢查。唯讀修正後原ROOT100全部通過，ROOT10的reco與
cutflow完全相同。下列特定命令沿用全部已驗證shower，不呼叫MG5或Pythia；
ROOT10／100只重新分析相同檔案，僅full1000 Delphes是尚未執行的物理步驟。
這三種歷史接續命令各有單次來源鎖，不能再次執行來增加統計。

```bash
bash simulation/new_backgrounds/scripts/run_background.sh \
  --process zh --events 1000 --seed 20261104 --energy 13000 \
  --resume-detector "$HOME/simulations/phase6g_runs/zh_1k_chain_v2" \
  --output "$HOME/simulations/phase6g_runs/zh_1k_detector_v3" \
  --max-hours 3.9 --max-disk-gb 9.9
```

本任務實際執行結果以 `reports/phase6g_final_decision.md` 和
`metadata/phase6g_run_manifest.json` 為準。指南中的生成命令不是已通過的物理結果。
