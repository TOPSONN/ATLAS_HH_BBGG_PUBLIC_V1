"""Narrow review documents for observed hashes and the next version-only scope."""
DOCS={
'G2_INSTALLED_VERSION_REVIEW.md':'''# Installed systemd 版本審查

使用者回報的systemctl SHA已綁定，但沒有systemctl --version或manager Version輸出。INSTALLED_SYSTEMD_VERSION_VERIFIED=false，實測值null；Ubuntu24.04.4或ELF hash存在都不等於已證v255。現workspace只持有Windows上的歷史資料，沒有讀取live Ubuntu binary，也沒有WSL/UNC存取。

所審systemd v255在systemctl.c的ARG_VERSION分支直接return version()；候選新argv固定為/usr/bin/systemctl --version，不是原三條manager query的替換。該source行為不證實installed binary；執行前要重核本次回報的三個hash及原source。所提wrapper只啟動一個pinned systemctl child，GNU timeout只查identity不執行；無system/user bus、無service unit參數、無pager/password agent。

候選採相同5s query、1s cleanup與8192-byte合併輸出，30s adapter soft gate；獨立single-use目錄先寫attempt再寫receipt/SHA，0700/0600 exclusive，不自動retry。它會消耗非零CPU/RAM與本地I/O，不是kernel hard envelope；未知dynamic loader/依賴可能有額外行為，此風險也須在版本query獨立批准時審閱。

未執行。即使之後輸出systemd255，只證client self-report與目前digest的配對；不證PID1/user-manager版本、bus可用、delegation或完整host attestation。若不是255、輸出不完整、timeout、stderr或cleanup未知，一律停止，不改family契約。版本觀測需新input/run，不能附舊checkpoint。

來源：[v255 systemctl.c](https://raw.githubusercontent.com/systemd/systemd/v255/src/systemctl/systemctl.c)、[systemctl255手冊](https://www.freedesktop.org/software/systemd/man/255/systemctl.html)。
''',
'G2_DEPENDENCY_CLOSURE.md':'''# Python、ELF 與依賴閉合

OBSERVED：使用者回報Python3.12.3、root-owned python3 symlink→python3.12與三個root-owned ELF64 x86-64；不是獨立讀取。三個binary的permission bits、ELF interpreter bytes/hash、DT_NEEDED、loader cache、transitive libraries、root trust及目前installed package/source映射仍UNKNOWN。不得用Ubuntu版本猜libc或systemd patch level，也不執行ldd。

SOURCE_COMPATIBLE：原碼需要hashlib/json/pathlib/re/base64/os/stat/sys/time/struct/signal/selectors/subprocess、Linux pidfd、dir_fd與O_NOFOLLOW。Python3.12 API族具所需介面；pidfd_open在Linux>=5.3可用且Python3.9新增。但使用者這個interpreter的build flags、stdlib/extension origins與hash、syscall/security-policy權限尚未觀察。Windows或GitHub Linux測試不能替代該環境。

新版bounded ELF parser只從相同pinned binary已讀bytes找ELF class/machine/PT_INTERP/PT_DYNAMIC，不執行loader或解析全機路徑。Synthetic fixture通過只證parser邏輯。實際interpreter/hash、direct/transitive依賴仍null；未把DT_NEEDED未讀當empty依賴。版本-only receipt可保留同一systemctl檔案的PT_INTERP線索，仍不是依賴閉合。

後續若需補閉合，另審固定binary/loader/必要library/stdlib allowlist及bounded同FD讀取；先審NSS/PAM/plugin與loader環境，不自動擴大全filesystem掃描、安裝或network。完整diagnostic維持BLOCKED_DEPENDENCY_CLOSURE，除非有新可核實證據或使用者另立明確較弱契約；本輪沒有產生這種放寬。

來源：[Python3.12 os/pidfd API](https://docs.python.org/3.12/library/os.html#os.pidfd_open)。文件API不是目前machine的attestation。
''',
'G2_PREEXECUTION_STOP_RULES.md':'''# 執行前停止規則

現在僅source-only；完整diagnostic與version-only新query均未執行、未授權。TOOL_IDENTITY_OBSERVED=true只表示此次直接使用者回報已保存；TOOL_IDENTITY_VERIFIED=false。沒有原probe raw bytes，不捏造其digest或capture時間，也不要求重跑成功的hash-only probe。

完整diagnostic繼續用原四個source SHA、UID/GID1000/1000、固定三條argv、封閉environment、no-pager/no-ask-password/no-autostart與固定output。每child5s、cleanup1s、adapter30s都是soft；8192/32768/131072 bytes、8 lineage、0700/0600 exclusive及no retry不變。不能以expected hashes填入就推升execution-ready。

installed systemd、dependency closure、existing root-owned system-bus socket、UID1000-owned user systemd/private socket及安全parents、private output parent與scope authorization reference全部需分別核實。目前bus/socket/parent實測null。user socket缺失記UNKNOWN、不start/enable/linger；v255內部default-user fallback的無效FD地址封閉規則保留；新version-only argv不觸碰bus。

任一source/tool/UID/GID/argv/env變更、unknown cleanup、超界、缺receipt、重複scope/input、舊attempt或既有output都停止；不改名自動重試、不換目錄逃避single-use、不補human reference、不將false改true。必要的新版本/依賴資料只能建立新source/input run。

原private writer僅ordinary filesystem fsync，空間/權限/寫入失敗可能只保留attempt，不能保證durability或failure evidence在所有主機故障下完整。保留stderr與既有檔案，不清理、不sudo、不mount、不改服務。查詢批准不接受B-V2，也不批准cgroup、device、S4、BUILD或物理工作。
''',
'G2_NEXT_ACTUAL_OS_ACTION.md':'''# 下一個實際OS動作

最小候選為一次version-only query：同一已開啟Ubuntu非root session、UID/GID1000、Python3.12.3；重核三個已回報binary hashes與source hashes後，只啟動/usr/bin/systemctl --version一個child。沿用pinned ELF、5s/1s soft watchdog與8192-byte合併輸出；寫新0700目錄中的0600 exclusive attempt/receipt/SHA。這個候選尚待獨立批准，沒有本輪授權。

它不執行原三條manager queries，不查bus，不驗證cgroup或架構，也不啟動WSL。現有parent若無法滿足ownership/mode則先停止，不create父目錄、不更改設定。version結果與依賴線索都要作新外部input，不能重綁PR44或本次completed source-only run。

完整diagnostic目前不能作「只差按同意就可執行」的承諾：installed family、依賴閉合、bus/socket與private parent均有精確缺口。先取版本，不默默放寬其餘。原G3–G7、A/B決策與frozen physics狀態不變。
'''}
