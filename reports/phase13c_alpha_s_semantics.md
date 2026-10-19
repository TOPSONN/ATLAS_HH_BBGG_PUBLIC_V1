# Phase13C：alpha_s 的參考值、ipol 與來源分層

Phase12 的原始 strict 診斷保持 **FALSE**：Q_reference=4.1799998 GeV，宣告值 0.2544023564420006，原生讀回值 0.254403024565842，絕對差約 6.681238414185664e-7、相對差 2.626248635282933e-6，高於當時的 1e-6 診斷門檻。本次不更改門檻、不改寫舊收據、不把它包裝成官方精度檢驗。官方 accuracy bound 仍為 `UNKNOWN`／null。

## 宣告值與插值表

原始 `.info` 的 MZ=4.1799998、AlphaS_MZ=0.25440235644200060；這是這個 set 的參考尺度與值。不能把欄名 MZ 當成固定 91.1876 GeV，也不能把 set 名中的 0130 填進未驗證的 ME 或 shower 參數。這些原始數值已由固定 SHA 的公開 metadata 再核對。

AlphaS_Type=ipol、AlphaS_OrderQCD=0。`AlphaS_Qs`/`AlphaS_Vals` 共 50 對表點；Q=1.275 重複，介面允許以重複邊界表達子網格。4.1799998 並非 knot，其相鄰表點為：

| Q (GeV) | alpha_s |
|---:|---:|
| 3.7262747 | 0.26466316 |
| 4.2313900 | 0.25335777 |

新 alpha 收據保存完整的 50 對數值以核對 knot 身分，不包含 PDF grid。已安裝 6.5.6 `AlphaS.h` 明確宣告以 Q² table、子網格、cubic interpolation、log(Q²) knot lookup 操作的 `AlphaS_Ipol`；`PDF.h` 顯示 `mkAlphaS(info())` 建立 alpha 物件，成員 `alphasQ(Q)` 經 Q² 傳給該物件。

已安裝套件不包含實作函式體 `AlphaS.cc`。本審核沒有獨立重現編譯中每一步插值運算，也沒有新增 native 點。因此目前能支持的是「宣告參考值與離散表插值結果是不同的量，觀察到的差值與此結構相容」，不能宣稱已證明完整誤差原因、官方容許精度或新物理不一致。介面與 cascade 定義另參照 [LHAPDF 6.5.6 AlphaS_Ipol](https://www.lhapdf.org/classLHAPDF_1_1AlphaS__Ipol.html) 與 [官方 configuration flags](https://www.lhapdf.org/config.html)。

## 味數與 threshold

本成員沒有 override alpha 或 threshold keys。alpha 的 flavour scheme 從 FlavorScheme=variable 取得、最大味數從 NumFlavors=4 取得；這些 fallback 來源在收據逐項標示。Charm 的 PDF/alpha threshold 來源為 MCharm=1.275 GeV；Bottom 是 MBottom=4.1799998；Top 是 MTop=173.07001。最大 4 味使 b、t 不啟用。這些是 PDF/evolution metadata 的值，不能當作 ME 中 b pole mass=4.7 的來源，更不能把兩個不同語義的質量視為應逐位相同的條件。

## MG5 的條件映射

`make_opts:110–125` 只有在 make 變數 lhapdf 非空時才選 `alfas_functions_lhapdf`。該檔 `ALPHAS(Q)` 呼叫 `alphasPDF(Q)`；6.5.6 對應的 `pdf_lhapdf62.cc` 最後以目前 member 的 `alphasQ(Q)` 求值。`GetOrderAs` 讀 AlphaS_OrderQCD，而 wrapper 再將 nloop 加一；這是兩種 order convention 的轉接，不能由變數名稱推斷多一圈的計算已發生。

`pdf_wrap_lhapdf.f:10/31` 另外以 Q=91.188 初始化 `asmz=alphasPDF(zmass)`。這不是把 `.info` 的 AlphaS_MZ=.2544023564420006 直接抄入 asmz。歷史 native04 量到的是 Q=91.1876 的 0.12470053368074485，不能冒充未執行的 91.188 之 asmz。本次將後者保持 null，直到未來授權的實際後端執行。

| alpha_s 所屬部分 | 現有證據 | 數值綁定狀態 |
|---|---|---|
| PDF 成員 | 歷史 native04、目前原始輸入與 library 再雜湊 | 歷史 standalone 支持；不是本次新量測 |
| ME coupling | 已審核條件式 Fortran/C++ 路徑 | null；UNVERIFIED_NOT_EXECUTED |
| ISR | 未啟動 shower；未審查實際運行參數 | null；UNVERIFIED_NOT_EXECUTED |
| FSR | 未啟動 shower；未審查實際運行參數 | null；UNVERIFIED_NOT_EXECUTED |

沒有任何一格以 PDF 名稱補齊其他部分；也沒有將 PDF 獨立讀回升格為 MG5／Pythia 綁定。MG5 parser、原生 ME、積分、hard events、Pythia 與 Delphes 在這次審核均為 0。

## 實際執行狀態

修正後 29 個方法測試已執行通過，包含 strict FALSE 保存、錯誤 91.1876 參考值、0.130 代入、不同 native 結果與 knot 長度錯誤拒絕。實際靜態 CLI `pdf_backend_02` 已完成（0.297 秒）；`alpha_s_reference_review.json` 為 20097 bytes、SHA256 `02f70fdb909fc5fd27fab1b2a0fa9385c918c08097b82ba1a0580faed9469d81`，狀態 `REVIEWED_IPOL_REFERENCE_DIAGNOSTIC_FALSE`。新證據保存原 strict FALSE、UNKNOWN 官方精度及未驗證的 ME/shower binding，不建立任何新 native PDF 量測。
