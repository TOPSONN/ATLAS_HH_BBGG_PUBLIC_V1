# Phase12D：隔離式 4F PDF 原生讀回與 alpha 診斷

**驗收結果：PASS_ISOLATED_NATIVE_PDF_INTERFACE_WITH_LIMITS。** 既有 LHAPDF 6.5.6 已實際讀取隔離資料夾內的 NNPDF30_lo_as_0130_nf_4 member 0，完成 36 個有限 xfxQ 數值、5 個正且有限的 alpha_s 數值及 5 個由 wrapper 在 native 呼叫前拒絕的 domain 負例。這項通過只限指定成員、指定點位與 PDF interface。declared alpha reference 的嚴格相對 10⁻⁶ 診斷仍為 **FALSE**；ME／shower alpha binding 與物理背景方案仍為 **UNVERIFIED_NOT_EXECUTED／BLOCKED**。

本報告以最終 `pdf_readback_04` 為 canonical 實測，保留 01／02 失敗及 03 的成功但有界結果；沒有用後來的 source correction 抹除歷史嘗試。

## 實際執行與 exact source binding

[最終執行收據](../analysis/phase12/evidence/native_PDF_isolated_readback_04_execution.json)記錄 exit=0、wall=0.253453261 s、CPU=0.206385 s，沒有 resource failure。執行命令使用既有環境，不安裝 reader：

```bash
/home/btu/miniforge3/envs/atlas-hh-root/bin/python -B \
  analysis/phase12/scripts/read_pdf_member.py \
  --payload-root /home/btu/simulations/hh_phase12/run_01/public_pdf_01 \
  --policy analysis/phase12/config/readback_points.json \
  --output-dir /home/btu/simulations/hh_phase12/run_01/pdf_readback_04
```

這是已執行命令的 provenance，並非要求再次執行。最終程式在 native import 前檢查 exact external payload root、regular resolved parent、指定命名的 fresh output；既有 output 必須拒絕。reader／interface 的更正只加入觀察到的 native API／路徑語義與輸出保護，沒有擴充四個 x,Q 點、五個 alpha Q 值或放寬相對診斷 tolerance。

[原生讀回收據](../analysis/phase12/evidence/pdf_readback_04/pdf_member_readback.json)及 [alpha 收據](../analysis/phase12/evidence/pdf_readback_04/pdf_alpha_reference_checks.json)綁定以下五個實際來源 SHA-256；[source before](../analysis/phase12/evidence/pdf_readback_sources_04_before.json)／[source after](../analysis/phase12/evidence/pdf_readback_sources_04_after.json)相同。

| 來源 | SHA-256 |
|---|---|
| scripts/read_pdf_member.py | b66559e09d94873e4a9e633e41206e927a563ce58f51ef01f8aeed9811780bcf |
| source/pdf_interface.py | 3bdc2a166fa480a1d17127f1d01cf5b3bebe3bf545f672948895fe499204c387 |
| source/pdf_metadata.py | 70de57fd7e91f62e604e26d2e32bff5a56f1adada1d77dcf8fc2e1668f714406 |
| source/pdf_acquisition.py | c45ef8d6ba8aa6e3950dde9d6ef6fd798229d7458c69d0f6442724bc4e16476f |
| config/readback_points.json | a303682dceadbbd88e19a81f6f5e493ebea2a3d1d1dad9d0644ead4e696f0a63 |

canonical 結果不是只有 metadata parser 通過：它實際載入 native member、核對 ID／flavours／domain、呼叫指定的 xfxQ／alphasQ，再保留數值。相對地，[metadata source](../analysis/phase12/source/pdf_metadata.py)與 30 個 synthetic fixtures 只驗證 strict parsing、metadata／header 與拒絕案例，不能替代原生讀回。

## 成員、路徑及不可變輸入

來源與條款審查見 [Phase12C](phase12c_4f_pdf_candidate.md)。本機僅取得同一官方 distribution 的 `.info` 與 member 0：DataVersion 2、ID 263400、中央成員。101 是 released members 總數；沒有下載其餘 100 replicas，沒有 PDF ensemble uncertainty 結果。

| 本機原始檔 | bytes | SHA-256 |
|---|---:|---|
| NNPDF30_lo_as_0130_nf_4.info | 2345 | 85f3b2626de0896f45f5cfef53d90abd8d7b5ae784800b18d652e3f817431162 |
| NNPDF30_lo_as_0130_nf_4_0000.dat | 683592 | e3055763f3a3154c2a2c6811d35e1f319a0bb38ff1c645c8db5cdc8bd210005e |

native `paths()` 實際回報兩個目錄：external `public_pdf_01` 及既有環境 `share/LHAPDF`。LHAPDF 仍附加 builtin metadata 搜尋路徑，因此不能宣稱搜尋路徑只有 external 一個。最終檢查限制 exactly 這兩個目錄，確認 builtin 目錄沒有同名 candidate set，並以 native `findFile` 核對所選 info、member、lhapdf.conf、pdfsets.index 全部解析至 external copies。結論是 **external selected-member resolution，保留已觀察的 builtin metadata fallback**。

existing lhapdf.conf／pdfsets.index 只以 exact bytes 複製至 external root，與 installed 原件相等；沒有改寫 installed config、套件或全域 shell 設定。搜尋環境變數限該次 Python process。raw grid、private runtime config bytes 及 binaries 留在本機。

canonical native job 對 10 個 input／dependency 保存 before／after bytes、SHA、resolved path：info、member、installed／external config 各一、installed／external index 各一、Python executable、libLHAPDF.so、Python package __init__.py 及 lhapdf.so；全部 before=after。獨立 review 再次唯讀重算 live SHA，相同。這是指定檔案的 raw identity 證據，不宣稱對整台機器或全部動態載入行為做完 tracing。

native flavours 為 −4,−3,−2,−1,1,2,3,4,21，hasFlavor(±5) 均未啟用，native ID=263400。metadata 與 native domain 相同：x∈[9.9999997×10⁻¹⁰,1]、Q∈[1,100000] GeV。PDF 與 alpha metadata 均為 order 0、variable scheme、maximum flavours 4；variable 不代表 5F。MC／MB／MT evolution masses 不改作 ME pole masses，也不由這次 standalone interface 推定 massive-bottom ME 或 matching 已可用。

## 實測點位與 domain guard

固定的四個 (x,Q/GeV) 是 (0.0001,10)、(0.01,91.1876)、(0.1,1000)、(0.5,100)。每點只讀上述九個 flavours，合計 **36 xfxQ 值，全部 finite**。完整雙精度值在 canonical JSON；nonfinite_errors=0、interpolation_errors=0。[03／04 回歸](../analysis/phase12/evidence/native_PDF_same_points_regression.json)核對 36 xfxQ 與 5 alpha 數值逐項相同、raw input SHA 相同、expanded points=0。

| Q / GeV | 實際 native alpha_s(Q) |
|---:|---:|
| 4.1799998 | 0.254403024565842 |
| 10 | 0.1965543155814504 |
| 91.1876 | 0.12470053368074485 |
| 100 | 0.12282594881647993 |
| 1000 | 0.08932158963547387 |

五個 domain 負例為 (x,Q)=(0,10)、(1.1,10)、(0.1,0.5)、(0.1,200000)、(NaN,10)。它們全由 wrapper 拒絕，記錄 `OUT_OF_DOMAIN_REJECTED_BEFORE_NATIVE_CALL`／native_xfxQ_called=false。**沒有測試或宣稱 LHAPDF 預設 extrapolator 自己會拒絕超界輸入。** 本結果只證明這個 wrapper 的有界入口。

## Alpha reference 不一致與來源語義

實際 info 的 MZ=4.1799998 GeV、AlphaS_MZ=0.2544023564420006。此處 MZ 是該 set 的 reference scale；不能從欄位名替換成 electroweak Z mass，也不能從 set 名稱的 0130 推定 reference coupling。明確測得 alpha_s(91.1876)=0.12470053368074485，並非 0.130。

| Reference 診斷 | 實測／結果 |
|---|---:|
| declared Q / GeV | 4.1799998 |
| declared alpha_s | 0.2544023564420006 |
| native alpha_s(declared Q) | 0.254403024565842 |
| native − declared | 6.681238414185664×10⁻⁷ |
| relative difference / declared | 2.626248635282933×10⁻⁶ |
| strict diagnostic relative tolerance | 1×10⁻⁶，未放寬 |
| within_strict_diagnostic_tolerance | **false** |
| publisher interpolation accuracy bound | UNKNOWN／null |
| physical ME or shower alpha binding | **UNVERIFIED_NOT_EXECUTED** |

4.1799998 不是 AlphaS_Qs table knot。相鄰節點為 Q=3.7262747、alpha=0.26466316 與 Q=4.23139、alpha=0.25335777。因此比較的是 tabulated ipol 在非節點處的實際結果與 declared reference metadata；不是把 table knot 自己重新讀回的恆等檢查。

為判讀差異，唯讀核對 installed `include/LHAPDF/AlphaS.h`（10202 bytes，SHA256 `5cb6ef49a769df21f34789b6d849215e1cdbd264fc925d54afa5192931f55897`）。第 83–91 行對 setMZ／setAlphaSMZ 的註解指出 ODE solver 用途；第 213–242 行將 AlphaS_Ipol 定義為從 metadata 的 Q²／alpha table 插值，允許 subgrid 邊界的相同 Q 值有不同 alpha；第 247–248 行另列 cubic interpolation 方法。這與 [官方 AlphaS_Ipol API](https://www.lhapdf.org/classLHAPDF_1_1AlphaS__Ipol.html)及 [configuration semantics](https://www.lhapdf.org/config.html)一致。

這些來源支持區分 ODE reference setters 與 ipol table，但沒有建立「ipol 必須在非 knot 的 MZ 精確重現 AlphaS_MZ」的數值保證，也沒有取得 publisher 的相對 10⁻⁶ interpolation accuracy bound。沒有讀取完整 AlphaS.cc／factory 實作或獨立重寫 compiled cubic algorithm，因此不把差值完全歸因為已證明的某個插值誤差，也不藉此宣布官方 grid 無效。**嚴格診斷 false 原值保存，有限 interface 通過與物理 reference closure 未驗證分開呈現。** 沒有調整 grid、alpha table、reference 或 tolerance 來消除差異。

## 失敗歷史與獨立數值覆核

| 嘗試 | 實際狀態 | 保留與限制 |
|---|---|---|
| 01 | exit 1；LIVE_DATA_SEARCH_PATH_NOT_ISOLATED | native mkPDF 前停下；原假設忽略了 builtin path 自動附加。保留原 log，不宣稱成功讀回。 |
| 02 | exit 1；ALPHA_REFERENCE_INTERFACE_DISAGREES | 實際進入 member／有限點計算後，舊版 strict assert 中止於數值保存前。保留 log；不把它當 canonical 完整數值證據。 |
| 03 | exit 0；PASS interface with limits | 改為明列 diagnostic=false，保存數值與限制。wall 0.509157513 s。 |
| 04 | exit 0；canonical PASS interface with limits | 加上 fresh-output／parent guards 的 exact final source；同樣的 36／5／5，wall 0.253453261 s。 |

對應證據為 [01 log](../analysis/phase12/evidence/native_PDF_isolated_readback_01.log)、[02 log](../analysis/phase12/evidence/native_PDF_isolated_readback_02.log)、[03 receipt](../analysis/phase12/evidence/pdf_readback_03/pdf_member_readback.json)與 [04 receipt](../analysis/phase12/evidence/pdf_readback_04/pdf_member_readback.json)。01／02 空 output 目錄及原始 failure logs 皆保留。

[獨立 review](../analysis/phase12/evidence/pdf_independent_review.json)完成 **65 個檢查**：核對兩份 canonical JSON、固定點位、36 finite 數值、5 alpha／5 reject、10 raw dependency live identities、5 exact current sources、03／04 同值、table bracket、installed header witnesses 與所有零 production counters。另用 stdlib Decimal 60 位精度，從序列化的 native／declared 數值重算 relative difference=2.6262486352099527…×10⁻⁶；與 binary-float 收據的末位差異是重建表示的 rounding，strict threshold 超出結論相同。這是獨立數值／來源覆核，不是第二套 native alpha 計算、外部人工簽核或新的 PDF evaluation。review 的新 native PDF 呼叫數為 0。

## Acquisition guard 的時序與驗收界線

實際 acquisition 取得同一 selected distribution 的兩個 response bodies，共 **685937 bytes**，低於 128 MiB aggregate／80 MiB single-payload bound；這個數字只涵蓋 selected PDF acquisition body，不是所有來源研究網路流量。[原始取得收據](../analysis/phase12/evidence/public_pdf_01/acquisition_receipt.json)記錄 exact HTTPS、長度與 SHA；publisher checksum／signature 未取得，本機 SHA 是此次 bytes identity，不是獨立 publisher cryptographic authenticity proof。

[acquisition 獨立審查](../analysis/phase12/evidence/acquisition_independent_review.json)明列：actual download 發生在 parent-symlink guard hardening 前；後來的 15 個 method tests 與 actual parent 的唯讀 guard proof 都通過，原始路徑未觀察到 redirected ancestor，但沒有重下載。因此不能把最終 hardened acquisition source 宣稱為已完成新的 network end-to-end run。04 實際執行的是最終 reader guards 與既有完整 payload 的 native 讀回，沒有額外 payload acquisition。

本報告不批准任何 MG5 import/parser、process generation、ME、積分、hard events、Pythia、Delphes、RouteA build 或 Stage A。canonical 收據的上述 ME／integral／hard／Pythia／Delphes counters 全為 0，MG5_parser_executed=false、matching_validated=false、physical_component_validated=false、installed_directory_writes=false。總物理背景仍 BLOCKED；fake source 仍 UNKNOWN；significance／CLs 仍 NOT_EVALUATED。後續若要將此 PDF 與 massive-bottom generator／ME alpha／shower tune／scale convention 綁定，必須先另行審查與授權，不能由 standalone interface PASS 自動進入 pilot。