# 下一個實際OS動作

最小候選為一次version-only query：同一已開啟Ubuntu非root session、UID/GID1000、Python3.12.3；重核三個已回報binary hashes與source hashes後，只啟動/usr/bin/systemctl --version一個child。沿用pinned ELF、5s/1s soft watchdog與8192-byte合併輸出；寫新0700目錄中的0600 exclusive attempt/receipt/SHA。這個候選尚待獨立批准，沒有本輪授權。

它不執行原三條manager queries，不查bus，不驗證cgroup或架構，也不啟動WSL。現有parent若無法滿足ownership/mode則先停止，不create父目錄、不更改設定。version結果與依賴線索都要作新外部input，不能重綁PR44或本次completed source-only run。

完整diagnostic目前不能作「只差按同意就可執行」的承諾：installed family、依賴閉合、bus/socket與private parent均有精確缺口。先取版本，不默默放寬其餘。原G3–G7、A/B決策與frozen physics狀態不變。
