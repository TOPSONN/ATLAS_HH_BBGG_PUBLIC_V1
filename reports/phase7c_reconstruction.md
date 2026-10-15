# Phase7C：真實重建診斷

完整1000個ROOT事件均以native字典與schema讀回；所有可用數值成員有限，Particle的p4、質量、位置float32多重集合與同一HepMC精確對應。四動量使用Cartesian表示，缺少配對的值保留null。

Hγγ幾何匹配計數：`{"0": 60, "1": 299, "2": 641}`；Hbb到eligible jet的幾何匹配：`{"0": 43, "1": 402, "2": 555}`。這些是幾何診斷，並非已校準效率。

以下統計僅針對有定義的實際觀測配對，包含選擇與tag條件，不是無偏Higgs質量或解析度測量：

```json
[
  {
    "observable": "m_gamma_gamma",
    "defined_events": 484,
    "missing_events": 516,
    "min_GeV": 111.28863407984525,
    "median_GeV": 124.92803451905753,
    "mean_GeV": 124.93083357260485,
    "sample_stddev_GeV": 1.3808374738587423,
    "max_GeV": 128.7701469695747
  },
  {
    "observable": "m_bb",
    "defined_events": 305,
    "missing_events": 695,
    "min_GeV": 20.526441847743037,
    "median_GeV": 107.24416366634247,
    "mean_GeV": 112.09135277230293,
    "sample_stddev_GeV": 59.005725743656356,
    "max_GeV": 842.8200211711331
  },
  {
    "observable": "m_bb_gamma_gamma",
    "defined_events": 143,
    "missing_events": 857,
    "min_GeV": 215.04413464327695,
    "median_GeV": 397.5213867738351,
    "mean_GeV": 439.2307441893969,
    "sample_stddev_GeV": 145.1894483511015,
    "max_GeV": 1074.9238219744802
  }
]
```

mbb與mbbγγ使用實際leading兩個tagged jets，沒有以未標記jet對替代。若計算tag期望配對分布，必須另外帶入各tag組合機率；本次質量分布保留真實一次tag結果。
