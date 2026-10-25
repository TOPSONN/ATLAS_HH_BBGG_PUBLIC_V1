# Python import信任與修復

原Windows-backed checkout的DACL與hash-then-import間隙分開記錄；不移動或修改PR45。新版本只規劃10份最小source closure，原四份diagnostic檔逐SHA不改；新增guard、capsule bootstrap與獨立security validator。staging writer只向已驗native Store exclusive-create 0400檔案，不搬整個專案。

正式冷啟動必須先由外部已審的inline command在同FD讀bootstrap bytes、核exact SHA，再compile相同bytes；缺EXTERNAL_BOOTSTRAP_SHA256就在native讀取前BLOCKED。bootstrap固定closure名稱、逐FD hash並保留FD到結束，建立封閉private package；只exec已compile的approved bytes，不插checkout sys.path、不讀它的__init__或pyc，也不對missing capsule module退回一般PathFinder。原始與secure Store兩組FD還須是同一檔案實例。

python -I忽略PYTHON環境、user site及不安全的起始搜尋路徑；不會凍結檔案。-B只禁止寫pyc，不能阻止讀取既有stdlib cache。新-I -S -B提案另禁site；這是新source契約，不能繼承已消耗version批准。Python/root stdlib、extension、loader、libpython與動態插件仍是外部信任邊界；檔名來源或.py hash不等於已驗執行中的cache/DSO閉合。[Python3.12 options](https://docs.python.org/3.12/using/cmdline.html)。

目前native staging與runtime dependency proof均未取得。固定allowlist比對已實作，但child的完整動態解析provider尚未實作；capture額外fail-closed gate保持BLOCKED，不讓一個JSON status取代閉合。
