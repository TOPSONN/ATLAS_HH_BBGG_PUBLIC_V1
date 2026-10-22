# OOM and protected evidence

worker/controller子死亡域與collector子域分離，但同一parent RAM/CPU pool。這減少worker失敗直接殺掉collector的機會，不保證parent OOM時collector存活。memory.oom.group、OOM score與manager設定都需獨立部署審查；不得假設原先MemoryMax旗標已覆蓋全部child或排除共享charge。

8×4096-byte slots中預留2個failure lanes；worker不得取得writer FD或collector UID權限。collector只寫預先核實、preallocated、受保護的fixed-device slots。UID、SO_PEERCRED、PID start、boot、InvocationID、source/config、slot身份及序號都要由future trusted acquirer綁定。現階段只有source predicates，沒有真的privileged consumer、writer保護或OOM測試。

遇OOM、collector死亡、ENOSPC或outer manager失效，只保留已commit slots並將缺失後段標UNKNOWN。重開相等/fsync ACK不能證明突然掉電後存活。final observer不得自稱觀察自己的死亡；它觀察的是已退出collector及空parent，自身生命週期留在declared external boundary。原A仍未滿足。
