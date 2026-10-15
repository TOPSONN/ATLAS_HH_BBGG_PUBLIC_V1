"""Native ROOT numerical output only; no canvas, PDF or PNG creation."""
import sys,csv,math
from array import array
from pathlib import Path
import ROOT
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from simulation.hh_signal.campaign.analysis import BINS
from simulation.hh_signal.campaign.common import require

def main():
    source,output=map(Path,sys.argv[1:]);require(not output.exists(),'ROOT numerical output exists')
    groups={}
    for r in csv.DictReader(source.open()):
        k=(r['process'],r['kappa_lambda'],r['stage'],r['observable']);groups.setdefault(k,[]).append(r)
    f=ROOT.TFile(str(output),'CREATE');require(not f.IsZombie(),'cannot create native numerical ROOT')
    for key,rows in groups.items():
        process,k,stage,observable=key;edges=BINS[observable];name='_'.join([process,'kl'+k if k else 'baseline',stage,observable]).replace('-','m').replace('.','p')
        for suffix,column,error in [('MODEL_SCOPE_PB','sumw','sumw2'),('SOURCE_SAMPLING_PB','sumw','source_sampling_variance'),
           ('UNIT_AREA_SHAPE_ONLY','UNIT_AREA_SHAPE_ONLY','unit_area_source_sampling_variance'),
           ('COMMON_LUMINOSITY_EXPLORATORY_100FB','expected_weighted_count_at_100fb_inverse','sumw2')]:
            h=ROOT.TH1D(name+'_'+suffix,suffix,len(edges)-1,array('d',edges));h.Sumw2()
            for row in rows:
                b=int(row['bin']);content=float(row[column]) if row[column] else 0.;err=math.sqrt(float(row[error])) if row[error] else 0.
                if suffix=='COMMON_LUMINOSITY_EXPLORATORY_100FB':err*=100000
                h.SetBinContent(b,content);h.SetBinError(b,err)
            h.SetEntries(sum(int(r['entries']) for r in rows));h.Write()
    ROOT.TNamed('scope','Numerical histograms only; MODEL_BR_ONLY/EXPLORATORY; zero/cancellation shape states in bound CSV; no combined physical background').Write()
    f.Close();check=ROOT.TFile.Open(str(output),'READ');require(check and not check.IsZombie() and not check.TestBit(ROOT.TFile.kRecovered),'native ROOT histogram readback failed')
    require(check.GetListOfKeys().GetSize()==len(groups)*4+1,'native histogram count mismatch')
    for key in check.GetListOfKeys():
        obj=key.ReadObj()
        if obj.InheritsFrom('TH1'):
            for b in range(obj.GetNbinsX()+2):require(math.isfinite(obj.GetBinContent(b)) and math.isfinite(obj.GetBinError(b)),'nonfinite native numerical histogram')
    print('PASS_NATIVE_NUMERICAL_ROOT_HISTOGRAM_WRITE_AND_READBACK',check.GetListOfKeys().GetSize());check.Close()

if __name__=='__main__':main()
