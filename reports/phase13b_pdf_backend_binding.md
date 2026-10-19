# Phase13B：外部 4F PDF 與 MG5 後端來源審核

本審核重用 Phase12 native04 已實際執行的獨立 LHAPDF 成員讀回，並重新雜湊目前的輸入、原生函式庫與讀回程式。Phase13 這支審核程式只讀文字與原始位元組，沒有載入 LHAPDF、匯入 MG5、編譯或執行生成器。獨立讀回與實際 MG5 綁定是兩種證據；後者保持 `UNVERIFIED_NOT_EXECUTED`。

## 固定的 PDF 成員

候選為 `NNPDF30_lo_as_0130_nf_4`、member 0、LHAPDF ID 263400、DataVersion 2。既有外部 `.info` 為 2345 bytes，SHA256 `85f3b2626de0896f45f5cfef53d90abd8d7b5ae784800b18d652e3f817431162`；member 為 683592 bytes，SHA256 `e3055763f3a3154c2a2c6811d35e1f319a0bb38ff1c645c8db5cdc8bd210005e`。本次不下載、不安裝、不複製 grid 到 Git。

Phase12 的實際原生 flavour 為 `[-4,-3,-2,-1,1,2,3,4,21]`，沒有 ±5；ID 263400、reader version 6.5.6。PDF OrderQCD=0，FlavorScheme=variable，最大味數=4，不能把 variable 直接誤稱固定味數，也不能因為 metadata 包含 MBottom 就宣稱啟用 b PDF。released members=101 並不代表本機已取得全部成員；本工作只使用 member 0。四個歷史點共 36 個有限 xfxQ 值，不是截面、ME 或外插的測試。

重新核對的歷史 native receipt SHA256 為 `13b49445a86537ec68e31d48c1438276b8d8d05f233df91f79ae166d72cb7b55`，alpha receipt 為 `c800618d3f03a0e03b0c8560875715306b4a15f2bef2607796dc759375c4a671`，兩者必須同時與 PR29 繼承的公開收據匹配。審核另外要求當年的 10 個原始依賴及 5 個讀回程式來源在目前仍完全匹配，並在讀取後再次核對；差一個 byte、大小或 resolved path 即拒絕。這是歷史原生證據的目前位元組閉合，沒有重新量測任何 native PDF 點。

## 版本與實際來源路徑

已安裝標頭 `include/LHAPDF/Version.h` 明示 6.5.6/60506；版本工具也包含 6.5.6，但本審核不執行它。共享函式庫 `lib/libLHAPDF.so` 的 SHA256 是 `dfca1050d6a9c155c2dba963a24e15e0c8c1460bd838a9a019151458995041d1`。每個相關標頭、MG5 source、版本工具、歷史 Python extension 的完整 SHA 與 witness 行號由新收據保存。

MG5 3.5.16 的 `Template/LO/Source/PDF/makefile:42–54` 在 lhapdfsubversion==1 使用 `pdf_lhapdf6.o`，其他 LHAPDF6 分支使用 `pdf_lhapdf62.o`。因此 6.5.6 的主要審核檔是 `Template/Common/Source/PDF/pdf_lhapdf62.cc`；不能把舊 `pdf_lhapdf6.cc` 的同名介面當作實際選中的版本。

來源呼叫鏈為：run-card `lhaid` → `pdf_wrap_lhapdf.f` 的 DEFAULT/value(1) → `pdfset_` 的 value[0] → `lookupPDF(id)` → `PDFSetHandler` → `mkPDF(setname,member)`。密度路徑為 `pdg2pdf` → `evolvepart` → 當前成員 `xfxQ`，再除以 x；所有映射目前只經來源審查。

## 仍未成立的數值 MG5 綁定

現有環境缺少 `lib/libLHAPDF.a`。MG5 的 `common_run_interface.py:4437–4442` 會建立這個靜態函式庫的 link，而 make_opts 另含 `lhapdf-config --libs` 與 `-lLHAPDF`。共享函式庫的獨立讀回成功，不能證明未來產生之 process 的 link 或載入結果。不得藉此更換函式庫或重裝套件；數值 ME 後端維持 `BLOCKED_UNVERIFIED_LINK_AND_RUNTIME_SELECTION`。

歷史 native04 的選中路徑是既有外部目錄，環境中的同名 set 不存在；全域 metadata fallback 有被觀察到，故沒有宣稱「完全沒有任何 fallback」。MG5 的 process-local `PDFsets`／`lib/PDFsets` 搜尋又是另一條路徑，必須在未來獲授權時固定並觀察。`copy_lhapdf_set()` 在缺少 set 時可呼叫 `install_lhapdf_pdfset()`；未來數值綁定審查必須禁止網路及安裝回退，不能只相信環境變數。

本次符號 parser scope 不評估 PDF 或 ME，故 PDF 數值函式庫不是該符號工作的必要依賴。這不解除未來 ME 的後端阻擋，也不把 parser-only 授權延伸到 link、PDF 數值呼叫或積分。

## 可重現驗證與限制

`analysis/phase13/scripts/audit_pdf_backend.py` 產生新的 `pdf_backend_review.json` 與 `alpha_s_reference_review.json`，拒絕覆寫。使用明確的 `--repo`、`--mg5-root`、`--lhapdf-prefix`、`--pdf-root`、`--phase12-readback`；所有路徑和 hash 記入收據。本機登記執行 `pdf_backend_02` 已完成（0.297 秒），結果為 `PASS_STATIC_BACKEND_MAPPING_WITH_LIMITS`。`pdf_backend_review.json` 為 27639 bytes、SHA256 `ed6c565ed9ef12c4dd14ea5b7f90242204406ba96605d2bde2eaee385f8cef9a`。第一次 `pdf_backend_01` 因 witness 字串空格不符而 exit 2，原失敗 log/ledger 保留；只修正來源 anchor 的字面拼寫，沒有改動任何已安裝來源或科學數值。

修正後 29 個 synthetic 方法測試已執行通過（0.014 秒），涵蓋錯誤成員、b flavour、參考尺度、成員 override、錯誤來源 anchor、raw whitespace、resolved-path 改指與輸出覆寫拒絕。這些測試沒有建立實際 MG5 綁定，也不是原生 PDF 新量測。

另外獨立比對了 actual B02 收據的 11 個 MG5 source 與 runtime 原始 manifest、目前隔離複本，5 個外部 header/tool source 與目前實檔，以及 native04 的 10 個依賴。全部 raw SHA、bytes、resolved paths 符合；新 `backend_source_closure_review.json` 為 19993 bytes、SHA256 `e6536daae51f7cacbd1d61b1dcf44426bec4889b1e4333937a43812779011f14`，狀態 `PASS_EXACT_BACKEND_SOURCE_MANIFEST_AND_COPY_CLOSURE`。這項 source closure 不代表未執行的 MG5 link/PDF binding 已通過。
