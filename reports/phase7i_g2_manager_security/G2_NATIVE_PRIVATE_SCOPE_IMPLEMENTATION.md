# Native scope實作與驗證界線

manager_scope_fs.py用完整ancestor dirfd鏈、O_DIRECTORY/O_NOFOLLOW與lstat/fstat身分核對，拒絕其他使用者可寫祖先。final私有dir需owner UID1000、0700；scope0600、source0400、regular file、nlink1。以fstatfs magic、proc fdinfo mount_id、精確mountinfo/device/fsid與mount namespace identity核對外部已審filesystem contract；只接受ext4。9p/DrvFS與unknown類型不會因path/chmod變成PASS。

getxattr在同FD讀access/default POSIX ACL；非空拒絕，unsupported/permission錯誤保持UNKNOWN。openat以固定單一basename開scope，bounded read在同FD計SHA；比對pre/post dev/inode/owner/mode/nlink/size/mtime/ctime及dirfd lookup，dispatch前再驗bytes。exclusive-create不覆寫；建立失敗保留檔案，不自行修chmod或重試。ordinary fsync不是WORM或power-loss證明。[open/openat](https://man7.org/linux/man-pages/man2/open.2.html)、[POSIX ACL](https://man7.org/linux/man-pages/man5/acl.5.html)。

本機沒有建立候選ext4 scope/source目錄，也沒有取得實際fsid/mount/namespace/dir inode；所有實測值null。Native CI只能證明它自己的普通fixture檔案行為，不是WSL部署。root、Windows host administrator、WSL控制面與同UID高權限侵入並未被排除。固定依賴／dynamic resolution仍BLOCKED，即使檔案allowlist相符也不能dispatch manager。
