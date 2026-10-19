#include "Phase8TruthMatching.hxx"
namespace atlas_hh::phase8 {
TruthReader::TruthReader(const fs::path& p,const std::string& f):input(p),format(f){demand(input.good(),"missing truth index");if(f=="continuum"){continuum=std::make_unique<atlas_hh::delphes::TruthIndex>(p.string());return;}std::string magic;input>>magic;demand(magic==(f=="signal"?"S01_SIGNAL_TRUTH_V1":"ATLAS_NEW_BACKGROUND_TRUTH_V1"),"wrong truth index profile");}
void TruthReader::next(const atlas_hh::delphes::InputEvent& source,Event& e){
 if(continuum){atlas_hh::delphes::TruthEvent t;demand(continuum->next(t)&&t.ordinal==source.ordinal&&t.number==source.number&&t.source_index==source.source_index&&t.source_hash==source.source_hash,"continuum truth/source identity mismatch");e.truth={{"status","NOT_APPLICABLE_NO_TRUTH_HH"},{"truth_source_validated",true}};return;}
 std::string key;long ordinal=0;int hbb=0,hgg=0;std::string hash;std::vector<int> gamma,bottom;
 auto ids=[&](const char* label){int n;demand(bool(input>>key>>n)&&key==label&&n>=0&&n<=100000,"invalid truth object list");std::vector<int> out;std::set<int> unique;for(int i=0;i<n;++i){int id;demand(bool(input>>id)&&id>0&&unique.insert(id).second,"duplicate/invalid truth id");out.push_back(id);}return out;};
 if(format=="signal"){demand(bool(input>>key>>ordinal>>hash>>hbb>>hgg)&&key=="E"&&hbb!=hgg&&hbb>0&&hgg>0,"invalid signal truth row");demand(ordinal==source.source_index&&hash==source.source_hash,"signal truth/source identity mismatch");gamma=ids("G");bottom=ids("B");demand(gamma.size()==2&&bottom.size()==2,"signal daughter counts");}
 else{long index;int h,z,t,tbar,wp,wm;demand(bool(input>>key>>ordinal>>index>>h>>z>>t>>tbar>>wp>>wm)&&key=="E"&&ordinal==source.ordinal&&index==source.source_index,"background truth/source identity mismatch");auto birth=ids("H");gamma=ids("G");bottom=ids("B");auto born=ids("O"),shower=ids("S"),hadron=ids("D"),other=ids("X");
  if(e.dataset=="B06")demand(h==0&&z==0&&t==0&&tbar==0&&birth.empty()&&gamma.empty(),"B06 invented Higgs truth");else{demand(h>0&&birth.size()==2,"missing background Higgs truth");hgg=h;}
  (void)born;(void)shower;(void)hadron;(void)other;
 }
 std::map<int,const atlas_hh::delphes::InputParticle*> byid;for(const auto&p:source.particles)demand(byid.emplace(p.id,&p).second,"duplicate upstream truth particle id");
 if(hgg){demand(byid.count(hgg)&&byid.at(hgg)->pid==25,"truth Hgg identity missing");}
 if(hbb){demand(byid.count(hbb)&&byid.at(hbb)->pid==25,"truth Hbb identity missing");}
 std::vector<P4> truth_gamma,truth_b,reco_gamma,reco_jets;
 for(int id:gamma){demand(byid.count(id)&&byid.at(id)->pid==22&&byid.at(id)->status==1,"invalid final truth photon");truth_gamma.push_back(byid.at(id)->p);}
 for(int id:bottom){demand(byid.count(id)&&std::abs(byid.at(id)->pid)==5,"invalid truth bottom");truth_b.push_back(byid.at(id)->p);}
 for(const auto&p:e.photons){reco_gamma.push_back(p.p);}
 for(const auto&j:e.eligible){reco_jets.push_back(j.p);}
 if(format!="signal"){e.truth={{"status",e.dataset=="B06"?"NOT_APPLICABLE_NO_HIGGS":"SINGLE_HIGGS_BACKGROUND_GEOMETRIC_ONLY"},{"H_origin_final_photons",truth_gamma.size()},{"H_photon_matches",atlas_hh::delphes::unique_match(truth_gamma,reco_gamma,.2L).pairs.size()},{"truth_source_validated",true}};return;}
 auto g=atlas_hh::delphes::unique_match(truth_gamma,reco_gamma,.2L),b=atlas_hh::delphes::unique_match(truth_b,reco_jets,.4L);Json gd=Json::array(),bd=Json::array();for(const auto&p:g.pairs)gd.push_back(double(p.distance));for(const auto&p:b.pairs)bd.push_back(double(p.distance));
 e.truth={{"status","SIGNAL_GEOMETRIC_DIAGNOSTIC_NOT_CALIBRATED_EFFICIENCY"},{"Hgg_matched",g.pairs.size()},{"Hbb_matched",b.pairs.size()},{"Hgg_ambiguous_truth",g.ambiguous_truth},{"Hgg_ambiguous_reco",g.ambiguous_reco},{"Hbb_ambiguous_truth",b.ambiguous_truth},{"Hbb_ambiguous_reco",b.ambiguous_reco},{"Hgg_deltaR",gd},{"Hbb_deltaR",bd},{"missing_ancestry",0},{"native_particle_order_is_barcode",false}};
}
void TruthReader::finish(){if(continuum){atlas_hh::delphes::TruthEvent t;demand(!continuum->next(t),"extra continuum truth row");return;}std::string extra;demand(!(input>>extra)&&input.eof(),"extra/truncated truth records");}
}
