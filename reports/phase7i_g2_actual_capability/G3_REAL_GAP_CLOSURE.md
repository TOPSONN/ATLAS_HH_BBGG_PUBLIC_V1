# G3 genuine source gaps closed

保留舊resource_trace與job_envelope，未修改歷史runtime/guard。新g2_protocol提供版本化pure contract/trace decoder、observer verification、checked integer memory模型與stop-state請求函數。

實際重現的舊缺口：(1)舊final observer只靠不同字串，不能綁定PID/start/UID/source/slot及同一預期job；(2)舊raw reader把空direct cgroup.procs等同空subtree，會拒絕parent無direct process、children仍活著的合法hierarchy。新decoder區分direct members與populated subtree，並保留seq_file可能重複PID的明確dedup診斷。

新trace綁定外部預期boot/Invocation/run nonce、parent dev/inode、source/config/slot、role registry與每個PID/start/UID。final observer必須位於job death domain之外、非worker UID、符合獨立source identity；綁定collector exit與slot commit。階段順序、sample windows、CPU parts/reset/overflow、local/hierarchical events、peak reset、OOM、swap、resurrection、missing registry與實際最終CPU/wall超額均拒絕。

source-only positive永不輸出actual enforcement verified。舊live reader不適用此新parent/children拓樸；新decoder尚未接到真實protected acquisition/manager。這個migration是明確runtime blocker，沒有偷偷把新pure協定視為已修好production controller。
