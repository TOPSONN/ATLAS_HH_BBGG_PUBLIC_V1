# Installed systemd 版本審查

使用者回報的systemctl SHA已綁定，但沒有systemctl --version或manager Version輸出。INSTALLED_SYSTEMD_VERSION_VERIFIED=false，實測值null；Ubuntu24.04.4或ELF hash存在都不等於已證v255。現workspace只持有Windows上的歷史資料，沒有讀取live Ubuntu binary，也沒有WSL/UNC存取。

所審systemd v255在systemctl.c的ARG_VERSION分支直接return version()；候選新argv固定為/usr/bin/systemctl --version，不是原三條manager query的替換。該source行為不證實installed binary；執行前要重核本次回報的三個hash及原source。所提wrapper只啟動一個pinned systemctl child，GNU timeout只查identity不執行；無system/user bus、無service unit參數、無pager/password agent。

候選採相同5s query、1s cleanup與8192-byte合併輸出，30s adapter soft gate；獨立single-use目錄先寫attempt再寫receipt/SHA，0700/0600 exclusive，不自動retry。它會消耗非零CPU/RAM與本地I/O，不是kernel hard envelope；未知dynamic loader/依賴可能有額外行為，此風險也須在版本query獨立批准時審閱。

未執行。即使之後輸出systemd255，只證client self-report與目前digest的配對；不證PID1/user-manager版本、bus可用、delegation或完整host attestation。若不是255、輸出不完整、timeout、stderr或cleanup未知，一律停止，不改family契約。版本觀測需新input/run，不能附舊checkpoint。

來源：[v255 systemctl.c](https://raw.githubusercontent.com/systemd/systemd/v255/src/systemctl/systemctl.c)、[systemctl255手冊](https://www.freedesktop.org/software/systemd/man/255/systemctl.html)。
