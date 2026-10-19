#!/usr/bin/env python3
"""Write Traditional Chinese reports from completed actual outputs only."""
import argparse
import hashlib
import json
import math
from pathlib import Path

def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def number(value): return '未定義' if value is None else format(value,'.12g')
def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,lines):
    with Path(path).open('x',encoding='utf-8',newline='\n') as stream:stream.write('\n'.join(lines)+'\n')

def generate(args):
    index=read(args.statistics_index)
    if 'datasets' in index:index=index['datasets']
    stats={name:read(path) for name,path in index.items()}
    kappa=read(Path(args.kappa_directory)/'phase8_kappa_summary.json')
    tails=read(Path(args.kappa_directory)/'phase8_kappa_weight_tails.json')
    methods=read(args.methods);audit=read(args.independent_receipt)
    if audit['status']!='PASS_INDEPENDENT_DECIMAL70_STATISTICS':raise ValueError('INDEPENDENT_STATISTICS_NOT_PASS')
    if methods['status']!='PASS_SYNTHETIC_METHOD_ONLY':raise ValueError('SYNTHETIC_METHODS_NOT_PASS')
    output=Path(args.report_directory)
    if not output.is_dir():raise ValueError('REPORT_DIRECTORY_MISSING')
    f=['# Phase8F 來源權重、模型 branching ratio 與 MC 統計','',
       '## 目標與實際輸入','',
       '以本次 native ROOT readback 的完整原始事件為分母，逐一分析八個資料來源。S01_B100 是不同有效設定的獨立100-event pilot；S01_C1000 是 NNPDF23 LO、two-loop alpha_s、seed20261122 的歷史1000-event source。兩者不合併。六個背景各維持自己的1000-event cohort，沒有產生新物理事件。','',
       '## 權重與選擇方法','',
       'native source index 綁定的 source_weight_pb 已為 XWGTUP_pb / N_original；不再乘 sigma/N。模型 BR 僅由原始 source contribution 套用一次。Signal 使用2 BR(H→bb) BR(H→gamma gamma)；ZH 已含 Z→bb，只乘自己的 H→gamma gamma；ttH 使用自己的 H→gamma gamma，沒有 HH factor2。identity multiplier1不宣稱物理BR=1。','',
       '| Dataset | N_original | 模型 factor | factor applications |','|---|---:|---:|---:|']
    for name,r in stats.items():f.append(f"| {name} | {r['N_original']} | {number(r['model_BR_factor'])} | {r['factor_applications']} |")
    f+=['','## 實際最終選擇數值','',
        'weighted sum 為各別來源的探索性 pb estimator；不得相加為 calibrated ATLAS total background。','',
        '| Dataset | N_pass | sumw [pb] | fixed-N source SE [pb] | ESS | conditional expected count | conditional tag variance |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for name,r in stats.items():
        stage=r['stages'][4];tag=r['conditional_tags'][1]
        f.append(f"| {name} | {stage['N_pass']} | {number(stage['sumw'])} | {number(math.sqrt(stage['fixed_N_source_sampling_variance']))} | {number(stage['ESS'])} | {number(tag['expected_count'])} | {number(tag['conditional_count_variance'])} |")
    f+=['','## 寬 mgg cut 前的雙 tag 對照','', '| Dataset | observed native double tags | conditional expected | conditional SD |', '|---|---:|---:|---:|']
    for name,r in stats.items():
        actual=r['stages'][3];conditional=r['conditional_tags'][0]
        f.append(f"| {name} | {actual['N_pass']} | {number(conditional['expected_count'])} | {number(math.sqrt(conditional['conditional_count_variance']))} |")
    f+=['','## 統計限制','',
        'x_i 已含來源1/N，未通過事件保留零貢獻。Var(S)=N/(N-1) sum_i(x_i-mean)^2，以 translated centered long-double accumulation 計算。sumw2是不同 histogram moment；不等同 fixed-N source variance。ESS=(sumw)^2/sumw2；零 second moment為null，signed weights保留符號，另列sum_absw與cancellation ratio。','',
        'observed event-sampling variance已含歷史 shower/detector/tag realization，不能隔離純generator variance。conditional estimator只對固定 reconstructed jets使用實際卡的獨立Bernoulli模型；persisted Float_t pT有storage-rounding approximation。三狀態DP直接累積P>=2，避免稀有tail由1-P0-P1相減消失。','',
        'conditional sum(w_i^2 q_i(1-q_i)) 與 analytic-mean source variance分開列出；不加回已含realized tag randomness的observed-outcome variance。conditional tag-count expectation不是conditional m_bb/m_HH分布；沒有用一個observed tagged pair代表所有可能tag組合。','',
        'N=1000零survivor的one-sided95% proposal acceptance upper約0.0029912495451。這只限制未加權Bernoulli proposal count，不是weighted cross-section或photon-fake rate上限。100fb^-1欄只按pb*1000*fb^-1換算，標記ILLUSTRATIVE_MODEL_YIELD。integration、PDF/scale、BR、full detector與overlap uncertainties沒有混成total band。','',
        '## 驗證、未解問題與下一步','',
        f"獨立 Decimal70 重算所有stage/observable/bin、ESS與missing，conditional tags以完整Poisson-binomial PMF獨立驗證。共{audit['comparisons']}項比較，狀態`{audit['status']}`，證據ACTUAL_FULL_DATA_READBACK；收據SHA256 `{digest(args.independent_receipt)}`。",'',
        'B01–B03 ME/PS overlap、B04/B05 MODEL_BR_ONLY、ttH spin、B06 photon fake、signal PDF/alpha_s與detector calibration限制仍保留。未來需要獨立來源、matching及校準輸入；本次不執行新production。']
    write(output/'phase8f_weight_statistics.md',f)
    h=['# Phase8H 六個 kappa_lambda benchmark 的共同來源診斷','',
       '## 目標、實際輸入與方法','',
       '讀取原已產生的6000列actual full-mass ME reweights，沒有呼叫MG5或MadLoop。六個benchmark共用1000個C1000 source events；source ordinal與hard-event SHA256逐筆join本次native ROOT summaries。每來源恰六個不同label，duplicate/missing/hash mismatch/nonfinite/normalization不符均拒絕。','',
       '來源是歷史NNPDF23 LO、two-loop alpha_s、seed20261122，不重標CTEQ6L1，不引入corrected SM1000。RAW_PRODUCTION weight已含sigma/N與ME ratio；MODEL_BR_ONLY欄已乘一次mixed HH factor。immutable CSV SHA256：`c76dd54b9236ee8110385fe746eb465125c70f1f30e0d580ac95acacc03a9e0f`。','',
       '## 實際 weighted support','',
       '| kappa_lambda | input ESS | final ESS | max ratio | top1 fraction | top5 fraction | top10 fraction | status |',
       '|---|---:|---:|---:|---:|---:|---:|---|']
    for r in kappa['summaries']:
        h.append(f"| {number(r['kappa_lambda'])} | {number(r['input']['ESS'])} | {number(r['final']['ESS'])} | {number(r['max_weight_ratio'])} | {number(r['top1_contribution_fraction'])} | {number(r['top5_contribution_fraction'])} | {number(r['top10_contribution_fraction'])} | {r['status']} |")
    h+=['','## 共用事件 covariance 與 per-bin 品質','',
        '每原始來源建立六維contribution vector，未通過者保留零。Cov(S_k,S_l)=N/(N-1) sum_i(x_i,k-mean_k)(x_i,l-mean_l)。各stage完整6x6 covariance與correlation維持pairing；marginal variance=0時correlation=null。6000 rows不視為6000獨立事件。','',
        '| Stage | minimum eigenvalue | arithmetic PSD tolerance | result |','|---|---:|---:|---|']
    for m in kappa['covariance_by_stage']:h.append(f"| {m['stage']} | {number(m['minimum_eigenvalue'])} | {number(m['PSD_absolute_tolerance'])} | {m['PSD_status']} |")
    h+=['',f"實際{kappa['bin_quality_rows']}個bin/kappa/stage診斷含flows、source count、moments、ESS、最大來源比例與missing。EMPTY_BIN、LOW_ESS_LT10/LT20、HIGH_SINGLE_EVENT_DOMINANCE、CANCELLATION_DOMINATED保留具體數據；不能以全樣本ESS代替bin precision。",'',
        '## Dominant source、統計限制與驗證','']
    for r in tails:
        if r['kappa_lambda'] in (2.5,5):
            d=r['dominant_sources'][0];h.append(f"kappa={r['kappa_lambda']}最大來源ordinal {d['source_event_ordinal']}，ratio={number(d['ratio'])}，hard-event SHA256 `{d['source_event_sha256']}`。")
    h+=['','kappa=2.5與5維持INCONCLUSIVE_REWEIGHTING。shared-event covariance只描述此proposal的MC sampling，不替代target-benchmark獨立integrals，也不修復歷史絕對normalization。無physical kappa interval。獨立Decimal70重算全部stage covariance/correlation、所有bin ESS與tail fractions；PSD容差綁定matrix norm及binary64 epsilon，沒有剪裁eigenvalues。','',
        '## 未解問題與下一步','',
        '未來須分別審查獨立kappa proposals或multiple-importance-sampling設計，保留proposal probabilities、各來源N、組合權重與correlations；不能複製rows假增事件。本次不執行production。']
    write(output/'phase8h_kappa_lambda.md',h)
    j=['# Phase8J RooFit / RooStats synthetic likelihood 方法','',
       '## 目標與實際輸入','',
       '本次實際執行native RooFit/RooStats likelihood tests。所有數據是明確定義的人工正yield toy，標記SYNTHETIC_METHOD_ONLY；沒有用HH或背景資料做inference。typed template要求dataset/process/region/observable、edges、expected bins、sumw2、signed status、normalization、overlap、systematics、source identity與validation state。','',
       '## 選擇與算法','',
       'counting Poisson用signal10、background20、Asimov count30驗證mu MLE、log likelihood、analytic likelihood ratio、curvature variance及boundary。RooStats實際建立Asimov count並計算profile-likelihood interval。','',
       '人工Gaussian peak總signal20覆蓋smooth positive background；各bin由Gaussian積分決定。extended binned model以Poisson product驗證total-Poisson乘multinomial等價。模型包含mu>=0、Gaussian auxiliary nuisance、正log-normal rate、背景normalization、保持總量的exponential shape morph與scaled-Poisson effective-count MC-stat auxiliary。effective-count僅為toy方法，不是signed MC一般解法。','',
       '## 實際數值測試','',
       '| Test | result | evidence |','|---|---|---|']
    for r in methods['tests']:j.append(f"| {r['name']} | {'PASS' if r['pass'] else 'FAIL'} | {r['evidence_class']} |")
    binned=next(r['details'] for r in methods['tests'] if r['name']=='extended_binned_Asimov_recovery')
    j+=['',f"Binned Asimov實測 mu={number(binned['mu_hat'])}、Gaussian normalization pull={number(binned['Gaussian_norm_pull'])}、shape pull={number(binned['shape_pull'])}、positive rate beta={number(binned['lognormal_rate'])}、max|gamma_MC-1|={number(binned['max_MC_factor_minus_one'])}、EDM={number(binned['EDM'])}。使用strategy={binned['minimizer_strategy']}、tolerance={number(binned['minimizer_tolerance'])}及有限call/iteration上限；同時檢查pull closure，fit status0本身不替代Asimov closure。"]
    covariance=next(r['details'] for r in methods['tests'] if r['name']=='count_covariance')
    j+=['',f"Counting toy 的外部 Hessian covariance={number(covariance['covariance_matrix_variance'])}，analytic variance={number(covariance['analytic_variance'])}；沿用absolute0.005測試容差。bounded RooRealVar的Minuit symmetric error平方={number(covariance['mu_error_squared'])}，受有界參數內部座標變換影響，分開記錄。covariance gate比較實際Hessian矩陣元素；不把bounded error平方誤當該矩陣。"]
    j+=['',f"共{methods['test_count']}項synthetic checks，狀態`{methods['status']}`，deterministic toy seed={methods['toy_seed']}；方法收據SHA256 `{digest(args.methods)}`。",'',
        '## Zero / negative policy與統計限制','',
        'n=0、lambda=0的log likelihood為0；n>0、lambda=0為負無限，不換成假小正數。small-positive expectation走log domain。negative/nonfinite expected bin、未建立signed-weight Poisson model、缺provenance、unknown overlap/systematics均拒絕；不把負bin剪成0，不把unknown nuisance改成零寬。','',
        '## 驗證、未解問題與下一步','',
        '成功只表示方法驗證：PHYSICAL_COMBINED_LIKELIHOOD=BLOCKED_OVERLAP_AND_CALIBRATION；PHYSICAL_SIGNIFICANCE、PHYSICAL_CLs_LIMIT與PHYSICAL_KAPPA_INTERVAL均NOT_EVALUATED，禁止discovery claim。未來實際templates須補overlap、fake、物理normalization、official calibration與nuisance correlations後另審physical gate；本次不解除gate。']
    write(output/'phase8j_likelihood_methods.md',j)
    return ['phase8f_weight_statistics.md','phase8h_kappa_lambda.md','phase8j_likelihood_methods.md']

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('statistics-index','kappa-directory','methods','independent-receipt','report-directory'):p.add_argument('--'+name,required=True)
    args=p.parse_args();print(json.dumps({'reports_written':generate(args)},ensure_ascii=False))
if __name__=='__main__':main()
