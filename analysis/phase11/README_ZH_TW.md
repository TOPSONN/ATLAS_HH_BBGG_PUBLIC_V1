# Phase11：精確generator設定與未啟用pilot gate

本目錄完成的是來源審查與既有資料驗證。結論為NONE_READY；沒有新MG5 parser/process、ME/integral、hard events、Pythia/Delphes production、Phase7I build/restart或physical likelihood。所有future cards均為全註解inactive文字，沒有dispatcher與approval override。

[最終驗收](../../reports/phase11_final_report.md)涵蓋欄位、測試、保存與交付；[選擇理由](../../reports/phase11d_generator_selection.md)及[有界pilot審查](../../reports/phase11f_bounded_pilot_review.md)說明精確缺件。A/B/C/E報告分別保存PDF/mass、family/interface、photon IR與detector control的實際來源證據。

## 具體減少的不確定性

- sm/default有效MC=0、MB=4.7；sm-no_b_mass二者為0。參數預設、restriction、PDF threshold及alpha reference分開。
- 10個明確安裝搜尋範圍沒有可綁定的4F member；catalogue、commented backend、公開.info均不是已安裝grid。
- QCD/QED等號是上限，雙等號才是精確amplitude階數；本次沒有解析任何卡。
- LO smooth cone只用is_a_j，maxjetflavor4時b另列is_a_b；ptgmin還會改變其他cut啟用情況，不能只看run-card表面值。
- MLM header能改effective settings；5F b/c需要一致matching flavour scope；CKKW-L native merging weight必須保留。沒有validated merging scale。
- Delphes isolation先原位更新candidate再拒絕；未來branch可保留隔離失敗候選。但標準writer未保留精確Candidate overlap graph，仍需另審writer；不因此得到fake calibration。

## 可重現的來源／方法測試

在repo根目錄用現有Python3，毋須安裝套件：

```bash
python3 -B -m unittest discover -s analysis/phase11/tests -p 'test_*.py' -v
python3 -B -m unittest discover -s analysis/phase10/tests -p 'test_*.py' -v
python3 -B -m unittest discover -s analysis/phase9/tests -p 'test_phase9_*.py' -v
python3 -B -m unittest discover -s analysis/phase8/tests -p 'test_*.py' -v
python3 -B analysis/phase11/scripts/validate_publication.py --repo .
```

GitHub CI只重跑來源／方法和有界已發布證據，不重跑本機安裝或完整ROOT資料。既有ROOT6.40.04/C++20環境原樣保存；本次不需要新增native build或完整ROOT loop。

## 靜態安裝來源與既有事件CLI

輸出必須使用不存在的新檔／目錄；不要指向Phase6–10任何歷史結果。以下只讀來源／既有檔，沒有generator呼叫：

```bash
cd /home/btu/projects/atlas_hh_phase11_v1
OUT=/home/btu/simulations/hh_phase11/user_source_audit_01
mkdir "$OUT"
python3 -B analysis/phase11/scripts/audit_model_pdf.py --output "$OUT/model_pdf.json"
python3 -B analysis/phase11/scripts/audit_family_ir.py \
  --repo . --mg5-root /home/btu/opt/mg5amcnlo --pythia-root /home/btu/opt/pythia8 \
  --output "$OUT/family_ir.json"
python3 -B analysis/phase11/scripts/audit_detector_events.py \
  --repo . --phase9 /home/btu/simulations/hh_phase9/run_01 \
  --phase8-manifest /home/btu/simulations/hh_phase8/run_01/phase8_local_manifest.json \
  --delphes-source /home/btu/.local/share/atlas-hh-phase6c/src/delphes-3.5.1 \
  --output "$OUT/detector_events"
python3 -B analysis/phase11/scripts/validate_event_covariance.py \
  --phase9 /home/btu/simulations/hh_phase9/run_01 \
  --diagnostics "$OUT/detector_events" \
  --phase10-summary /home/btu/simulations/hh_phase10/run_01/hf_02/phase10_hf_summary.json \
  --output "$OUT/independent_covariance.json"
python3 -B analysis/phase11/scripts/audit_pilot_gate.py \
  --repo . --model-audit "$OUT/model_pdf.json" --family-audit "$OUT/family_ir.json" \
  --detector-summary "$OUT/detector_events/phase11_existing_hf_event_crosscheck.json" \
  --independent-covariance "$OUT/independent_covariance.json" \
  --output "$OUT/pilot_readiness.json"
```

`BLOCKED_PHASE11_NO_VALIDATED_COMPONENT`是正常科學結論：CLI能完成審查，並不代表pilot可執行。source_supported只適用於已列來源前提；parser/matching/physical validation仍未完成。不要為了通過gate把null改為0、填historical defaults、增添approval flag或執行卡。

## 輸出及限制

有界evidence收錄model/PDF inventories、版本／行號／SHA256、225 origin-stage、675 origin-region、3825 covariance rows、獨立3885數值比較、source hash前後與保存清單。所有同事件多jet/origin flags共同使用原始N=1000；cross-dataset未知physical covariance保留null。資料共享祖先標籤的獨立性限制寫在各收據，不把重讀報告叫作第二個獨立物理樣本。

本次受監測歷史基準含2874檔、2611429240bytes：原970個Phase6–9路徑、全部舊Phase10結果／收據／remote snapshot及舊Phase10所有tracked檔。另核對舊PR24–27與stopped source HEAD/index；不宣稱遞迴檢查每一個停止工作區檔案。

未來資源示例仍未批准，aggregate future CPU ceiling也未凍結。只能另行提出精確source/PDF/card/hash、資源與新目錄的審查請求。既有12組Phase9圖維持AWAITING_USER_APPROVAL，本次不生成／提交新PDF/PNG，不merge、不force push。

## 初態b/c的額外精確讀回

舊combined HF不能當成incoming bottom。原始LHE3000筆讀回得到B01 bottom25/charm33、B02 bottom2/charm67、B03 bottom0/charm6；沒有ROOT loop。可使用另一個不存在的輸出目錄重現：

```bash
python3 -B analysis/phase11/scripts/audit_initial_flavours.py \
  --manifest /home/btu/simulations/hh_phase8/run_01/phase8_local_manifest.json \
  --phase9 /home/btu/simulations/hh_phase9/run_01 \
  --output "$OUT/initial_flavours"
```

保留原始source-event bytes SHA、index與權重；p4物種可容許子集不是物理4F轉換。本次全部172項Phase11 tests、143/165/92項Phase10/9/8 regression及5個歷史validator實際通過。

## 最終外部來源身分阻擋

A02 在稽核當下的 before/after 相同，不保證之後外部檔案仍相同。最終重讀發現已安裝 MG5 `input/mg5_configuration.txt` 從 9212 bytes、SHA256 `83d48923f215d20565931e8e0eb6ee986b34658d0bbe6f2e7a75e0400b4d7f85`，變成 9239 bytes、`9132f5ddcab8eb45ee00830d3ed9b7582bda67058180288d3f93222a96f74506`，再變成 9266 bytes、`82a6d1943d0acd139704910dfd0510ee2bd86d06f94a410b5f28e68a45bc3f5a`。在記憶體逆向移除三個設定行的註解 padding 與其空白行，可精確重建前兩個雜湊；有效設定相同。這是經雜湊核對的重建，不是找到磁碟備份，也不等同原始位元組凍結。已安裝檔案沒有被本工作回復或改寫。

MG5 `extended_cmd.py` 的 option serializer 可重現同樣的空白變化，但實際呼叫者 **UNKNOWN**，不能據此推定何人或何工作執行 MG5。本次受登錄工作沒有 generator dispatch；外部 host 全歷史活動並未受完整稽核。最新 gate 必須重算外部原始 SHA，漂移時明確標示 `BLOCKED_EXTERNAL_RUNTIME_CONFIGURATION_DRIFT`，不能只沿用 A02 收據或先正規化空白。這與 2874 個受監測歷史檔案保存全部通過是不同範圍。
