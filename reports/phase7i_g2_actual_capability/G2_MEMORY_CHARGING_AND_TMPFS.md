# RAM, swap and tmpfs charging

一個job parent的memory.max涵蓋controller、worker、compiler、helpers、collector、可歸帳kernel/cache與tmpfs/shmem resident pages。不能給每個child完整RAM再相加。memory.events為hierarchical時不再加各child同名計數；events.local只看該層。memory_localevents mount語義須被future acquirer核對，未知則拒絕hierarchical宣稱。

BUILD work tmpfs ceiling=2,147,483,648 bytes，private=268,435,456 bytes，合計2,415,919,104 bytes，已比2,147,483,648 RAM pool多268,435,456 bytes；尚未計入process與collector。filesystem size不是預配置resident RAM，也不保證兩個tmpfs可填滿。既有ceilings不改，不能在報告中把這個配置宣稱可同時滿載。

新memory_plan要求逐項非負整數：work_resident + private_resident + process_runtime + collector + kernel_and_cache + safety_reserve <= 原RAM cap，且後四項必須非零。任何未量測/未規劃項為null就拒絕；正例只為SYNTHETIC arithmetic fixture，沒有把任意reserve當成真實runtime需求。現階段BUILD resident allocation實際可行配置仍UNKNOWN，需未來受控試驗，不能自動降低或提高上限。

須fresh私有tmpfs、排除外部writer與預先charged共享pages；否則page初始charge可能留在其他memcg，路徑名稱不保證RAM都歸此job。ancestor同時承受其他workload，會比job leaf更早OOM；需exclusive parent或明確上層約束讀回。shared host/VMM overhead另依未接受的B條款記帳，不是零。

memory.swap.max=0必須有effective readback，swap.current=0只是瞬時usage。memory.max可短暫超額；分開讀的current、peak、limit不是原子snapshot，較晚current可以大於較早peak。任一observed peak超原cap或OOM仍拒絕run，沒有證明零transient overshoot。原A若要求literal零超額，標準Linux此API不能證成。[memory](https://raw.githubusercontent.com/torvalds/linux/v6.6/mm/memcontrol.c)、[tmpfs](https://www.kernel.org/doc/html/v6.6/filesystems/tmpfs.html)、[systemd](https://www.freedesktop.org/software/systemd/man/255/systemd.resource-control.html)。
