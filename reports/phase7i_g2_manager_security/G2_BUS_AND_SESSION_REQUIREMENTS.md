# Bus與Session條件

既存system socket預期root owner，user systemd/private預期UID1000；需safe ancestors、型別、owner與前後一致性。不存在時UNKNOWN_USER_MANAGER_BUS，不能start/enable/linger或daemon-reload。原WSL user-session warning沒有被client version成功清除。

所審v255 user-private連線失敗可能轉default user bus；封閉DBUS_SESSION_BUS_ADDRESS指向無效FD路徑的既有規則保留。這是source-family推論，不是對Ubuntu binary patch/library的attestation。[bus-util v255](https://raw.githubusercontent.com/systemd/systemd/v255/src/shared/bus-util.c)。

本輪沒有讀live sockets、bus、proc或cgroup。將來只可使用使用者既有非root session；不能用wsl --exec建立新attachment替代未驗證的原session。無合法直接session能力時交付人工命令，仍需scope/source/dependencies先通過。不是在本輪啟動WSL、登入或修復服務。
