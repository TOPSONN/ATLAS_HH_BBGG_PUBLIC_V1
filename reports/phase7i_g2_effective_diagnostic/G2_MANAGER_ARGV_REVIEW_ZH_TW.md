# Manager query source 審查

所審systemd255的show不指定unit會查manager，Version/SystemState可作固定選擇；不是列全部unit、journal或配置檔。額外的user@UID.service只查effective resource/delegation相關properties，不create/start unit；查unit可能引發manager載入unit metadata，須列入incidental control-plane side effects。

新第三條不證明未來job配置：CPUAccounting/MemoryAccounting是該既存service的effective property；Delegate=yes不等於任意未來child或collector UID已獲寫權。ControlGroup/InvocationID/MainPID需要與當時service狀態解讀。沒有合格未來group、受保護UID、fixed device或observer，仍UNKNOWN。

v255 verb_show使用BUS_MANAGER；user private連線失敗可fallback default_user。因此僅檢查session-bus socket不夠。此新版本改檢既存systemd/private且封閉default-user fallback address；沒有bus-autostart helper。這是source-family推論，不是對未讀binary的證明；版本或hash不同先另審，不自行採納新版。

官方來源：[systemctl255](https://www.freedesktop.org/software/systemd/man/255/systemctl.html)、[bus-util255](https://raw.githubusercontent.com/systemd/systemd/v255/src/shared/bus-util.c)、[systemctl-util255](https://raw.githubusercontent.com/systemd/systemd/v255/src/systemctl/systemctl-util.c)。
