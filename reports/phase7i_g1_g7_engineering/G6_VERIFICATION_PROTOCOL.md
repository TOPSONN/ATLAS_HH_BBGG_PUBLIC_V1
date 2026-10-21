本文件為待獨立審查提案，不是執行授權。Exact source `83d1cda235e1d5fcc23f48d6a53065f88f2d1b1d`。未批准者保持BLOCKED；不得自行填假approval、降限制或改原始收據。

# Post-format independent verification

目前NOT_EXECUTED_DEPENDS_ON_G5。新parse_geometry_header接受有界、去重、明確欄位的dumpe2fs header，將raw SHA與fields分開；Total journal blocks缺失或工具版本拼法不同時拒絕，不猜值。geometry再對exact source-instance、fresh UUID/label、ext4/features、block size/count、inode count/size、internal journal、free blocks/inodes及8槽reserve交叉核對。

block_count*block_size是FS固定邊界，metadata、bitmap、inode table、internal journal在內，不應再加一次journal造成double counting；host backing/外層metadata則另計帳，不能消失。allocated st_blocks*512與inode硬限制需在已批准device作真實正反測試，包含正常reserve、block ENOSPC、inode ENOSPC、torn receipt、failure lane、再開啟驗證；本輪只fixture，未寫新FS。

fsync ACK及重開相等不是power loss測試。須另審device/host flush與durability失效模型；沒有實測則durability=null。parse出正確幾何也不是來源attestation或format批准。
