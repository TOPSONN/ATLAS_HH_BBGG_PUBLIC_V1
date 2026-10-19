# Phase11F：有界pilot合約及執行邊界

**INACTIVE_REVIEW_ONLY；NONE_READY；PILOT_APPROVAL=NOT_AUTHORIZED。** 所有實際新ME、integral、hard/Pythia/Delphes events為0。沒有generator dispatcher，沒有可用來跳過審查的approval override flag。合約位於analysis/phase11/config/bounded_pilot_contract.json；結構schema及Python科學policy另有負向測試。

## 已具體固定與仍為null的欄位

來源審查固定MG5 3.5.16、Pythia8.317、既有sm/default或sm-no_b_mass的限制語義、process文字、LO耦合階數、cut及matching介面的實際程式位置。這些facts有檔案SHA256與行號，不能只以版本字串代替exact source identity。

沒有完整可用組件，因此future executable source revision、PDF/member/flavour binding、alpha_s/reference scale/thresholds、photon IR數值、generation cuts、hard scale、shower settings均為null/BLOCKED。這些null不能改成0、空物件或historical default。未來精確source revision還需獨立審查與明確授權，不能把本次base或先前Phase7I批准移作新pilot批准。

## 資源：提案與批准分開

| 項目 | 既有Phase10未核准示例 | 本次批准／enforcement |
|---|---:|---|
| threads | 2 | approved=null，UNVERIFIED |
| wall | 7200s | approved=null，UNVERIFIED |
| RAM | 4GiB | approved=null，UNVERIFIED |
| disk | 2GiB | approved=null，UNVERIFIED |
| total new hard events | 1000 | approved=null，UNVERIFIED |
| scan points | 3 | approved=null，UNVERIFIED |
| ME evaluations | 1000000 | approved=null，UNVERIFIED |
| integration cycles | 20 | approved=null，UNVERIFIED |
| event trials | 100000 | approved=null，UNVERIFIED |
| aggregate CPU | null/BLOCKED | 沒有凍結；不能由threads×wall推定批准 |

本次source/existing-data jobs另使用既有Phase8 execute()監控器：單job／worker、4h aggregate CPU／job-wall、build/results額外2GiB。這是Phase11來源分析的保守容器，與任何未來物理pilot／Phase7I預算無關。其process-group CPU／wall／disk監控及TERM/KILL不等於硬性job RAM保證，也未提供native ME/trial/cycle全域上限。Kernel存在cgroup controller不代表使用者已獲per-job delegation。這些差別在phase11_pilot_readiness.json明列，不能將UNVERIFIED標成ENFORCED。

## 原始事件、權重及正規化

未來原始source key至少含dataset UUID、原始ordinal及hard-event SHA256。保留LHE IDWTUP/XWGTUP/SCALUP、原始與選後signed sumW/sumW2、native Pythia與merging weights、接受／拒絕／veto及所有試次。若interface定義combined weight，需用實際source/writer閉合確認只作用一次。

統計單位是原始獨立source event，所有未通過選取的0貢獻仍留在原始N。負權重不能丟棄；signed sumW=0時relative precision未定義而非0。`signed_source_statistics`只有代數方法及負向fixtures，沒有宣稱未來signed generator interface已驗證。BR亦需按確定的decay約定只作用一次。不得將B01+B02+B03相加成物理總背景。

## Integration與停止條件

未來真正授權後，需報告survey/refine grids、實際seed/PDF/alpha/scales、integration error、獨立replica dispersion、ME calls、candidate trials、accept/reject/veto、unweighting效率與truncation。完成run不自動證明convergence。

以下任一項即停止：source/grid/card hash不符、PDF/alpha/IR/weight不相容、使用未審merging scale、失去原始source denominator、counter無法量測或cap到達、科學gate失敗、非預期輸出、歷史覆寫或未批准圖件。不可補跑failed replica、增加seeds／runtime／disk或擴張scope。必須使用另外核對的新輸出目錄。

## 獨立parser/process請求

config/parser_process_review_request.json只提議原始massive4F model/alias/generate三行的解析／process-code審查；沒有launch/check數值ME/integration/events命令。300s CPU／wall、1job／worker／thread、2GiB RAM／256MiB disk亦只是待審提案，approved_limits=null。其exact execution revision與enforcement尚未批准；本次沒有執行該request。

## 科學gates

HF origin診斷維持VALIDATED_WITH_LIMITS；generator exclusivity=UNVERIFIED；photon fake=UNKNOWN；signal normalization=BLOCKED_PHASE7I；physical total=BLOCKED；significance/CLs/κ interval=NOT_EVALUATED。未來增加pre-isolation branch只補觀測母群，不提供ATLAS tight/anti-tight shower shapes、conversion或calibration。所有未知nuisance與covariance保留null，合成方法通過不解除上述blockers。

沒有外部獨立人類review簽核。本次代理的不同實作、Fraction/covariance計算與負向測試提供來源／方法證據；不等同人類物理批准。

## 最終外部來源身分阻擋

A02 在稽核當下的 before/after 相同，不保證之後外部檔案仍相同。最終重讀發現已安裝 MG5 `input/mg5_configuration.txt` 從 9212 bytes、SHA256 `83d48923f215d20565931e8e0eb6ee986b34658d0bbe6f2e7a75e0400b4d7f85`，變成 9239 bytes、`9132f5ddcab8eb45ee00830d3ed9b7582bda67058180288d3f93222a96f74506`，再變成 9266 bytes、`82a6d1943d0acd139704910dfd0510ee2bd86d06f94a410b5f28e68a45bc3f5a`。在記憶體逆向移除三個設定行的註解 padding 與其空白行，可精確重建前兩個雜湊；有效設定相同。這是經雜湊核對的重建，不是找到磁碟備份，也不等同原始位元組凍結。已安裝檔案沒有被本工作回復或改寫。

MG5 `extended_cmd.py` 的 option serializer 可重現同樣的空白變化，但實際呼叫者 **UNKNOWN**，不能據此推定何人或何工作執行 MG5。本次受登錄工作沒有 generator dispatch；外部 host 全歷史活動並未受完整稽核。最新 gate 必須重算外部原始 SHA，漂移時明確標示 `BLOCKED_EXTERNAL_RUNTIME_CONFIGURATION_DRIFT`，不能只沿用 A02 收據或先正規化空白。這與 2874 個受監測歷史檔案保存全部通過是不同範圍。
