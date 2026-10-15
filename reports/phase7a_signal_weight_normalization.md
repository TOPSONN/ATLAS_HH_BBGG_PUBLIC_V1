# Future signal source and weight ledger

`simulation/hh_signal/config/weight_contract.json` contains every requested
source, IDWTUP/XWGTUP, Info, converter, original N, BR, identical-H and
already/missing-factor field. Real values are null/NOT_EVALUATED until actual
source closure. There is no invented cross section or empty event manifest
claiming generated particles.

Method algebra supports certified signed raw cross-section weights in pb:
c_i=(raw_weight_pb/original_N)*missing_BR_factor*selection_i. Negative signs
are preserved. A separately certified positive unit-weight convention may use
sigma_pb/original_N. IDWTUP alone is insufficient to select a convention.
Negative unit weights need explicit normalization/closure and are rejected by
the positive-unit branch. Do not infer or silently recast source semantics.

Never divide by selected/showered N, multiply sigma/N twice, multiply already
corrected Info by BR again, or convert pb/mb twice. Tests explicitly reject
these failures. Native LHE→Info→HepMC correspondence, retries/source loss,
signed sums and real decay weights remain Gate P NOT_EVALUATED.
