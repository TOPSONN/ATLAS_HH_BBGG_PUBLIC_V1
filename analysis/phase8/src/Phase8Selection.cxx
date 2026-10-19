#include "Phase8Selection.hxx"
namespace atlas_hh::phase8 {
void rank_objects(std::vector<Object>& v){std::sort(v.begin(),v.end(),[](const auto&a,const auto&b){return a.pt!=b.pt?a.pt>b.pt:a.index<b.index;});}
void select(Event& e){rank_objects(e.photons);rank_objects(e.jets);e.selected.clear();e.eligible.clear();e.tagged.clear();
 for(const auto&p:e.photons)if(atlas_hh::delphes::photon_fiducial(p.pt,p.eta))e.selected.push_back(p);
 for(const auto&j:e.jets)if(atlas_hh::delphes::jet_fiducial(j.pt,j.eta)){e.eligible.push_back(j);if(j.btag&1U)e.tagged.push_back(j);}
 e.stages={true,e.selected.size()>=2&&e.selected[0].pt>35,false,false,false};e.stages[2]=e.stages[1]&&e.eligible.size()>=2;e.stages[3]=e.stages[2]&&e.tagged.size()>=2;
 if(e.stages[3]){const auto m=(e.selected[0].p+e.selected[1].p).mass();e.stages[4]=m>=105&&m<=160;}
}
}
