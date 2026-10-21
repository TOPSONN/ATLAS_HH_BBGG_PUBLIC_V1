本文件為待獨立審查提案，不是執行授權。Exact source `83d1cda235e1d5fcc23f48d6a53065f88f2d1b1d`。未批准者保持BLOCKED；不得自行填假approval、降限制或改原始收據。

# Formatting review packet

G4未完成且privileged consumer/host exclusivity未部署，G5_FORMAT_READY=false。不存在本次format授權或執行。

獨立批准必須包含exact source/device/lease/policies、disposable provenance、root/history與sibling排除、無host/guest writers或mount refs、fresh evidence位置、完整幾何、failure reserve及rollback。mke2fs -n只是不寫FS的工具模式，仍會開target，不能跳過same-instance審查；本輪沒有執行dry-run、dumpe2fs、mkfs或任何device讀寫。

候選4MiB、1KiB blocks、128 inodes、1MiB internal journal只是提案。上游手冊journal最少1024 filesystem blocks，不等於本機mke2fs一定能在此幾何建立成功。先核工具version/hash/features與reviewed dry-run，再同instance readback；任何不相容保持BLOCKED，不增加capacity、不去journal、不降inode要求、不加-F。


來源語義：[Linux6.6 cgroup](https://www.kernel.org/doc/html/v6.6/admin-guide/cgroup-v2.html)、[systemd255 exec](https://www.freedesktop.org/software/systemd/man/255/systemd.exec.html)、[Linux6.6 get_tree_bdev](https://github.com/torvalds/linux/blob/v6.6/fs/super.c#L1448)、[mke2fs手冊](https://man7.org/linux/man-pages/man8/mke2fs.8.html)。這些是API/source審查，不是本機kernel版本或實機能力證明。
