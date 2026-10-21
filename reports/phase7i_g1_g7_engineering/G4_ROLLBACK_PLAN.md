本文件為待獨立審查提案，不是執行授權。Exact source `83d1cda235e1d5fcc23f48d6a53065f88f2d1b1d`。未批准者保持BLOCKED；不得自行填假approval、降限制或改原始收據。

# Rollback與資料保護

未provision所以本輪不需要rollback。未來依exact attachment/provision receipt，只能回復此次新增的owned資源；先保存raw evidence並證明owned jobs已停，再由管理員批准解除/移除該新裝置。不得刪root/history、回收未知device、清journald、任意fsck/wipefs，或因error自動重試format。格式化前資料不可逆，因此disposable provenance必須在批准之前成立。
