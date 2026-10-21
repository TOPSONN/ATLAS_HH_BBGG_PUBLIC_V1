本文件為待獨立審查提案，不是執行授權。Exact source `83d1cda235e1d5fcc23f48d6a53065f88f2d1b1d`。未批准者保持BLOCKED；不得自行填假approval、降限制或改原始收據。

# Same-instance helper design及不可用介面

現有InertFDLease只消費regular-file fixture的同一FD；本run實際重測，沒有block device consumer。新preflight先拒FD/helper/lease改變，再沿用原四階段transaction policy；acquire→before_operation→after_operation→before_release需綁定host instance、major/minor、diskseq、capacity、FD、boot/ns、helper start、lease、device/mount政策digest及protected graph。

Linux6.6 get_tree_bdev由fc->source做lookup_bdev再取得superblock；不能由generic mount API存在FD參數，就宣稱ext4會消費我們持有的FD。這是上游source語義審查，不是本機WSL kernel已核實。傳/proc/self/fd/N給外部mkfs/mount也不等同已證明same-open-file-description與Windows排他。

最小可信helper還需要：in-process且受審的FD formatter、可核對的ext4 mount實例綁定、kernel exclusive block claim、跨host writer/hotplug排他lease、保持四階段FD及lease不中斷、收尾再釋放。相容libext2fs／mount方案目前未核實，不能虛構API。flock只管合作程序，不能代表Windows所有writer已排除。

替代管理員程序是先在獨立maintenance環境隔離專用裝置、提供排他與不可成長provenance，再另審consumer；若必須path-reopen或更改same-instance合約，需新的明確修約。沒有排他及consumer時format/mount一律BLOCKED。live_operation永遠拒絕；本PR不部署privileged helper。


來源語義：[Linux6.6 cgroup](https://www.kernel.org/doc/html/v6.6/admin-guide/cgroup-v2.html)、[systemd255 exec](https://www.freedesktop.org/software/systemd/man/255/systemd.exec.html)、[Linux6.6 get_tree_bdev](https://github.com/torvalds/linux/blob/v6.6/fs/super.c#L1448)、[mke2fs手冊](https://man7.org/linux/man-pages/man8/mke2fs.8.html)。這些是API/source審查，不是本機kernel版本或實機能力證明。
