# Phase11A：massive-bottom 4F 候選的來源與 PDF 審查

本項結論為 `BLOCKED_PHASE11_PDF_OR_ALPHA_S`。MG5 3.5.16 的預設 `sm` restriction 可以支持 massive-bottom、massless-charm 的硬過程來源定義；本機明確檢查的 PDF 搜尋範圍內，沒有可綁定的相容 4F LO member payload。PDF、member、LHAID、grid／info SHA256、alpha_s 參考值與參考尺度仍為 `null`。候選沒有被選為可執行 pilot，也不是 inclusive diphoton+HF 總背景。

`audit_model_pdf.py` 已實際執行；A02 收據為本機 `hh_phase11/run_01/phase11_model_pdf_audit_02.json`，工作耗時 0.757 秒。它只讀取文字、表格與雜湊，沒有匯入 MG5／PDF library、執行 parser、ME、積分、Pythia 或 Delphes。證據類別為 `HISTORICAL_SOURCE_AUDIT`；獨立公開文件查核另標 `PUBLIC_SOURCE_AUDIT`，兩者都不是物理 pilot。

## 1. 硬過程與有效 mass restriction

候選文字保持為不可執行的提案：

```text
# INACTIVE; PARSER_NOT_VALIDATED; PHYSICAL_PILOT_NOT_EXECUTED
# import model sm
# define p4 = g u u~ d d~ s s~ c c~
# generate p4 p4 > b b~ a a QCD=2 QED=2
```

`models/import_ufo.py:227–228` 顯示預設讀取 `restrict_default.dat`。實際有效值在該檔第 17、18 行是 MC=0、MB=4.7 GeV；`parameters.py:136` 的未 restriction MC=1.27 GeV 不能當成此模型的有效 charm 質量。對照如下。

| restriction | MC [GeV] | MB [GeV] | 意義 |
|---|---:|---:|---|
| `sm`／default | 0 | 4.7 | 本項 massive-bottom 候選 |
| `sm-no_b_mass` | 0 | 0 | 歷史 massless-bottom 來源，不能替代本項 |
| `sm-c_mass` | 1.55 | 4.7 | 不同候選；不能直接保留本項 massless incoming charm 合約 |

p4 明列 g、u/d/s/c 及其反粒子，不含 incoming b。`QCD=2 QED=2` 是 amplitude order 的上限文字，不能寫成已經 parser 驗證的精確階數限制。bbγγ 的直接強作用 Born 分量預期為 alpha_s² alpha_EM²，但實際圖集、cross section、diagram 分類與輸出卡皆尚未生成。弱作用其他階數、loop-induced、fragmentation 和其他 multiplicity 都沒有因此取得有效覆蓋。

有效 restriction SHA256：`cc9e735d3dea306b31dcf3ef179719fceeefb505406bd163308324dc9aebda53`。未 restriction parameters SHA256：`2e4046c3566f1fb62fad92ffa705eef66a0124cc2a1cf4cc0d0ff2dc7f94c8fc`。完整 17 個 MG5 來源的 path、resolved path、bytes、SHA256 與逐行 witness 保存在 A02；讀取前後 hash 相同。

## 2. 有界的已安裝 PDF 清查

清查並未宣稱遍歷整台電腦、未設定的私有目錄或壓縮檔。實際執行時 `LHAPDF_DATA_PATH`、`LHAPATH` 未設定；另查下列明確 configured／conventional roots。每個目錄的深度界線、所有範圍內檔案 bytes／SHA256，以及未遍歷目錄均有機器可讀記錄。

| 路徑 | 範圍與實際結果 |
|---|---|
| MG5 `Template/LO/lib/Pdfdata` | 根層全部 12 個 grid／table；沒有 `cteq5f4.tbl` |
| MG5 `vendor/SudGen` | 根層 36 個項目，其中 1 個 broken symlink；輔助來源不能冒充新 backend |
| Pythia `share/Pythia8/pdfdata` | 根層全部 58 個檔案；不假定它們可被 MG5 直接當成相容 4F PDF |
| ROOT 環境 `share/LHAPDF` | 只有 `lhapdf.conf`、`pdfsets.index`，沒有 member grid／set info |
| `~/.local/share/LHAPDF`、`~/.local/share/lhapdf`、`~/.lhapdf` | 不存在 |
| `/usr/local/share/LHAPDF`、`/usr/share/LHAPDF` | 不存在 |
| MG5 `HEPTools/lhapdf6/share/LHAPDF` | 不存在 |

A01 曾遇到 SudGen 中指向不存在檔案的 symlink，因而在任何輸出／物理執行前停止。原失敗日誌保留；A02 會記錄 `BROKEN_SYMLINK`、link target、`bytes=null`、`sha256=null`，不忽略失敗或把未知寫成零。所有範圍內目錄沒有未遍歷的 symlink directory／depth-limit remainder。

MG5 `pdf_list.txt:52` 的 CTEQ5F4 是目錄文字，不能證明 payload 已安裝。`pdfwrap.f:207–209` 對應分支本身也已註解；目錄給出的 alpha_s(MZ)=0.112、two-loop 不能靜默升格為此 LO 候選的相容設定。

本機 `pdfsets.index` 第 129、1061 行有 CT14lo_NF4／13202 與 NNPDF30_lo_as_0130_nf_4／263400 的公開目錄識別，但本項沒有安裝、下載 member grid、選擇任何 member，或把目錄 ID 當成已存在 payload。未執行 library interpolation。

## 3. Alpha_s、flavour threshold 與參考尺度

4F 不等於要求所有 metadata 都寫 `FlavorScheme=fixed`。一個最高 active flavour 為 4、在 charm threshold 下轉換而從不啟用 bottom PDF 的 variable scheme，也可能是 4F 候選；必須核對精確 member、PDF 與 alpha_s scheme、threshold 與使用尺度。

公開 [NNPDF30 LO nf4 metadata](https://lhapdfsets.web.cern.ch/current/NNPDF30_lo_as_0130_nf_4/NNPDF30_lo_as_0130_nf_4.info) 就是具體反例：最高 4 flavour、沒有 b parton，metadata 採 variable；其 alpha 參考尺度標為 4.1799998 GeV，參考值為 0.254402356442，不能從 set 名字或 `AlphaS_MZ` 欄位名稱推成物理 Z 質量下的 0.130。此公開 metadata 回應 2345 bytes，SHA256 `85f3b2626de0896f45f5cfef53d90abd8d7b5ae784800b18d652e3f817431162`，取得時間 2026-10-19T08:18:31.8739627Z。它只用來檢驗 schema 的語意，不是已安裝或已選定的 PDF。

[LHAPDF 官方 configuration 說明](https://www.lhapdf.org/config.html) 區分 PDF 與 alpha_s 的 flavour scheme、order、threshold、member override。全域 `lhapdf.conf` 的 mass 預設值不是缺少 member metadata 的替代品。本項 schema 因此要求 alpha 的參考值和尺度同時存在，並保留 info/grid hashes；LO、no-bottom 與 threshold 相容性另作明確檢查。

本機 CTEQ6L1 只作反證診斷，沒有拿來替代 A：

| 層級 | 來源可確認內容 |
|---|---|
| PDF table header | maximum flavour=5；charm／bottom mass parameters 1.3／4.5 GeV |
| MG5 `pdfwrap.f:233–236` | alpha_s=0.130，one-loop |
| MG5 `alfas_functions.f:96–100,141–151` | alpha 演化上限 nf=5；預設 charm／bottom thresholds 1.42／4.7 GeV |

PDF evolution mass parameters、模型 pole mass 和 alpha matching threshold 是不同定義。這些非同一數值是需要精確追蹤的 review item，不是單憑相異數字就宣告所有方案不相容。本項尚未生成程式，沒有聲稱上述預設已成為某個新 executable 的有效值。

若未來採 LHAPDF，安裝的 MG5 interface 在 `alfas_functions_lhapdf.f:74–83` 將 ALPHAS(Q) 委派到 alphasPDF(Q)，而 `pdf_lhapdf6.cc:441–444` 再交給 active member 的 alphasQ(Q)。這只確認介面來源存在，未證明任何 4F member 已綁定。

## 4. Photon IR、shower 與權重仍需補齊

LO smooth-cone sum 使用 `is_a_j`。當 `maxjetflavor=4` 時，b 會進入 `is_a_b`，沒有被同一個 Frixione sum 包含；positive ptgmin 會停用 draj，但不會停用 drab。finite MB 可調節 bγ 的嚴格 collinear divergence，卻不能自動證明此 hybrid acceptance 等同全 QCD Frixione 或 detector fixed-cone。A 的精確 photon target、drab 與 generation cuts 因此維持 null／BLOCKED，詳見 Phase11C。

shower g→bb／cc、incoming heavy threshold、QCD/QED shower 和選用 tune 尚未綁定；既有 shower heavy births 不能替這些新設定背書。若未來執行，必須保存 LHE IDWTUP、來源 cross section/error、全部 accepted/rejected counters、sumW/sumW2、事件索引、merging weight（若適用）與 writer identity。Signed weight 的代數測試不等於 writer closure；目前沒有為此新候選選定物理正規化或 shower weight。

## 5. 明確的下一個證據需求

需要的是一個經另外審查並允許取得的 LO、最高 4 active flavours／無 bottom PDF 的精確 proton PDF member，以及 info 和 grid 原始 bytes／SHA256、member／LHAID、alpha 參考尺度與值、running order／type／threshold、有效 MG5 backend 綁定。還需 mass／scale／photon IR 相容定義與獨立檢查。禁止用 5F PDF 默默補洞；也不能把本項獨立 bbγγ component 加上其他未證明互斥的分量作物理總和。

修正後 29 個 method／negative fixtures 全部通過，涵蓋 mass restriction、incoming b、已知 5F 即使其他欄位 null 也拒絕、zero alpha、member=0 與 unknown、threshold、reference-scale、broken symlink 與 inactive/exclusivity gate。它們是合成或來源解析測試，沒有外部人類 physics signoff。整體 CI／歷史保存驗收以 Phase11 最終報告為準。
## 最終外部來源身分阻擋

A02 在稽核當下的 before/after 相同，不保證之後外部檔案仍相同。最終重讀發現已安裝 MG5 `input/mg5_configuration.txt` 從 9212 bytes、SHA256 `83d48923f215d20565931e8e0eb6ee986b34658d0bbe6f2e7a75e0400b4d7f85`，變成 9239 bytes、`9132f5ddcab8eb45ee00830d3ed9b7582bda67058180288d3f93222a96f74506`，再變成 9266 bytes、`82a6d1943d0acd139704910dfd0510ee2bd86d06f94a410b5f28e68a45bc3f5a`。在記憶體逆向移除三個設定行的註解 padding 與其空白行，可精確重建前兩個雜湊；有效設定相同。這是經雜湊核對的重建，不是找到磁碟備份，也不等同原始位元組凍結。已安裝檔案沒有被本工作回復或改寫。

MG5 `extended_cmd.py` 的 option serializer 可重現同樣的空白變化，但實際呼叫者 **UNKNOWN**，不能據此推定何人或何工作執行 MG5。本次受登錄工作沒有 generator dispatch；外部 host 全歷史活動並未受完整稽核。最新 gate 必須重算外部原始 SHA，漂移時明確標示 `BLOCKED_EXTERNAL_RUNTIME_CONFIGURATION_DRIFT`，不能只沿用 A02 收據或先正規化空白。這與 2874 個受監測歷史檔案保存全部通過是不同範圍。
