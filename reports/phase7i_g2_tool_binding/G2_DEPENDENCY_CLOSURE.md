# Python、ELF 與依賴閉合

OBSERVED：使用者回報Python3.12.3、root-owned python3 symlink→python3.12與三個root-owned ELF64 x86-64；不是獨立讀取。三個binary的permission bits、ELF interpreter bytes/hash、DT_NEEDED、loader cache、transitive libraries、root trust及目前installed package/source映射仍UNKNOWN。不得用Ubuntu版本猜libc或systemd patch level，也不執行ldd。

SOURCE_COMPATIBLE：原碼需要hashlib/json/pathlib/re/base64/os/stat/sys/time/struct/signal/selectors/subprocess、Linux pidfd、dir_fd與O_NOFOLLOW。Python3.12 API族具所需介面；pidfd_open在Linux>=5.3可用且Python3.9新增。但使用者這個interpreter的build flags、stdlib/extension origins與hash、syscall/security-policy權限尚未觀察。Windows或GitHub Linux測試不能替代該環境。

新版bounded ELF parser只從相同pinned binary已讀bytes找ELF class/machine/PT_INTERP/PT_DYNAMIC，不執行loader或解析全機路徑。Synthetic fixture通過只證parser邏輯。實際interpreter/hash、direct/transitive依賴仍null；未把DT_NEEDED未讀當empty依賴。版本-only receipt可保留同一systemctl檔案的PT_INTERP線索，仍不是依賴閉合。

後續若需補閉合，另審固定binary/loader/必要library/stdlib allowlist及bounded同FD讀取；先審NSS/PAM/plugin與loader環境，不自動擴大全filesystem掃描、安裝或network。完整diagnostic維持BLOCKED_DEPENDENCY_CLOSURE，除非有新可核實證據或使用者另立明確較弱契約；本輪沒有產生這種放寬。

來源：[Python3.12 os/pidfd API](https://docs.python.org/3.12/library/os.html#os.pidfd_open)。文件API不是目前machine的attestation。
