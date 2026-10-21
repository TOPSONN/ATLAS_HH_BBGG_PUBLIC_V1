本文件為待獨立審查提案，不是執行授權。Exact source `83d1cda235e1d5fcc23f48d6a53065f88f2d1b1d`。未批准者保持BLOCKED；不得自行填假approval、降限制或改原始收據。

# Provisioning prerequisites

選擇dedicated fixed-capacity filesystem位於獨立、可拋棄、已核實whole block backend；不是WSL root partition、C-drive可成長VHD、loop、tmpfs或S3 logical slots。裝置供應方式與host allocation仍待管理員提出，未假裝目前有4MiB實體裝置。若厚配置virtual/LUN，須證明independent parent、fixed allocation與完整host mapping，不能只看guest size。

架構條款未接受、device/exclusivity/helper未部署前，不能provision。對主機的影響是新裝置供應及受審attachment，可能有host metadata/log writes；影響邊界未綁定所以本輪不生成會碰裝置的命令。
