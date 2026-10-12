# Phase 6A background LHE validation

實際執行完整 portable suite：59/59 PASS，無 skips。原 22 tests 保留，新增 generator/publisher 與兩個背景 profile 的 adversarial tests。`--repository .` 原 bbgg smoke100/reference1000 均 PASS；`--background-library .` 對 3 個 reference 共 3000 events PASS，100-event smoke 另作 regression、不計入 library。

```bash
python3 -B -m unittest discover -s simulation/mg5/tests -v
python3 -B simulation/mg5/scripts/validate_lhe.py --repository .
python3 -B simulation/mg5/scripts/validate_lhe.py --background-library .
```

完整執行輸出見 `simulation/mg5/evidence/background_1k/tests-final.txt`；physical outputs 與 cut extrema 見 `library-validation.json`。檢查 gzip CRC/deterministic header、完整 XML、exact counts、beam/PDF/version/cards/hashes、status/ancestry、每 event 2 photons 與指定 partons、color representation/flow、finite vectors/weights、mass shell、four-momentum、electric charge 與新 profiles 的逐味道 net-quark-number conservation；測試包含 same-charge flavour mutation、missing event、cuts/PDGs/cards/hash corruption 等。

| Profile | Max component closure [GeV] | Max mass-shell residual [GeV²] | Negative / zero weights |
|---|---:|---:|---:|
| bbgg | 9.69998836808e-08 | 0.000272020697594 | 0 / 0 |
| ccgg | 9.09999471332e-08 | 0.000413162633777 | 0 / 0 |
| jjgg | 8.99999577086e-08 | 0.000319346785545 | 0 / 0 |

Mass-shell 大數相減採相對/絕對 tolerance；以上是 LHE decimal serialization 的實測殘差，並非 detector resolution。IDWTUP=-4，`event_norm=average`，本批常數 XWGTUP 約等於該 process 截面 [pb]，histogram 每 event 的 normalization 為 XWGTUP/N；無負權事件。

截面另外從真正的 `event_generation.log` 和 `SubProcesses/results.dat` 各獨立提取；兩者列印位數較少，與 LHE `<init>` 在各自 rounding precision 內一致。raw results、SHA 和 field definitions 在 `cross-section-audit.json`。不共用三個 process 截面，不加總為完整 diphoton+jets prediction。

| Profile | NEVENTS (nonzero sampling points) | NW (after primary unweighting) | NUNWGT (pool) | NUNWGT/NEVENTS |
|---|---:|---:|---:|---:|
| bbgg | 185383 | 72409 | 8541 | 4.607219% |
| ccgg | 199873 | 74532 | 8312 | 4.158641% |
| jjgg | 498864 | 178281 | 11870 | 2.379406% |

欄位依 pinned MG5 `madgraph/madevent/sum_html.py` `OneResult.read_results` 及 `Template/LO/Source/dsample.f`（lines147,213–219）定義：NEVENTS 寫入 kevent，只計非零權重 sampling points，不包含所有 function calls；NW=after primary unweighting，NUNWGT=unweighted pool。以上 count ratios 是 summed final results（含 oversampled pool）對非零權重 pool 的條件效率，排除 zero-weight integration points，不能稱為 all-point 或 universal generator efficiency，亦不是 detector acceptance。NW/NEVENTS 與 NUNWGT/NW 詳列 JSON，raw headers 保留供核對。

歷史 bbgg manifest 的 `alpha_s_settings.param_card_as=0.118` 是先前 metadata 值；原實際 banner SMINPUTS(3)=0.129783，event AQCD=0.1238062。依要求保留歷史 manifest 原 bytes，不以該舊欄位覆蓋實際 physics。新 ccgg/jjgg manifests 均直接從 actual card 導出 0.129783；三批實際 PDF/scales/event coupling 相同。

舊 bbgg reference SHA `bc8f0c4a48a1db512013552afe3ec8091dddaae8b47daf7aae808d7cb767a343`；smoke SHA `1427fd1446f6bce5627be769a5fde905206f01b684d72d2b8ee35b46a198c568`，原目錄、cards、historical provenance 的 Git blobs 對基線完全未變。兩個新 archive 均 <=5 MiB。ROOT source/build 無影響，所以依任务條件不重跑 ROOT CTest；既有 ROOT environment identity 未變，不將舊 CTest 報成此次新執行。

GitHub CI 狀態在 publication/decision reports 記錄；local PASS 不代替 remote CI PASS。

GitHub Actions 同樣實際執行59tests且成功：https://github.com/TOPSONN/ATLAS_HH_BBGG_PUBLIC_V1/actions/runs/38240760152。遠端 reference bytes 重新下載後重驗為3000，original smoke100 regression 亦 PASS。
