本文件為待獨立審查提案，不是執行授權。Exact source `83d1cda235e1d5fcc23f48d6a53065f88f2d1b1d`。未批准者保持BLOCKED；不得自行填假approval、降限制或改原始收據。

# B-V2逐條決策

本文件為待獨立審查提案，不是執行授權。Exact source `83d1cda235e1d5fcc23f48d6a53065f88f2d1b1d`。未批准者保持BLOCKED；不得自行填假approval、降限制或改原始收據。

原terms raw SHA `c01968bda61e705c25cca774372572ad8b5efb221451db21ba33c21b77682193`；VM成本assignment raw SHA `eedc17a761f2aaefde628d858a70bf9d4518d271df8bedcaf54f34d96cf6237d`；新post-exit observer supplement SHA `fcbfba8c4dececd545b4f75a852a7ec4b123d67078a038d03d85772c5076364b`。三者均PROPOSED_NOT_ACCEPTED，原候選檔不改。

| 條款 | 審查結論與需要的人類決定 |
|---|---|
| B1 | 建議審查單一job parent包含worker/controller/collector/helpers；manager_journal、launcher、host_backing是明示external nonzero costs。VM/hypervisor residual歸host_backing屬較弱邊界，須明確接受。最後post-collector observer另提版本化supplement，歸manager_journal，不免費。 |
| B2 | cpu.max只提供rate；保留累積usage/user/system及early-stop介面，actual overrun FAIL，缺counter UNKNOWN，無零排程延遲承諾。 |
| B3 | admission到collector完成且owned group空的獨立readback，以可信時鐘保存上界；Main-origin不夠，普通scheduler可延遲。 |
| B4 | 接受Linux memory.max標準階層語義與swap.max=0；保留peak/events/OOM，不承諾literal零瞬時超額。 |
| B5 | 獨立可拋棄fixed-capacity whole-device及真實allocated blocks/inodes，metadata/journal在內。root/shared/thin/sparse/unknown loop不接受。 |
| B6 | collector與worker/controller分死亡域，仍同parent計帳；8x4096 slots，failure reserve2槽。外層/collector/host死後只剩已有checkpoint，未測durability保持UNKNOWN。 |
| B7 | 需驗cgroup空及無owned descendants。collector不能證明自己的post-exit狀態；需獨立final observer。unit消失不是cleanup成功。 |
| B8 | 各條款接受後仍需個別device/provision/format/mount/kernel/S4/build批准，source或CI不能解鎖。 |

每條記錄ACCEPT／REJECT／需修改，不能一個布林值默認整批接受。原A結果與限額不變，B不改名為原A FULL PASS。


來源語義：[Linux6.6 cgroup](https://www.kernel.org/doc/html/v6.6/admin-guide/cgroup-v2.html)、[systemd255 exec](https://www.freedesktop.org/software/systemd/man/255/systemd.exec.html)、[Linux6.6 get_tree_bdev](https://github.com/torvalds/linux/blob/v6.6/fs/super.c#L1448)、[mke2fs手冊](https://man7.org/linux/man-pages/man8/mke2fs.8.html)。這些是API/source審查，不是本機kernel版本或實機能力證明。
