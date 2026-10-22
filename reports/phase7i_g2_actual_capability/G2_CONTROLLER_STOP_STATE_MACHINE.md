# Controller stop state machine

g2_protocol.stop_decision為純函數：RUNNING → TERM_REQUESTED → KILL_REQUESTED → DRAINING_COLLECTOR → WAIT_OBSERVER；collector/observer loss、總wall/CPU超限 → UNKNOWN。先只TERM/KILL worker/controller死亡域，collector仍計帳並限時postmortem後退出；collector-loss／deadline失敗才要求manager清全部job並保留既有commit。UNKNOWN沒有自動retry。輸入event叫FINAL_ACCEPTED也不能取代完整trace驗證或trusted capture；此函數任何分支accept=false，沒有執行kill或service。

完整順序為ADMISSION、ACTIVATION、CONTROLLER_START、WORKER、TERMINATION、POSTMORTEM、DESCENDANT_CLEANUP、COLLECTOR_FINALIZATION、INDEPENDENT_FINAL_OBSERVATION。每個sample有start/end monotonic、序號、job identity及phase budget；phase總和不得超過原S4 13s／BUILD14400s，最後端點不得用Main PID exit替代。時間單位只用checked整數ns。

future部署需事先武裝獨立manager deadline；RuntimeMaxSec只對active runtime生效，start/stop另外設定TimeoutStartSec/TimeoutStopSec。KillMode=control-group只清該unit的群組，不能據此推論其他sibling collector或parent已空；需外部管理整個job registry。SIGTERM後grace與SIGKILL fallback仍受普通scheduler延遲，沒有硬即時保證。[service](https://www.freedesktop.org/software/systemd/man/255/systemd.service.html)、[kill](https://www.freedesktop.org/software/systemd/man/255/systemd.kill.html)。

observer最後時間是收集完final kernel readback的end；後續receipt序列化/commit及observer自身termination是B supplement明載的external非零成本，不能偷偷算成原A已全涵蓋。若沒有最終committed receipt，終態UNKNOWN；不能用一個已死亡collector自己的宣告補足。
