# Phase12C：官方 4F LO PDF 候選與來源／使用條款審查

本階段只選擇 **NNPDF30_lo_as_0130_nf_4，member 0，LHAPDF ID 263400，DataVersion 2**，作為隔離式 PDF interface validation 的唯一候選。這不是選定或批准 massive-bottom generator pilot；沒有 MG5 parser、ME、積分、Pythia 或 Delphes 執行。是否真正取得並可由 native reader 讀取，以實際 acquisition／readback 收據與 [Phase12D](phase12d_pdf_readback.md) 為準，不能由目錄名稱、metadata 或本報告推定。

## 官方來源與選擇理由

[NNPDF3.0 發布頁](https://nnpdf.mi.infn.it/nnpdf3-0/)把此 set 列在最高 NF=4 的 LO grids 中，並指定物理文獻 [arXiv:1410.8849](https://arxiv.org/abs/1410.8849)。[LHAPDF 官方 set catalogue](https://www.lhapdf.org/pdfsets)對應列記錄 SetIndex=263400、101 個 released members 與 DataVersion=2。[NNPDF 使用者頁](https://nnpdf.mi.infn.it/for-users/)及 [download/use 說明](https://nnpdf.mi.infn.it/for-users/tutorials-and-drivers/)提供公開 PDF 取得與使用方向；[LHAPDF 官方入口](https://www.lhapdf.org/)指向 CERN 的正式 set distribution。

唯一候選的精確 HTTPS 來源是：

- [官方 set info](https://lhapdfsets.web.cern.ch/current/NNPDF30_lo_as_0130_nf_4/NNPDF30_lo_as_0130_nf_4.info)
- [官方 member 0](https://lhapdfsets.web.cern.ch/current/NNPDF30_lo_as_0130_nf_4/NNPDF30_lo_as_0130_nf_4_0000.dat)

member 路徑依 [LHAPDF 的 set/member naming](https://www.lhapdf.org/design.html) 使用四位數索引；端點是否存在、回傳長度、redirect、完整 payload 與 raw SHA-256 必須由 bounded acquisition 實際檢查。本項來源研究沒有下載 archive 或 grid body，也沒有為 reader 安裝套件。root 決定僅取得 .info 與 member 0，不取得含 101 members 的 archive，也不取得其他候選。

member 0 在公開 SetDesc 中是 replica average；members 1–100 才是 PDF replicas。101 是發行版總數，不表示所有 members 都已存在本機，更不表示只取得中央 member 就能建立 PDF uncertainty band。

## Metadata 的精確物理語意

以下是公開 .info 的來源事實，實際取得後仍須對 info、member header 與 native interface 再核對。`pdf_metadata.py` 沒有把 set 名稱當成證明。

| 項目 | 公開 metadata／解釋 |
|---|---|
| publisher／distributor | NNPDF Collaboration／官方 LHAPDF CERN distribution |
| set/member identity | NNPDF30_lo_as_0130_nf_4；member 0；SetIndex/member LHAPDF ID 263400；DataVersion 2 |
| format／parent | lhagrid1；proton PDG 2212 |
| declared released members | 101；本階段只選中央 member 0 |
| Flavors | −4,−3,−2,−1,1,2,3,4,21；不含 b、反 b 或 top |
| FlavorScheme／NumFlavors | variable／最高 4；不是因 variable 這個字就改判為 5F |
| OrderQCD | 0，LO evolution metadata |
| AlphaS_OrderQCD／AlphaS_Type | 0／ipol；以成對 AlphaS_Qs／AlphaS_Vals 定義插值，不擅改 analytic running |
| reference scale | MZ=4.1799998 GeV；這裡是 set 自己的 alpha reference scale |
| reference value | AlphaS_MZ=0.25440235644200060，位於上述 reference scale |
| evolution masses | MCharm=1.275、MBottom=4.1799998、MTop=173.07001 GeV；不是新 ME pole masses |
| declared domain | x∈[9.9999997×10⁻¹⁰,1]；Q∈[1,100000] GeV |
| ForcePositive | 2；屬 interface positivity policy，不是新的物理驗證 |

依 [官方 configuration flags](https://www.lhapdf.org/config.html)，AlphaS_NumFlavors／AlphaS_FlavorScheme 若未另列，回到 NumFlavors／FlavorScheme。此 fallback 的來源在結果中明列，不拿未記錄的 global defaults 填空。ThresholdCharm/Bottom/Top 與 AlphaS-specific threshold/mass 欄位有各自的 metadata resolution；本 set 沒有明列的 threshold 需按已記錄的 mass fallback 解讀，並由實際 reader/source 核對。MCharm 對應的重複 alpha Q nodes 可以是 table 分段位置，不能把所有重複節點或 MBottom 數值視為獨立已驗證的活化事件。

**不能把欄位名 MZ 自動替換成 91.1876 GeV，也不能把 set 名稱中的 0130 當成這個 reference point 的 alpha 值。** native reader 應分開報告 alpha 在 declared reference 與其他明確有限 Q 點的實際值；本項 metadata 審查不預先填入量測結果。AlphaS_Lambda5 之類未用於 ipol 的附帶欄位，也不能獨自證明 bottom 已活化。

PDF maximum flavours=4 與不含 ±5 的 flavour list 支持這個 4F 候選的來源範圍。它沒有證明與某個未生成的 MG5 executable、shower tune、ME／ISR／FSR alpha、threshold／scale convention 已完成物理匹配。模型 sm/default 的 MB=4.7、MC=0 與這裡 evolution masses 的不同定義需保留，不能要求字面相等，也不能忽略其方案審查。

## License、使用範圍與 cryptographic provenance

已檢查的官方 publisher／distribution 頁面明確提供 PDF 的公開下載與科學使用說明，但未找到對這個 NNPDF3.0 grid 明列的獨立 license identifier。故結論是 **PUBLIC_DOWNLOAD_AND_SCIENTIFIC_USE_DOCUMENTED；FORMAL_GRID_LICENCE=UNSPECIFIED**，不是推定 CC、GPL 或無限制再散布。NNPDF fitting code／LHAPDF code 的 software license 不可自動轉移成此 grid 的資料授權。

本任務的使用範圍限定為使用者明確允許、隔離本機資料夾內的 bounded scientific interface validation；沒有把下載 grid、private runtime config bytes 或 binaries 放上 GitHub。引用同時保留 NNPDF3.0 物理論文及 [LHAPDF6 文獻 arXiv:1412.7420](https://arxiv.org/abs/1412.7420)。若未來要再散布 payload，不能由本報告假定已取得額外權利。

在已檢查的官方頁面未找到 publisher-provided checksum 或 signed manifest。下載後量出的 SHA-256 用來凍結此次收到的 bytes，**不是 publisher 的 cryptographic authenticity proof**。HTTPS 正式端點、來源頁與 raw hashes 提供有界來源證據；不得捏造 expected checksum 或省略這個限制。`current/` URL 可以更新，須以此次取得的 DataVersion、bytes、SHA 與時間綁定，不能只保存可變 URL。

## 取得與原生讀回的界線

[來源 policy](../analysis/phase12/config/pdf_source_policy.json)只描述一個選定 distribution、.info/member pair、128 MiB aggregate response-body budget、80 MiB single payload limit、HTTPS／未知 redirect／partial／oversize 拒絕、fresh isolated directory 與禁止 installed-path writes。這些是可審查條件；實際執行與完整記帳由 acquisition 收據證明，不能由設定檔的數字宣稱已 enforce。

catalogue entry、public metadata、actual member payload、working native reader 是四種不同證據。`inspect_local_pair` 只驗證真實檔案存在、canonical filenames、header、member override、metadata、bytes 與 SHA；即使 header 合法，仍不能保證 grid body 完整或可插值。native LHAPDF6 讀回須另外執行，保留 reader/library／isolated config 身份、實際 flavours、alpha evaluation、finite values、錯誤與 domain policy。

LHAPDF 的預設 extrapolator 不一定會拒絕 domain 外呼叫；本任務要求的 out-of-domain rejection 必須分清是 caller 的明確 guard／error policy，還是 native default 的行為。不能測到 wrapper 拒絕後，便聲稱 library 原本從不 extrapolate。環境搜尋路徑與必要 default config 應在單一隔離程序中明確控制，不改全域 shell、live MG5 或 conda PDF directory。

## 方法測試與保留 gates

`test_pdf_metadata.py` 的 **30 個小型 synthetic fixtures 已通過**，涵蓋 member=0／Order=0 的已知零、variable-max4、b activation 拒絕、alpha-max5 override 拒絕、錯誤 reference 推論、缺值／空 reference、NaN、無效 alpha tables、data-version drift、duplicate keys、缺少真正 member、member override、replica 冒稱 central、header 截斷及沒有 network/native/generator dispatch。刻意使用合法 header 配假的 grid body 的 fixture，明確要求結果保持 NOT_TESTED_BY_METADATA_VALIDATION；不把方法測試偽裝成實際 PDF payload。

本項可解除的只有取得後經 native readback 證明的「沒有這個隔離 member／interface」缺件。它不解除 runtime baseline approval、MG5 parser、photon IR/cuts、hard scales、shower／matching、weight closure 或物理總背景 gate。PHYSICAL_TOTAL_BACKGROUND=BLOCKED；PHYSICAL_SIGNIFICANCE／CLs=NOT_EVALUATED；PHOTON_FAKE_RATE=UNKNOWN；任何真正 parser、ME、積分或新事件仍需另行精確來源授權。
## 實際 bounded acquisition 與 static pair 驗證

root 已實際完成唯一選定 set 的 .info／member 0 取得，`acquisition_receipt.json` 狀態為 **PASS_COMPLETE_SELECTED_MEMBER_ACQUISITION**。HTTPS 憑證驗證開啟、來源與最終 URL 相同、沒有 redirect；advertised 與 received 長度逐檔一致。該 acquisition 收據記帳的選定 PDF response body 為 **685937 bytes**，低於 128 MiB；兩個單檔均低於 80 MiB。沒有取得 archive、其他 members 或第二個候選，沒有 installed-path writes。

| payload | bytes | 本次收到的 raw SHA-256 |
|---|---:|---|
| .info | 2345 | `85f3b2626de0896f45f5cfef53d90abd8d7b5ae784800b18d652e3f817431162` |
| member 0 .dat | 683592 | `e3055763f3a3154c2a2c6811d35e1f319a0bb38ff1c645c8db5cdc8bd210005e` |

上表 member hash 以 acquisition 收據實際值為準。工作區位於隔離的 `hh_phase12/run_01/public_pdf_01/NNPDF30_lo_as_0130_nf_4`，不是 MG5／conda 的 installed PDF directory。網路傳輸由既有 Windows Python 的正常 TLS client 執行，原始 bytes 經橋接保存於 WSL ext4；WSL HEAD 的 TLS timeout 沒有變成繞過憑證驗證的理由。這是 transport 路徑記錄，不是替正式來源增添 publisher signature。

候選報告作者另外對實際 .info／member header 呼叫 `inspect_local_pair`，得到 LOCAL_PAYLOAD_METADATA_AND_HEADER_CHECKED：metadata、central header、member overrides、4F flavour／alpha/reference 定義與上述 hashes 一致。這次是靜態檔案讀取，不是 native interpolation；native readback 另見 Phase12D 的實際程序／輸出。下載 grid 僅留本機，GitHub 不發布 .dat 或完整 PDF distribution。
