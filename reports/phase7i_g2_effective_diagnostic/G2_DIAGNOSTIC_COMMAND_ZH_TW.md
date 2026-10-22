# 最小下一步：hash-only bootstrap，完整diagnostic未批准

先另審此單次query，只在已開啟的Ubuntu非root session操作，不啟動WSL。DIAG_ROOT須指向此exact source checkout；它不是tool hash占位值。工具身分仍UNKNOWN。

```bash
DIAG_ROOT="$(pwd -P)"
/usr/bin/python3 -I -B -c 'import hashlib,pathlib,sys; p=pathlib.Path(sys.argv[1]); b=p.open("rb").read(131073); assert len(b)<=131072 and hashlib.sha256(b).hexdigest()==sys.argv[2], "SOURCE_HASH_MISMATCH"; exec(compile(b,str(p),"exec"),{"__name__":"__main__","__file__":str(p)})' "$DIAG_ROOT/simulation/hh_signal/final_closure/master/diagnostic_tools.py" '6ffd7db2f116fb509e44584651feb5bb4595ab33dcc3f034d89c25fe50509582'
```

只讀三個ELF、link/stat/owner/mode與目前Python版本/UID/GID，不執行systemctl或timeout、不讀proc/sys inventory、不寫receipt、不連bus/network。來源hash是此source的真值。Python自身尚屬bootstrap觀察，不是root-of-trust attestation；查到的SHA及version仍須獨立source/family審查。輸出為HASH_ONLY_OBSERVED_NOT_ATTESTED；不得拿它批准後續query。若錯誤先保留一次輸出，不重試。

完整adapter必須等三個binary真值、resolved identity、source revision/hash、UID/GID、private parent與獨立human scope reference核實後另審。現在沒有可執行的完整scope，無假hash、無預先授權。
