# Independent final observer V2

consumer先取得trusted acquisition的expected contract，不能從不受信trace抄自己的identity當expected。包含boot、InvocationID、run nonce、parent dev/inode、source/config與slot SHA；registry含controller/worker/collector及所有designated helpers的PID/start/UID/group。registry必須由未部署的受保護manager確認完整且封閉migration，不能只相信JSON布林值。

最後observer在parent與所有job child death domains之外，使用獨立PID/start、UID與source hash；外部成本只在未接受的B supplement proposed manager_journal歸屬，原A未滿足。observer只能觀察collector已退出，不能自證自己termination。

九個phase sample windows含同job identity、sequence、registry hash、role states、parent raw cpu/memory/events/procs與membership讀回。最後還有observer actor/source、observed collector PID/start、postmortem SHA、slot identity/complete。cpu.stat應在collector退出後、parent移除前flush/read；若group已消失或缺counter則UNKNOWN，不補0。

final populated=0、direct members空、完整owned registry EXITED及獨立掃描無descendant必須一致。過早Main PID exit、unit消失、collector自己的empty聲明不能接受。protected slot落盤失敗、observer死亡或timeout只保留既有commits，不重跑。raw acquisition、UID/FD/peer credential保護、slot writer及manager部署仍缺，任何通過只稱PASS_G2_TRACE_INPUT_CONSISTENCY_ONLY。
