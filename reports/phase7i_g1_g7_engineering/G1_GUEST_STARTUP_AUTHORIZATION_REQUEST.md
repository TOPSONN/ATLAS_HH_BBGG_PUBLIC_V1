# Ubuntu guest 診斷啟動：獨立授權請求套件

本文件為待獨立審查提案，不是執行授權。Exact source `83d1cda235e1d5fcc23f48d6a53065f88f2d1b1d`。未批准者保持BLOCKED；不得自行填假approval、降限制或改原始收據。

目前沒有啟動授權。Ubuntu是既有Windows capture的registered distribution名稱，registration identity digest為`3d2ca8f596d2340db1e70a6de71dc758b699d0849212c0f4446acd668dd6f8f2`。這是reported registry identity，不是boot identity。`btu`來自歷史使用者shell；本輪未重新驗證guest UID，禁止fallback到root或sudo。

目的：僅取得boot/namespace、完整cgroup lineage、sysfs/mount及logging檔案設定，解決G1/G2實證缺口。guest collector SHA `79e0879b214b7945137d416b9da9b9d2a38c8b13997bec0e638ef68e23e5d84a`；依賴的原V1 constants source SHA `dc9240024052d2d1ab8fa76689e8bcce3281078026826271da7469f2fb6b881f`。installed guest copy及Python/timeout binary身份仍未核對，不能宣稱已部署。

擬議單次argv如下，**現在不得執行**：

```powershell
& "C:\Windows\System32\wsl.exe" --distribution Ubuntu --user btu --exec /usr/bin/timeout --signal=TERM --kill-after=2s 20s /usr/bin/python3 -B /mnt/c/HH/.local/phase7i_g1_g7_readiness_v1/source/simulation/hh_signal/final_closure/master/guest_v2.py --output-directory /home/btu/simulations/hh_final_closure/g1_g7_readonly_private_01 --expected-script-sha256 79e0879b214b7945137d416b9da9b9d2a38c8b13997bec0e638ef68e23e5d84a
```

WSL binary維持`fcd08205b608b5c4831e0dcb1801dd274436cd2c8420815f18ae58a085891a18`，若改變另審。輸出目錄必須先由使用者另允許建立，nonroot owner、0700、無symlink；不是自動mkdir。source路徑是host checkout唯讀，不安裝或修改MG5。

輸出：一份CreateNew 0600 private guest JSON，最大262144 bytes、retained file text196608 bytes、最多768 records、每file1024/2048/8192/32768 bytes按固定用途，cgroup深度16，block/by-id各128、config dir32、holders/slaves128，超限整項UNKNOWN。stdout只給摘要；raw不push。collector不發subprocess/network/ioctl，也不開block-device data FD。

啟動WSL會產生VM/kernel/systemd/session、log與host-backed writes，且guest可能在命令結束後繼續running。這些啟動成本目前未量測，也未在S4 envelope內。guest timeout只是提案中的20s＋2s終止界線，工具存在性及host WSL admission timeout仍未實測，不可稱硬wall/RAM限制。若不能接受這個啟動成本範圍，不批准此argv；先由使用者手動提供已運作且受允許的shell，或另審host admission wrapper。

Stop：distro/user/hash不符、缺timeout/Python、private path不符、boot/ns變更、輸出超限或launcher失敗時停止，不重試、不改用root、不安裝、不重啟systemd、不自動terminate整個distro。不能把殺掉Windows launcher當guest cleanup已成功；需另核對該診斷PID。這份scope不含format/mount/quota/S4/build/ME/integration。

請決定是否准許此**有揭露啟動限制的研究級唯讀診斷**；不是批准原A完整hard envelope。若同時要求可證明的host startup hard cap，目前仍BLOCKED，不能沿用此命令冒充。
