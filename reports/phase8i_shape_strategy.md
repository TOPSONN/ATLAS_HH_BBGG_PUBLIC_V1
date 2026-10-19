# Phase8I 固定分箱的 shape strategy 與預宣告變體

## 目標、輸入與選擇

使用本次7,100個完整 native ROOT 事件，S01_C1000 分別與六個背景比較；B100保留為不同 generator configuration 的 pilot，不與C1000合併。歷史五階段選擇完全保留。所有26個observable的edges在讀取事件前凍結；沒有依本次結果重新挑選最佳cut。

## 方法

SOURCE_WEIGHTED shape 使用所有underflow、regular、overflow的有定義事件權重和正規化；缺失候選不填0。空樣本或近抵消signed sum保持undefined。ROOT scaled Sumw2為填入權重的代數量；另以完整original N計算 normalized bin 的delta-method covariance：g_i=(x_bin_i-p_bin*x_total_i)/sum(x_total)，Var(p)=N/(N-1)*sum(g_i^2)。這保留bin與total的事件相關，未將bin視為獨立。

Total variation、binned cumulative distance與overlap coefficient只描述固定分箱的形狀，不是p-value、物理顯著度或實驗可辨識度。每一個bin另列ESS、實際來源數、empty/low-ESS/單事件dominance警告；background為0的ratio保持null。

## 實際數值

| Background | Observable (FINAL_MGG) | Total variation | Binned cumulative distance | overlap | Status |
|---|---|---:|---:|---:|---|
| B01 | DeltaR_bb | 0.537962037962038 | 0.5309690309690311 | 0.462037962037962 | VALID_DESCRIPTIVE_ONLY |
| B01 | m_HH | 0.3856143856143856 | 0.1660839160839161 | 0.6143856143856143 | VALID_DESCRIPTIVE_ONLY |
| B01 | m_bb | 0.7335164835164835 | 0.5954045954045954 | 0.2664835164835165 | VALID_DESCRIPTIVE_ONLY |
| B01 | m_gamma_gamma | 0.9005994005994006 | 0.5714285714285715 | 0.0994005994005994 | VALID_DESCRIPTIVE_ONLY |
| B02 | DeltaR_bb | 0.951048951048951 | 0.8881118881118882 | 0.04895104895104895 | VALID_DESCRIPTIVE_ONLY |
| B02 | m_HH | 0.7482517482517482 | 0.4895104895104895 | 0.2517482517482518 | VALID_DESCRIPTIVE_ONLY |
| B02 | m_bb | 0.986013986013986 | 0.9720279720279721 | 0.013986013986013986 | VALID_DESCRIPTIVE_ONLY |
| B02 | m_gamma_gamma | 1.0 | 1.0 | 0.0 | VALID_DESCRIPTIVE_ONLY |
| B03 | DeltaR_bb | undefined | undefined | undefined | UNDEFINED_EMPTY_OR_ILL_CONDITIONED_SHAPE |
| B03 | m_HH | undefined | undefined | undefined | UNDEFINED_EMPTY_OR_ILL_CONDITIONED_SHAPE |
| B03 | m_bb | undefined | undefined | undefined | UNDEFINED_EMPTY_OR_ILL_CONDITIONED_SHAPE |
| B03 | m_gamma_gamma | undefined | undefined | undefined | UNDEFINED_EMPTY_OR_ILL_CONDITIONED_SHAPE |
| B04 | DeltaR_bb | 0.23720279720279724 | 0.1477855477855478 | 0.7627972027972028 | VALID_DESCRIPTIVE_ONLY |
| B04 | m_HH | 0.4085780885780886 | 0.36941724941724946 | 0.5914219114219115 | VALID_DESCRIPTIVE_ONLY |
| B04 | m_bb | 0.6186480186480187 | 0.6186480186480187 | 0.38135198135198134 | VALID_DESCRIPTIVE_ONLY |
| B04 | m_gamma_gamma | 0.045780885780885766 | 0.045780885780885794 | 0.9542191142191142 | VALID_DESCRIPTIVE_ONLY |
| B05 | DeltaR_bb | 0.38627021833128705 | 0.38627021833128716 | 0.613729781668713 | VALID_DESCRIPTIVE_ONLY |
| B05 | m_HH | 0.24000427053862167 | 0.14509154967170235 | 0.7599957294613783 | VALID_DESCRIPTIVE_ONLY |
| B05 | m_bb | 0.4708268830406235 | 0.4536379650883468 | 0.5291731169593765 | VALID_DESCRIPTIVE_ONLY |
| B05 | m_gamma_gamma | 0.03208242139539852 | 0.018096407409384563 | 0.9679175786046015 | VALID_DESCRIPTIVE_ONLY |
| B06 | DeltaR_bb | undefined | undefined | undefined | UNDEFINED_EMPTY_OR_ILL_CONDITIONED_SHAPE |
| B06 | m_HH | undefined | undefined | undefined | UNDEFINED_EMPTY_OR_ILL_CONDITIONED_SHAPE |
| B06 | m_bb | undefined | undefined | undefined | UNDEFINED_EMPTY_OR_ILL_CONDITIONED_SHAPE |
| B06 | m_gamma_gamma | undefined | undefined | undefined | UNDEFINED_EMPTY_OR_ILL_CONDITIONED_SHAPE |

本次產出10770筆bin-level比較與56筆預宣告variant。`phase8_shape_variants.csv`逐樣本列baseline、100≤mbb≤150 GeV、diphoton pT>100 GeV、ΔRbb<1.5，以及mHH<350、350–500、≥500 GeV三區。所有結果是同一資料集內的descriptive sensitivity，沒有用S/√B選擇cut，沒有獨立holdout optimization。

## 統計限制與驗證

C1000只有143個final events；B02只有1個、B03與B06為0個，因此多數細分bin沒有足夠支持。空shape未產生虛構密度，也不解讀成零物理背景。normalized shape的不確定度與generator integration normalization error分開。

邊界、flows、signed cancellation與normalized-bin covariance已由獨立Python方法測試；actual native ROOT histogram另有逐cell回讀與獨立event-summary重算，完整最終狀態見Phase8L。

## 未解決項目與下一步

物理擬合前必須先解決heavy-flavour overlap、photon fake模型、detector calibration與系統學；κλ=2.5與5仍低支持。未自動產生新樣本或新ME；未輸出PDF/PNG。未來若有獨立資料，再預宣告可支持的粗分箱與驗證計畫。
