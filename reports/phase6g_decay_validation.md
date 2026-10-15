# Phase6G 實際 decay 與 ancestry

| Process | Hgg birth events | Source Zbb birth events | Top/W validated events | One-Born-photon validated events |
| --- | --- | --- | --- | --- |
| B04 | 1000 | 1000 | 0 | 0 |
| B05 | 1000 | 0 | 1000 | 0 |
| B06 | 0 | 0 | 0 | 1000 |

B04 的 Zbb 在 MG5 source 內；B04/B05 的穩定 source H 由 initialized Pythia forced H→γγ model 衰變。Full HepMC record graph、source index、原始 particle identities 及 decay birth/final photons 分開讀回，不只依據 Pythia.next()。

B05 top/W 採 supported inclusive Pythia model，W channels 無 restriction；t→b/s/d W 的 supported CKM branches 保留。Installed MadSpin source 存在，但 end-to-end spin-correlated workflow 沒有完成驗證；production-decay spin correlations 為 NOT_VALIDATED，無 exclusive top/W BR factor。

B04 actual top daughter PDGs：`{}`；W birth PDGs：`{}`；H final photon multiplicity：`{'2': 1000}`。

B05 actual top daughter PDGs：`{'-5': 1000, '5': 1000}`；W birth PDGs：`{'-16': 108, '-15': 114, '-14': 97, '-13': 106, '-12': 116, '-11': 122, '-4': 326, '-3': 328, '-2': 353, '-1': 330, '1': 347, '2': 326, '3': 329, '4': 332, '5': 3, '11': 116, '12': 122, '13': 97, '14': 106, '15': 108, '16': 114}`；H final photon multiplicity：`{'2': 1000}`。

B06 actual top daughter PDGs：`{}`；W birth PDGs：`{}`；H final photon multiplicity：`{'0': 1000}`。

B06 一個 Born photon 與 shower radiation/hadron decay/other photons ancestry 各自保存，第二個 reconstructed Photon 不能解釋成 calibrated fake。

MG5 stable-source input widths（top1.4915 GeV、W2.0476 GeV）與Pythia初始化後的inclusive model widths分開：

| Actual initialized Pythia particle | Mass (GeV) | Inclusive model width (GeV) |
| --- | --- | --- |
| 6 | 173 | 1.3553448418805865 |
| 24 | 80.418999999999997 | 2.0931855123021208 |

Actual W channel counts（包括rare supported CKM mode）：`{"-24:-12,11": 116, "-24:-14,13": 97, "-24:-16,15": 108, "-24:-2,1": 331, "-24:-2,3": 22, "-24:-4,1": 16, "-24:-4,3": 307, "-24:-4,5": 3, "24:-1,2": 312, "24:-1,4": 18, "24:-11,12": 122, "24:-13,14": 106, "24:-15,16": 114, "24:-3,2": 14, "24:-3,4": 314}`。此pilot rare top→d/s觀測0，不代表model probability為0；actual on-mode與inclusive tables保持其非零supported channels，完整table列於metadata。
