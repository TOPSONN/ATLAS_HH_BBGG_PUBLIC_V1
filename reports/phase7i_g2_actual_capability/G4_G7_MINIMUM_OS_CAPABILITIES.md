# Minimum deployable OS capabilities

G4：需要真正可拋棄、固定容量、whole-device、獨立host backing、完整root/history排除、stable host↔guest identity與all-writer exclusion。WSL官方支援管理員attach未被使用的whole disk，不能attach Windows安裝盤；這只證明API路徑，不證明本機有合格裝置或lease。[WSL](https://learn.microsoft.com/en-us/windows/wsl/wsl2-mount-disk)。不選目前任何Windows/Ubuntu disk，不提供猜target的可執行format/mount命令。

G5：4MiB、1KiB blocks、128 inodes、1MiB internal journal的核心幾何在e2fsprogs1.47.0 source下可相容：4096 blocks的default journal為1024 blocks，JBD2 minimum亦1024。inode table為32KiB，journal與metadata包含在4MiB內。這不是實際mke2fs執行；features、fast_commit/orphan_file、mke2fs.conf、工具build與精確free blocks/inodes尚待固定與readback，不能省略配置或擴大device讓測試綠。[journal sizing](https://raw.githubusercontent.com/tytso/e2fsprogs/v1.47.0/lib/ext2fs/mkjournal.c)、[JBD](https://raw.githubusercontent.com/tytso/e2fsprogs/v1.47.0/lib/ext2fs/kernel-jbd.h)。

G6：保留既有geometry/header pure verifier。未來須固定device instance與UUID，核實FS block_count×block_size、allocated backing而非sparse logical length、inodes、internal journal、兩failure lanes與32KiB slots reserve；正常/block/inode ENOSPC/torn/reopen等獨立實測。fsync ACK不等於power-loss durability，outer device/host flush boundary需另審。真正FS與readback目前均無新增。

G7：一個manager/單writer、合法delegation、專用parent及子域、protected collector UID/FD、swap0/effective ancestors、bounded stdout/manager logs、post-collector observer、完整cleanup、capacity與failure slots缺一不可。不得只用LogNamespace或user-session存在推斷整個control plane已受限。維持無service啟動argv、無mount、無collector deployment。
