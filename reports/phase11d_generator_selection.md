# Phase11D：精確組件比較與選擇

本次結論為 **NONE_READY**。這是以實際安裝來源與必要參數逐欄檢查得到的結果；不是宣稱所有方法均不可行。4F 與 5F 各自已有確定的來源支持範圍，但仍沒有一個完整組件符合目前的 source-level configuration gate。沒有執行 MG5 parser、process generation、ME、積分或新事件。

## 兩個候選的不同問題

| 項目 | A：massive-bottom 4F | B：共同 5F aa+0/1/2 partons |
|---|---|---|
| 模型 restriction | sm/default，MB=4.7、MC=0；不是 unrestricted UFO 的MC=1.27 | sm-no_b_mass，MB=MC=0 |
| 初態 | 明列g,u,d,s,c及反粒子，排除b；4F不等於排除charm | 包含massless b/c，必須以一致PDF/alpha/shower定義處理 |
| hard order | 原卡QCD=2/QED=2是amplitude上限；power counting為alpha_s² alpha_EM²，parser未驗證 | 各multiplicity有QCD/QED上限；嚴格==等階另為未解析提案，tree family不含loop-induced gg→aa |
| PDF | 10個明確安裝搜尋範圍未找到可綁定的相容4F member；目錄索引不是grid | 有歷史5F grid不等於本family已選定member、threshold與alpha演化 |
| alpha_s | 必須綁PDF member/參考尺度/演化與backend；模型卡aS=.118不是選定PDF耦合 | ME/PDF/ISR/FSR及matching閾值尚未凍結 |
| photon IR | maxjetflavor4的LO smooth-cone和is_a_b/drab相互作用須明確定義 | maxjetflavor5涵蓋b/c，但smooth cone本身不解決額外QCD parton軟／共線問題 |
| matching | isolated LO+PS component仍須凍結shower；不需捏造merging scale | MLM/CKKW-L只有generic source支持，實際history、effective settings、weight closure未驗證 |
| 統一權重 | 原始source identity、sumW/sumW2、試次及cross-section error必須保存 | 除原始weight外還須處理native mergingWeight及multiplicity接受／拒絕正規化 |
| 現狀 | PDF/alpha、IR、cuts、scale、shower未閉合 | PDF/alpha、matching、IR、weights、highest-multiplicity未閉合 |

`phase11_compatibility_matrix.json` 將8項必要條件逐候選列出。每個必要項都有來源／理由，缺少任一項不能藉由一個 generic SOURCE_SUPPORTED 標籤跳過。原始模型restriction與generic介面已有確實文字證據，完整可執行組件仍未建立。

## 4F所缺的精確證據

需要實際可讀的4F member payload與.info、LHAID/member、各自SHA256、active-flavour與alpha threshold/reference-scale資料，以及已審查的MG5讀取／alpha_s backend路徑。CTEQ5F4在catalogue或commented backend中出現，不代表可呼叫的已安裝PDF；CTEQ6L1不能直接替代4F需求。允許fixed或經審查的variable-max4定義，但不能默認b activation或把模型pole mass視為PDF threshold。

公開NNPDF nf4 metadata反例說明，名為MZ/AlphaS_MZ的欄位可能以約4.18GeV作reference scale；不能把AlphaS數值自動解讀為91GeV處的耦合。這份公開metadata僅作適用性審查，並未下載member grid或選定該set。[官方metadata](https://lhapdfsets.web.cern.ch/current/NNPDF30_lo_as_0130_nf_4/NNPDF30_lo_as_0130_nf_4.info)

## 為何沒有選B來繞過缺件

B需要一致的0/1/2 multiplicity family。Pythia能表達某些photon core並不證明本process的history選擇、最高multiplicity、QCD/QED分工、fragmentation或flavour matching已閉合。MLM的header可覆寫effective merge/qCut/nQmatch；5F不能把nQmatch4時未matching的b稱為已matching。CKKW-L的額外merging weight也不能默默忽略或重複乘入。沒有numerical merging scale被選為validated值；FxFx不適用於把歷史LO樣本直接升格成NLO合併樣本。

## 必須保留的四種狀態

- SOURCE_SUPPORTED：限定到已雜湊的模型／cut／介面文字及其已列前提。
- PARSER_NOT_VALIDATED：這次沒有執行MG5，即使語法看來合理也不算parser通過。
- PHYSICAL_PILOT_NOT_EXECUTED：沒有真正物理pilot。
- MATCHING_NOT_VALIDATED：沒有matching/merging數值閉合。

合約中的massive4F「conditional review target」只用來聚焦缺件清單，**不是selected pilot**。精確parser/process-only request另列在config/parser_process_review_request.json，尚未授權；它也不能替代PDF、IR、matching與物理測量驗證。

## 現有資料不能改名成新組件

B01–3現有樣本的模型、初態、PS與原始權重保持原樣。ME outgoing、incoming heavy、shower births、direct splitting、hadron/native flavour與bit0是不同層級；incoming heavy的b/c須分清，因4F仍可含初態charm。現有3000事件的相關性／region migration只診斷歷史proposal，不能當作新的4F生成，也不能用shared reconstructed support證明ME/PS double counting。

結論：HEAVY_FLAVOUR_GENERATOR_EXCLUSIVITY=UNVERIFIED；PHYSICAL_TOTAL_BACKGROUND=BLOCKED。下一步是逐項審查缺件，不自動下載／安裝PDF、不執行卡、不開始pilot。

## 精確初態b/c既有LHE讀回

另行實際串流讀取原始B01–3共3000筆LHE，與原始index、HepMC event-id、native/origin及權重逐筆join：

| 來源 | incoming bottom | incoming charm、無bottom | p4初態PDG-domain可容許 |
|---|---:|---:|---:|
| B01 |25|33|975|
| B02 |2|67|998|
| B03 |0|6|1000|

所以舊combined initial-HF的58／69／6不能都叫incoming bottom；B03的6全是charm。p4-domain只是alias物種條件，未檢查4F PDF、mass、alpha或新ME，不能拿975／998／1000個事件重標為物理4F sample。新400列stage、1395列covariance及3000個原始source identity是歷史診斷，沒有新hard events或物理總和。

## 最終外部來源身分阻擋

A02 在稽核當下的 before/after 相同，不保證之後外部檔案仍相同。最終重讀發現已安裝 MG5 `input/mg5_configuration.txt` 從 9212 bytes、SHA256 `83d48923f215d20565931e8e0eb6ee986b34658d0bbe6f2e7a75e0400b4d7f85`，變成 9239 bytes、`9132f5ddcab8eb45ee00830d3ed9b7582bda67058180288d3f93222a96f74506`，再變成 9266 bytes、`82a6d1943d0acd139704910dfd0510ee2bd86d06f94a410b5f28e68a45bc3f5a`。在記憶體逆向移除三個設定行的註解 padding 與其空白行，可精確重建前兩個雜湊；有效設定相同。這是經雜湊核對的重建，不是找到磁碟備份，也不等同原始位元組凍結。已安裝檔案沒有被本工作回復或改寫。

MG5 `extended_cmd.py` 的 option serializer 可重現同樣的空白變化，但實際呼叫者 **UNKNOWN**，不能據此推定何人或何工作執行 MG5。本次受登錄工作沒有 generator dispatch；外部 host 全歷史活動並未受完整稽核。最新 gate 必須重算外部原始 SHA，漂移時明確標示 `BLOCKED_EXTERNAL_RUNTIME_CONFIGURATION_DRIFT`，不能只沿用 A02 收據或先正規化空白。這與 2874 個受監測歷史檔案保存全部通過是不同範圍。
