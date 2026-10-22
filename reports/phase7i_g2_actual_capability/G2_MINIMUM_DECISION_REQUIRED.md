# 最小使用者決策（不在本次要求執行）

先決定是否願意逐條審核較弱的B-V2語義：允許明列external非零成本、普通scheduler的早停／overrun拒絕，以及memory.max的暫態語義。若不接受，原A維持，不部署WSL候選。

需要明確綁定的三份原件SHA256：

- B1–B8 terms：`c01968bda61e705c25cca774372572ad8b5efb221451db21ba33c21b77682193`。
- VM cost assignment：`eedc17a761f2aaefde628d858a70bf9d4518d271df8bedcaf54f34d96cf6237d`。
- Post-exit observer supplement：`fcbfba8c4dececd545b4f75a852a7ec4b123d67078a038d03d85772c5076364b`。

附件terms引用只有57字元，不能作SHA256批准binding；以上是原件與既有assignment相互核對的完整hash，沒有修改條款。B1–B8逐條decision、VM assignment與observer均仍NOT_ACCEPTED；任何單一含糊回覆不能自動補滿所有欄位，更不能產生approval token。

架構接受前尚需處理guest異步filesystem/journal CPU是否完整歸帳；不能把fixed-device容量當作此CPU證明，也不自行排除新角色。如現有三份條款不能表達實際成本，先精確審查所需補充，不修改舊條款、不自動接受。

下一個可審scope可先是單次、非管理員、唯讀的effective manager/delegation/tool identity診斷，僅收集決策資訊，不要求先接受B。現在不執行，也不啟動WSL；精確proposal見G2_EFFECTIVE_STATE_DIAGNOSTIC_PROPOSAL.json，尚缺tool binary identity而不是execution-ready。之後device provision/format/mount、kernel正常與故障測試、S4、正式build、binary binding與物理restart各自另審。
