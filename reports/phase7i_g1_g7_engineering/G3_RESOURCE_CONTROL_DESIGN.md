本文件為待獨立審查提案，不是執行授權。Exact source `83d1cda235e1d5fcc23f48d6a53065f88f2d1b1d`。未批准者保持BLOCKED；不得自行填假approval、降限制或改原始收據。

# CPU/RAM/wall control-plane interface

保留既有job_envelope.py與full_controller.py。原source明載CPU early-stop 3s、contract4s、Main-origin wall缺activation、非atomic lifetime hard kill；這些不被新profile改名為完整硬限制。新resource_trace reader獨立檢查raw usage/user/system、memory peak/events、swap、boot/cgroup/InvocationID、clock/counter reset、worker resurrection、admission與collector-finalized端點、owned descendants、postmortem及raw populated=0。

最後cgroup-empty收據不能由已退出collector自證；必須有不同的final observer identity。這個新source檢查會拒絕self-post-exit claim，但身份認證與真正kernel counters仍需外部acquisition，輸入一致性不是kernel attestation。

候選enforcement重用原parent cumulative observer、early stop及manager fallback。Worker/controller共享死亡子域、collector另一子域但同budget parent。memory.max/peak/events與swap.max=0沿整條適用lineage核對；outer OOM可殺collector，故只保留已commit結果。CPU/timeout必須停整組owned descendants，postmortem在卸載前保存；缺counter或unit消失不算成功。普通Linux不提供本提案未證明的零延遲cumulative CPU stop。

SOURCE_VERIFIER_IMPLEMENTED；KERNEL_FEATURE_AVAILABLE=UNKNOWN；ACTUALLY_DEPLOYED=false；REAL_NEGATIVE_TEST_PASS=false。沒有新增live enforcer或kernel測試。


來源語義：[Linux6.6 cgroup](https://www.kernel.org/doc/html/v6.6/admin-guide/cgroup-v2.html)、[systemd255 exec](https://www.freedesktop.org/software/systemd/man/255/systemd.exec.html)、[Linux6.6 get_tree_bdev](https://github.com/torvalds/linux/blob/v6.6/fs/super.c#L1448)、[mke2fs手冊](https://man7.org/linux/man-pages/man8/mke2fs.8.html)。這些是API/source審查，不是本機kernel版本或實機能力證明。
