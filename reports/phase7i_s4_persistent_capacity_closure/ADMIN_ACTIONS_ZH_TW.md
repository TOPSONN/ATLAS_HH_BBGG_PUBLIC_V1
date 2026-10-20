# 持久容量後端：管理員操作提案

狀態：PROPOSAL_ONLY／BLOCKED。本文沒有執行格式化、掛載、quota 修改、S4、資源壓測或正式 build，也不構成人類授權。尚未取得新專用裝置的精確身分，因此下列命令包含必須另審的裝置識別值；未填入時必須中止，不能改用目前的根裝置。

## 已確認的現況

本輪 /home 的 ext4 是 /dev/sdd、8:48，虛擬 block device 為 1 TiB，與既有 source、資料及系統 journal 共用。六次 GETFMT／GETINFO 對 user、group、project 均回 ESRCH，對應目前沒有 active accounting。這項判斷依實際回傳值與匹配版本的核心來源，不依缺少 quota 工具或 mount 旗標。superblock 讀取被權限拒絕，quota／project feature 仍 UNKNOWN。

原九次查詢中另含三次 GETQUOTA，核心將這個名稱為 GET 的操作列為可能配置 dquot 的 write-class；本次 user／group 回 ESRCH，project 回 EPERM。原始紀錄完整保留，沒有成功 buffer 值可解讀。後續唯讀方案只允許 GETFMT／GETINFO。錯誤路徑來源核對與限制另見 quota_get_corrective_audit_01.json。

控制平面的實際調查發現 journald、rsyslog、user manager 與 journal／syslog 輸出仍涉及共用根檔案系統。這裡的新 volume 只能包住自己的 blocks、inodes、metadata 與內部 journal；不能宣稱已包住那些外部寫入。不能以更改全域 journald Storage、rotation 或清除歷史 logs 處理本任務。

## 選定的最小後端及總額

選定「管理員另外供應、不可成長、非 thin／sparse 的專用 block device」，不修改現有根 ext4 的 quota feature，也不在線 remount 根系統。裝置不可讓受測 worker 開啟 raw device、resize、建立新 mount 或改變 inode pool。

| 用途 | 專用裝置 | FS block | inode 提案上限 | 內部 journal 提案 | 保留的 tmpfs | 已知總額 | 仍未強制封閉的餘額 |
|---|---:|---:|---:|---:|---:|---:|---:|
| S4 inert | 4 MiB | 1 KiB | 128 | 1 MiB，含於 4 MiB | 8＋1 MiB | 13 MiB | 3 MiB |
| 未來 BUILD_ONLY 提案 | 2 GiB | 4 KiB | 32768 | 32 MiB，含於 2 GiB | 2 GiB＋256 MiB | 4.25 GiB | 768 MiB |

餘額只有算術，沒有 OS hard limit；因此兩列目前都不能通過 aggregate persistent capacity。不能把未來 persistent volume 設為 4 GiB：既有 build profile 的 tmpfs 已占 2.25 GiB，會超出 5 GiB。既有 CPU／wall／RAM／swap／job／worker 設定不變，這份幾何提案也沒有變更 profile。

4 MiB ext4 的可用 data 空間小於 4 MiB；journal、inode table、bitmaps、superblocks、lost+found 都在其內。格式化工具的實際 readback 若不符合提案、不能配置指定 journal，立即 STOP，不能默默取消 journal、放大 volume 或改用根目錄。mke2fs 的 -N 是要求值，必須由 superblock 及 statvfs 核對實際 inode 數。上述幾何尚未建立或實跑。

## 管理員必須先提供的證據

需另行核准一個全新裝置：穩定 by-id、解析後絕對路徑、major:minor、容量、底層 ancestry、非 thin／snapshot／sparse 證明、可寫入範圍及對 host 的影響。不能用本文的示例名稱代替這些證據，也不能對 /dev/sdd 或其父／子／同源裝置操作。

若只能提供 loop image，內層固定長度與 fallocate 成功仍不足：還要對外層檔案系統實際配置的 blocks／extents、inode、metadata、journal 及控制平面有可驗證 hard bound。truncate／sparse image、du 的單次數值、固定 FD 數量或邏輯 byte cap 都不符合這項條件。這個替代路線目前未選用，也沒有在本輪建立 image／loop。

WSL 附加實體磁碟通常需要 Windows 管理員權限。實際 host device 必須另外識別及核准；本文不猜測 PHYSICALDRIVE 編號，也不將 Ubuntu 本身的 VHD 當新空白磁碟。參考：[Microsoft WSL 磁碟文件](https://learn.microsoft.com/en-us/windows/wsl/wsl2-mount-disk)。

## S4 專用新裝置的命令提案

以下內容只供精確審查，尚未授權執行。第一段提供兩階段的唯讀 guard：格式化前必須是空白裝置，掛載前必須符合格式化後另審的新 ext4 身分；命令中沒有 sudo、自動套用、授權字串或自動選取空白磁碟。HH_EXPECTED_MM 未由管理員實際證據填入時，程式會中止。new mountpoint 本身也會使用 host inode，必須列入 provisioning 的影響與後續 controller 邊界。

先由管理員另審並提供新裝置的 root:root／0600 raw-device 權限證據；目前尚無這個新裝置，權限狀態 UNKNOWN。不能自動 chmod 任何現有裝置。若這項前置條件未滿足，下面 guard 會中止，須另外核對特定新裝置後才可提出其 chown／chmod 操作。

```bash
set -eu
export LC_ALL=C
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
HH_DEVICE_LINK=/dev/disk/by-id/HH7I_S4_NEW_FIXED_DEVICE
HH_EXPECTED_MM=REPLACE_WITH_REVIEWED_MAJOR_MINOR
HH_EXPECTED_BYTES=4194304
HH_MOUNT=/srv/atlas-hh/s4-capacity-v1
HH_DEV="$(/usr/bin/readlink -e -- "$HH_DEVICE_LINK")"
export HH_DEV HH_EXPECTED_MM HH_EXPECTED_BYTES HH_MOUNT

hh_readonly_guard() {
/usr/bin/python3 -I -B - <<'PY_GUARD'
import hashlib, json, os, re, stat, subprocess
from pathlib import Path
def need(ok, reason):
    if not ok:
        raise SystemExit('STOP: '+reason)
dev = os.environ['HH_DEV']
expected = os.environ['HH_EXPECTED_MM']
stage = os.environ['HH_GUARD_STAGE']
need(stage in ('PRE_FORMAT_BLANK','PRE_MOUNT_NEW_EXT4'), 'unreviewed guard stage')
need(re.fullmatch(r'[0-9]+:[0-9]+', expected) is not None, 'exact reviewed identity absent')
need(Path(dev).is_absolute() and dev.startswith('/dev/') and
     Path(dev).resolve().as_posix() == dev, 'absolute canonical device required')
info = os.stat(dev)
need(stat.S_ISBLK(info.st_mode), 'not a block device')
actual = f'{os.major(info.st_rdev)}:{os.minor(info.st_rdev)}'
need(actual == expected, 'device changed')
need(info.st_uid == 0 and info.st_gid == 0 and stat.S_IMODE(info.st_mode) == 0o600,
     'raw-device root:root0600 prerequisite not established')
root = os.stat('/').st_dev
root_mm = f'{os.major(root)}:{os.minor(root)}'
chain = subprocess.check_output(['/usr/bin/lsblk','-s','-r','-n','-o','MAJ:MIN',dev], text=True).splitlines()
need(root_mm not in chain and actual != root_mm, 'root ancestry')
state = json.loads(subprocess.check_output(
    ['/usr/bin/lsblk','-J','-b','-o','PATH,MAJ:MIN,SIZE,TYPE,MOUNTPOINTS',dev], text=True))
rows = state['blockdevices']
need(len(rows) == 1 and not rows[0].get('children'), 'nested partition or holder')
need(not any(rows[0].get('mountpoints') or []), 'already mounted')
need(rows[0]['size'] == int(os.environ['HH_EXPECTED_BYTES']), 'size differs')
need(subprocess.run(['/usr/bin/findmnt','-r','-n','-S',dev],
                    stdout=subprocess.DEVNULL).returncode == 1, 'mounted or query failed')
mount = Path(os.environ['HH_MOUNT'])
need(mount.as_posix() == '/srv/atlas-hh/s4-capacity-v1', 'fixed absolute mountpoint')
for ancestor in reversed((mount,*mount.parents)):
    need(not ancestor.is_symlink(), 'symlink in mountpoint ancestry')
    if ancestor.exists():
        st = ancestor.stat()
        need(ancestor.is_dir() and st.st_uid == 0 and
             stat.S_IMODE(st.st_mode) & 0o022 == 0,
             'ancestor must be root-owned and not group/world writable')
if mount.exists():
    st = mount.stat()
    need(st.st_uid == 0 and st.st_gid == 0 and stat.S_IMODE(st.st_mode) == 0o700 and
         not any(mount.iterdir()), 'existing leaf must be empty root:root0700')
if stage == 'PRE_FORMAT_BLANK':
    signatures = json.loads(subprocess.check_output(
        ['/usr/sbin/wipefs','--no-act','--json',dev], text=True))
    need(type(signatures) is dict and signatures.get('signatures') == [], 'existing signature')
else:
    uuid = os.environ['HH_EXPECTED_NEW_UUID']
    expected_header = os.environ['HH_EXPECTED_NEW_SUPERBLOCK_SHA256']
    need(re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}',uuid) is not None,
         'reviewed post-format UUID absent')
    need(re.fullmatch(r'[0-9a-f]{64}',expected_header) is not None,
         'reviewed post-format header hash absent')
    probe = subprocess.check_output(['/usr/sbin/blkid','-p','-o','export',dev],text=True)
    fields = dict(line.split('=',1) for line in probe.splitlines() if '=' in line)
    need(fields.get('TYPE') == 'ext4' and fields.get('LABEL') == 'HH7I_S4_V1' and
         fields.get('UUID') == uuid, 'expected newly-created ext4 identity differs')
    header = subprocess.check_output(['/usr/sbin/dumpe2fs','-h',dev])
    need(len(header) <= 16384 and hashlib.sha256(header).hexdigest() == expected_header,
         'post-format superblock readback differs')
    text = header.decode('utf-8','strict')
    for key,value in [('Block count',4096),('Block size',1024),('Inode count',128),('Inode size',256)]:
        values = re.findall(r'^'+re.escape(key)+r':\s+([0-9]+)\s*$',text,re.M)
        need(values == [str(value)], 'exact '+key+' differs')
    need(re.search(r'^Filesystem features:.*\bhas_journal\b',text,re.M) is not None,
         'internal journal feature absent')
print('READ_ONLY_DEVICE_GUARD_ONLY:'+stage)
PY_GUARD
}
export HH_GUARD_STAGE=PRE_FORMAT_BLANK
hh_readonly_guard
/usr/sbin/mke2fs -n -t ext4 -b 1024 -I 256 -N 128 -m 0 \
  -O none,has_journal,extent,filetype,sparse_super,dir_index \
  -J size=1 -E lazy_itable_init=0,lazy_journal_init=0,nodiscard \
  -L HH7I_S4_V1 "$HH_DEV" 4096
```

PRE_FORMAT_BLANK 必須在格式化前通過，存在任何 signature 一律中止；不得對既有 filesystem 格式化。只有管理員確認身分、空白簽章、非 thin ancestry 及 dry-run 佈局，且取得另一次明確核准後，才考慮下一行破壞性新裝置格式化。不能加 -F、-FF 或自動回答提示。

```bash
export HH_GUARD_STAGE=PRE_FORMAT_BLANK
hh_readonly_guard
/usr/sbin/mke2fs -t ext4 -b 1024 -I 256 -N 128 -m 0 \
  -O none,has_journal,extent,filetype,sparse_super,dir_index \
  -J size=1 -E lazy_itable_init=0,lazy_journal_init=0,nodiscard \
  -L HH7I_S4_V1 "$HH_DEV" 4096
```

格式化後先停止。下面僅讀回新 UUID、label、geometry 與完整 header digest，保存有身分綁定的 post-format 收據並另外審查；本輪沒有這份新裝置收據。不能重新執行 blank guard，也不能略過所有 guard 直接 mount。

```bash
/usr/sbin/blkid -p -o export "$HH_DEV"
/usr/sbin/dumpe2fs -h "$HH_DEV"
/usr/sbin/dumpe2fs -h "$HH_DEV" | /usr/bin/sha256sum
```

只有審查後的新 UUID／header SHA256 已明確填入，PRE_MOUNT_NEW_EXT4 才可能通過。此階段核對同一個未掛載新裝置的身分、精確新 ext4 UUID／label／geometry／header 與所有 mountpoint ancestors；它不要求新 filesystem 為空白簽章。建立 mountpoint 後再核對其 root:root0700 與空目錄狀態，才可另授權 mount。

```bash
export HH_EXPECTED_NEW_UUID=REPLACE_WITH_REVIEWED_NEW_UUID
export HH_EXPECTED_NEW_SUPERBLOCK_SHA256=REPLACE_WITH_REVIEWED_HEADER_SHA256
export HH_GUARD_STAGE=PRE_MOUNT_NEW_EXT4
hh_readonly_guard
/usr/bin/install -d -m 0700 -o root -g root "$HH_MOUNT"
hh_readonly_guard
/usr/bin/mount -t ext4 -o nodev,nosuid,noexec,errors=remount-ro "$HH_DEV" "$HH_MOUNT"
```

這段沒有建立 fstab、啟動 service、修改 journald／rsyslog、調整根 quota 或啟動 fixture。noexec 是 S4 的 inert 限制；不能直接套用於需要執行編譯結果的未來 build。未來 2 GiB 路線須以另一個新裝置、另審 exact command；幾何候選為 4096-byte blocks、524288 blocks、32768 inodes、32 MiB 內部 journal，不自動產生執行命令。

## 建立後的唯讀驗證與失敗證據

另一次授權建立後，至少保留以下原始輸出與 SHA256，並與裝置 readback、source revision、完整 mount capture 綁定。以下亦未在本輪執行。

```bash
/usr/sbin/blockdev --getsize64 "$HH_DEV"
/usr/sbin/dumpe2fs -h "$HH_DEV"
/usr/bin/findmnt -J -T "$HH_MOUNT" -o TARGET,SOURCE,FSTYPE,OPTIONS,FSROOT,MAJ:MIN
/usr/bin/stat -f -c 'type=%T block=%S blocks=%b free=%f inodes=%c ifree=%d' "$HH_MOUNT"
```

必須核對整個固定裝置，不能只計 data payload：superblock／group descriptor、inode table、bitmaps、extent／directory／xattr metadata、內部 journal 都須在這個裝置內，沒有外部 journal、thin growth、可用 resize API、worker raw-device FD 或其他未計寫入路徑。內部有限空間只能證明自身 volume 上限，不能證明外部 host filesystem 或日誌上限。

後續 bounded receipt 可採同 controller 的固定 slots／固定大小、先配置後開啟、明確限制 offset 的 FD；worker 不繼承 evidence writer FD，也不能 unlink、truncate、punch-hole 或改名失敗收據。需真正驗證預配置 blocks、inode、metadata／fsync 行為及 block/inode ENOSPC 後仍可更新已配置區域。現在只有 source 提案，沒有這個 durable writer 的實跑結果。controller 死亡後只能保存先前已同步的 checkpoint，不能聲稱死亡後仍生成新的成功收據。

控制平面待辦：stdout／stderr=null 與 volatile pipe 的提案須另審；systemd manager、journald、rsyslog 及 kernel 記錄的外部配置仍需可靠 hard limit。3 MiB 或 768 MiB reserve 不可當成 enforcement。外部路徑未封閉前，persistent_capacity、controller-loss acceptance 與 FULL 均維持 BLOCKED。

## 未來另外授權的測試與回復

需分開核准並實跑正常固定輸出、block ENOSPC、inode ENOSPC、file-size overflow、metadata／directory／xattr 壓力、sparse／fallocate／punch-hole／link／rename bypass、漏繼承 FD、controller 及 child 異常退出、kill 後殘留程序與既有 checkpoint 完整性。每案有固定 CPU／wall／RAM／disk 範圍，原歷史失敗不得覆蓋；不能因失敗自動換案、放大容量或改用 root。

回復只針對經核對的新 mount：先確認沒有執行中的 writer，保存失敗收據與裝置身分，核對 findmnt 指向同一個 HH_DEV，再由另行授權的管理員執行 umount。失敗時保留現場，不 lazy-unmount、不 recursive delete、不重新格式化。保留新裝置以供鑑識，不自動刪除 image、解除 host disk 或變更既有 PR／樣本。

```bash
/usr/bin/findmnt -J -T "$HH_MOUNT" -o TARGET,SOURCE,FSTYPE,MAJ:MIN
# 確認 writer 已停止、裝置仍相同並保留收據後，才可另授權：
/usr/bin/umount -- "$HH_MOUNT"
```

## 來源與判定限制

- [Microsoft WSL 6.6.87.2 quota.c](https://github.com/microsoft/WSL2-Linux-Kernel/blob/linux-msft-wsl-6.6.87.2/fs/quota/quota.c)：GET 分類、權限及 inactive errno。
- [相同版本 dquot.c](https://github.com/microsoft/WSL2-Linux-Kernel/blob/linux-msft-wsl-6.6.87.2/fs/quota/dquot.c) 與 [ext4/super.c](https://github.com/microsoft/WSL2-Linux-Kernel/blob/linux-msft-wsl-6.6.87.2/fs/ext4/super.c)：失敗路徑及 ext4 dispatch。
- [Linux quota 文件](https://www.kernel.org/doc/html/latest/filesystems/quota.html)：block 與 inode quota 邊界。
- [mke2fs](https://man7.org/linux/man-pages/man8/mke2fs.8.html)：-n、-N、block／inode size、內部 journal 與初始化選項。
- [ext4 journal](https://www.kernel.org/doc/html/latest/filesystems/ext4/journal.html)：journal 屬於檔案系統的實體空間。
- [quotactl](https://man7.org/linux/man-pages/man2/quotactl.2.html)：O_PATH filesystem descriptor 與 errno 的使用介面。

最終判定：管理員新專用 block device 是可審查的最小方向；目前沒有已驗證的完整持久容量後端，尚不能執行 S4 或正式 build。
