本文件為待獨立審查提案，不是執行授權。Exact source `83d1cda235e1d5fcc23f48d6a53065f88f2d1b1d`。未批准者保持BLOCKED；不得自行填假approval、降限制或改原始收據。

# Format stop rules

device/FD/namespace/boot/diskseq/helper/lease/policy任何漂移、排他失效、額外writer、target已mount、root/history關聯、來源/工具hash不符、幾何不支援、evidence reserve不足、approval scope不符或任何輸出/資源異常均STOP。保留全部原始收據，不自動重試，不換target，不提高容量，不改FS，不補假approval。
