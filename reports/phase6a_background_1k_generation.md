# Phase 6A background reference 1000-event generation

已用現有 MG5 3.5.16 自助指令實際完成 ccgg 與 light-jjgg 各 1000 events。既有 bbgg 1000 events 從 PR #9 原樣保留；本次只生成 2000 新事件，reference library 共 3000。未執行更大批次、Pythia 或 Delphes。

基線 PR #9 head `640bec6b64b2533bd33ac23d0a1e2e328e93e842`；新分支 `codex/phase6a-backgrounds-1k` 以 `codex/phase6a-mg5-lo-bbgg` 為 base。保留 PR #9 與其他分支，無 merge。

| Profile | Actual events | Seed | LO cross section ± integration error [pb] | Runtime [s] |
|---|---:|---:|---:|---:|
| bbgg | 1000 | 20261013 | 0.06624666 ± 0.0005940933 | 32.246294 |
| ccgg | 1000 | 20261021 | 0.6274417 ± 0.005190692 | 13.649301 |
| jjgg | 1000 | 20261022 | 9.436556 ± 0.0547472 | 28.844856 |

ccgg/jjgg runtime 為完整 CLI 實測 elapsed；bbgg 是歷史 manifest 的 process/event generator phases 之和，沒有重跑也不宣称為完整 CLI timing。所有 weight 均正值，zero/negative counts 均 0。

現有安裝官方 tag `v3.5.16` commit `3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7`，4658 retained source files identity 全部核對通過，未重新安裝。Python 3.12.15、GCC/G++/gfortran 14.4.0、GNU Make 4.4.1 在既有隔離 WSL toolchain 執行。ROOT 6.40.04 環境與 source/build 均未改動。

實際執行的參數如下（output 用可攜變數表示；當時使用兩個不同且不存在的本機目錄）：

```bash
bash simulation/mg5/scripts/generate_sample.sh --process simulation/mg5/cards/ccgg.mg5 --events 1000 --seed 20261021 --energy 13000 --output "$HOME/simulations/mg5_runs/phase6a_background_ccgg_1000" --jobs 2 --max-hours 1 --max-disk-gb 5
bash simulation/mg5/scripts/generate_sample.sh --process simulation/mg5/cards/jjgg_light.mg5 --events 1000 --seed 20261022 --energy 13000 --output "$HOME/simulations/mg5_runs/phase6a_background_jjgg_1000" --jobs 2 --max-hours 1 --max-disk-gb 5
```

Protection：2 workers; 1 hour overall wall-time limit; 5 GiB local output cap with periodic disk/headroom polling; RAM preflight check; process-group stop with failure evidence。真正的 local run manifests 含預檢資源與 execution exits，公開副本只替換本機路徑；不以 synthetic events 代替。個人產樣預設 LOCAL_ONLY，generator 不做 Git 操作。

MG5 `generate` help 實際顯示 `QCD=2`/`QED=2` 是 amplitude coupling-order 上限（`<=` semantics）。兩個 photons 要求 QED 至少 2，本次保留 QCD2/QED2 continuum tree content；純 QED4、loop-induced 及 Higgs/fragmentation/shower contributions 不在這些卡的內容。parser 實際成功，ungrouped 與 grouped counts 分別記錄，不能把 grouped directories 當作所有 flavor channels 數量。

| Profile | Parser processes / diagrams | Grouped representative subprocesses / diagrams | Generated subprocess directories |
|---|---:|---:|---:|
| bbgg | 6 / 150 | 4 / 110 | 2 |
| ccgg | 6 / 150 | 4 / 110 | 2 |
| jjgg | 47 / 1260 | 25 / 700 | 4 |

ccgg 終態為 c/cbar + 2 photons；jl 僅 g/u/d/s 及反夸克，排除終態 charm/bottom。proton 初態仍採 5F，包括 c/b PDFs。`sm-no_b_mass` restriction 實際將 MC/MB 和 charm/bottom Yukawa 設為 0；CTEQ6L1 built-in PDF ID10042、6500+6500 GeV、fixed muR=muF1=muF2=125 GeV。

Photon：`pta=25`, `etaa=2.5`, `draa=0.4`。新 ccgg/jjgg 普通 jet：`ptj=20`, `etaj=5`, `drjj=0.4`, `draj=0.4`, `maxjetflavor=4`。已讀 pinned release 的 `setcuts.f`，abs(PDG)<=4 與 gluon 走 ordinary jet cuts，b 走原 b-specific cuts。source SHA 與 line ranges 見 `cut-source-identities.json`。各 real LHE banner 的 run/param/process cards 逐字保存，MG5 產後 reset seed 的 card 僅保留本機，seed authority 為事件 banner。

pT、pair DeltaR 與有限 eta 切割提供本次有限 hard-parton phase space 的 soft/collinear regulators；photon-parton separation 是固定 DeltaR，`ptgmin=0`，沒有 smooth-cone isolation 或完整 fragmentation treatment。本次截面僅屬指定 generation phase space。

These are three separate LO parton-level reference categories. No shower/hadronization, detector response, charm/light-to-b mistags, shower flavour migration, photon fake background, or fragmentation contribution is modeled. Their cross sections are not summed and their event counts are not equal expected yields.

實際 logs/cards：`simulation/mg5/evidence/ccgg_reference_1000/`、`jjgg_reference_1000/`；audit/runtimes/toolchain：`simulation/mg5/evidence/background_1k/`。本機 full process directories 未加入 Git。
