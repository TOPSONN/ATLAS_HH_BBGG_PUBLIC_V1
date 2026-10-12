# Actual V2 small-run results

All rows below contain genuine MG5 events, not generated fixtures. Only the two 13 TeV references are selected for repository publication. The separate 100-event final CLI test verifies changed energy/seed and supplied cards, remains local, and contributes zero events to the production target.

| Sample | Events | Seed | Energy GeV | Cross section pb | Integration error pb | Total seconds | Measured events/s | Gzip bytes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| smoke_100 | 100 | 12345 | 13000 | 0.06685344 | 0.0005076687 | 12.171224 | 8.216101 | 22449 |
| reference_1000 | 1000 | 12346 | 13000 | 0.06569109 | 0.0004706016 | 27.360766 | 36.548684 | 166712 |
| cli_100 | 100 | 12347 | 14000 | 0.0732962 | 0.0005512499 | 16.251610 | 6.153236 | 22463 |

Elapsed measurements include startup/process setup, integration/event generation, export and independent validation. These short runs are not production performance benchmarks. Estimated million-event runtime and total disk are UNKNOWN: integration/setup costs and MG5 production behaviour have not been measured at that size. Current reference output directories were about 37.2/38.3 MB, including build/integration artefacts; gzip sizes alone do not represent total production disk use.

Every actual event was independently checked for full gzip/XML integrity, init metadata, generator/model/orders/PDF identity, finite records, final PDGs, mass shell, four-momentum/charge closure, actual pT/eta/DeltaR cuts, positive constant nominal weights, applied seed/energy and card/source/hash consistency. No invalid event was repaired or discarded. Archived cards come from exact LHE banner text; the mutable post-run seed-reset card is preserved separately. IDWTUP=-4/event_norm=average uses positive constant XWGTUP approximately equal to the integrated cross section: histogram normalization is XWGTUP/N.

The scalable standard-library validator reads all events without retaining the event tree. It accepts plain/gzip LHE with adjustable 20/100 GiB input/decompressed policy limits. Reference repository policy separately remains 5 MiB per gzip and 10 MiB total. Corruptions and resource/control paths are covered by tests; a large comment-only container test retains the real events and is not a large statistics sample.

PRODUCTION_1M_STATUS: NOT_EXECUTED_BY_DESIGN. No 10000/100000/1000000 generation ran. Single-million and ten-independent-batch plans were physically dry-run only (zero events, no production output directory). No blind concatenation, repeated-process cross-section summation or reference-count inclusion is implemented. Interrupted generation restarts a complete attempt preserving the old attempt; it does not continue MG5 integration grids or merge partial events.
