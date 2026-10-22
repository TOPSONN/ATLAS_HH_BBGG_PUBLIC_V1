# 建議架構

推薦路徑為 **B-V2候選＋VM成本歸屬＋collector退出後的獨立observer**，仍為PROPOSED_NOT_ACCEPTED。理由是已有Linux介面觀察與source可重用，能明確設計一個job parent和受保護子域；不存在的joint host/VMM強保證不應由更多Python tests代替。

建議使用由一個受信manager管理的parent hierarchy；worker/controller與collector分開死亡子域，CPU/RAM使用共同parent counter和cap；external manager的final observer從外部確認collector已退出與parent空。若走delegation，必須service/scope與single-writer，不能Delegate=slice；不部署任何新unit或猜UID。

保留4固定seed、原CPU/wall/RAM/swap/disk、1job/1worker與0retained events。BUILD兩tmpfs不能同時滿載於2GiB；需先有可審resident模型及measurements，不能因此降限制或把shared page免費外移。S4通過也僅能是有限語義驗收，不能使原A FULL true。

本次建議不是使用者已接受，也不構成diagnostic、provision、format、mount、S4、BUILD_ONLY或physics approval。
