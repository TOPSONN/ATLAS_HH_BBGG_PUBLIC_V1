# Phase12：runtime provenance 與 isolated 4F PDF recovery

本目錄以實際runtime snapshots、官方公開payload及現有LHAPDF reader減少Phase11兩項缺件。結論 **PASS_PHASE12_PARTIAL_RECOVERY**；不是完整generator相容性或物理背景驗證。完整欄位在[驗收報告](../../reports/phase12_final_report.md)。

## 已實際執行

- 三次read-only snapshots為不同PID、依序執行，共用同主機cache；9302bytes/e4567fd5…f77dca1穩定，但writer UNKNOWN。新baseline僅PROPOSED_UNAPPROVED，舊P11 gate維持BLOCKED。
- Phase7I exactb80 RouteA合約的明列inventories／callchain不綁定這份runtimeconfig；NOT_BOUND_BY_REVIEWED_CONTRACT不表示目前Phase7I build通過，也不自動失效。未執行prepare-review/HumanReview/build/StageA。
- 官方NNPDF30 LO nf4 member0與.info取得685937bytes；沒有下載101member archive，沒有寫installedPDFdirs。
- nativeLHAPDF6.5.6 canonical04完成36xfx/5alpha/5域外guard，10個input/backend依賴before/after rawhash相同；03與04同點結果相同。builtin metadata fallback如實記錄。
- alpha reference strict1e-6 diagnostic為false（relative2.626e-6），未放寬；alpha at91.1876實測.12470053368074485，名稱0130不是該點定義。

## 可重現的來源／方法檢查

在repo根目錄使用既有Python，不需安裝套件：

```bash
python3 -B -m unittest discover -s analysis/phase12/tests -p 'test_*.py' -v
python3 -B -m unittest discover -s analysis/phase11/tests -p 'test_*.py' -v
python3 -B analysis/phase12/scripts/validate_publication.py --repo .
```

CI只執行這些來源／方法與bounded-publication檢查。沒有本機installeddata，故不宣稱CI重跑實際nativePDF或runtime snapshots，也不重跑完整Phase8–11 ROOT analysis。

## 本次實際命令紀錄

以下是已執行命令的紀錄；指定output已存在會拒絕覆寫，請不要重跑下載。所有source/runtime/.dat位於獨立ext4工作區和results；私人config bytes、PDFgrids、backendconfigs與binaries不進Git。

```bash
cd /home/btu/projects/atlas_hh_phase12_v1
python3 -B analysis/phase12/scripts/audit_runtime.py --output-dir /home/btu/simulations/hh_phase12/run_01/runtime_01
python3 -B analysis/phase12/scripts/audit_phase7i_dependency.py --phase7i-checkout /home/btu/projects/atlas_hh_phase7i_b80e1677 --output /home/btu/simulations/hh_phase12/run_01/phase7i_dependency_impact.json
/home/btu/miniforge3/envs/atlas-hh-root/bin/python -B analysis/phase12/scripts/read_pdf_member.py --payload-root /home/btu/simulations/hh_phase12/run_01/public_pdf_01 --policy analysis/phase12/config/readback_points.json --output-dir /home/btu/simulations/hh_phase12/run_01/pdf_readback_04
```

下載程式為scripts/download_pdf_member.py，contract為config/acquisition_contract.json。實際由Windows現有Python3.14經WSL UNC路徑執行，因WSL HTTPS HEAD握手timeout（body0）；Windows標準TLS驗證成功，沒有關閉驗證或接受未知redirect。128MiB總body／80MiB單檔／onecandidate限制適用於該payload acquisition；685937只表示已量測的.info/memberbody，不冒稱整台host或webresearch流量。rawpublisherchecksum/signature未取得，publisher payload cryptographic authenticity未建立；正式grid licenceidentifier保留UNSPECIFIED，官方下載／科學使用有公開說明，本PR不宣稱再散布權。

下載發生於ancestor-symlink guard硬化之前；後續15項離線guard測試及actualparent唯讀檢查均通過，payload hashes不變。沒有再次下載，不把硬化後的版本說成新增end-to-end下載成功。

## 安全的現有證據重新審查

以下只讀既有證據與當前檔案，使用新的不存在output名稱。若runtime再次漂移，應保留BLOCKED，不要restore/normalize或編輯收據：

```bash
python3 -B analysis/phase12/scripts/audit_readiness.py --repo . --result-root /home/btu/simulations/hh_phase12/run_01 --output /home/btu/simulations/hh_phase12/run_01/user_readiness_01.json --matrix-output /home/btu/simulations/hh_phase12/run_01/user_matrix_01.json
```

數值輸出只屬PDF INTERFACE VALIDATION。沒有MG5 parser/process、ME/integral/hard events、Pythia/Delphes、RouteA或likelihood。futureparser request與cards全inactive；下一步仍須另行審查精確runtime/PDF/alpha/IR依賴並取得單獨明確授權。沒有新增或發布PDF/PNG figures。
