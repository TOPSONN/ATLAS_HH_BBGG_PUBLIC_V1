// Independent read-only weight-vector and reconstruction regression.
#define main retained_phase6g_background_main
#include "../../../new_backgrounds/src/analyze_background_root.cxx"
#undef main
int main(int argc,char**argv){try{
 require(argc==5,"ROOT/input-index/fresh-output/count required");
 long entries;Adapter a(argv[1],&entries);const long count=std::stol(argv[4]);require(entries==count,"entry count mismatch");
 InputIndex index(argv[2]);auto output=out(argv[3]);
 for(long i=1;i<=count;++i){
  InputEvent s;require(index.next(s)&&s.ordinal==i,"source index mismatch");a.read(i-1);
  auto event=a.get<HepMCEvent>("Event");require(event.size()==1&&event[0]->Number==s.number&&event[0]->Weight==float(s.contribution),"Event weight mismatch");
  auto w=a.get<Weight>("Weight");require(w.size()==s.weights.size(),"named weight multiplicity mismatch");
  for(std::size_t j=0;j<w.size();++j)require(w[j]->Weight==float(s.weights[j]),"named weight value mismatch");
  for(auto&[name,b]:a.branches)if(b.present)for(int j=0;j<b.array->GetEntriesFast();++j)finite_members(b.array->At(j));
  std::vector<Object>ph,jets,tagged;std::map<int,unsigned>flavors;
  int n=0;for(auto*p:a.get<Photon>("Photon")){auto v=polar(p->PT,p->Eta,p->Phi,0);derived_p4(v);if(photon_fiducial(p->PT,p->Eta))ph.push_back({n,p->PT,p->Eta,v,0});++n;}
  n=0;for(auto*j:a.get<Jet>("Jet")){auto v=polar(j->PT,j->Eta,j->Phi,j->Mass);finite_cartesian(v);if(jet_fiducial(j->PT,j->Eta)){jets.push_back({n,j->PT,j->Eta,v,j->BTag});flavors[n]=j->Flavor;}++n;}
  auto order=[](const Object&x,const Object&y){return x.pt>y.pt;};std::stable_sort(ph.begin(),ph.end(),order);std::stable_sort(jets.begin(),jets.end(),order);
  for(auto&j:jets)if(j.tag&1U)tagged.push_back(j);
  bool havegg=ph.size()>=2,havebb=tagged.size()>=2;P4 gg{},bb{};if(havegg)gg=ph[0].p+ph[1].p;if(havebb)bb=tagged[0].p+tagged[1].p;
  bool cp=havegg&&ph[0].pt>35,cj=cp&&jets.size()>=2,ct=cj&&havebb,cm=ct&&gg.mass()>=105&&gg.mass()<=160;
  output<<"{\"source_event_index\":"<<i<<",\"source_event_sha256\":"<<quoted(s.source_hash)<<",\"source_contribution_pb\":"<<s.contribution<<",\"original_N\":"<<s.source_count<<",\"all_ROOT_named_weights_verified\":true";
  output<<",\"m_gamma_gamma\":";mass(output,havegg,gg);output<<",\"m_bb\":";mass(output,havebb,bb);output<<",\"m_bb_gamma_gamma\":";mass(output,havegg&&havebb,gg+bb);
  output<<",\"pT_gamma_gamma\":";if(havegg)output<<gg.pt();else output<<"null";output<<",\"pT_bb\":";if(havebb)output<<bb.pt();else output<<"null";
  output<<",\"DeltaR_gamma_gamma\":";delta_r(output,havegg,havegg?ph[0].p:P4{},havegg?ph[1].p:P4{});output<<",\"DeltaR_bb\":";delta_r(output,havebb,havebb?tagged[0].p:P4{},havebb?tagged[1].p:P4{});
  output<<",\"N_jets\":"<<jets.size()<<",\"N_btags\":"<<tagged.size()<<",\"cut_photons\":"<<(cp?"true":"false")<<",\"cut_jets\":"<<(cj?"true":"false")<<",\"cut_two_btags\":"<<(ct?"true":"false")<<",\"cut_mgg\":"<<(cm?"true":"false")<<",\"eligible_jets\":[";
  bool comma=false;for(auto&j:jets){if(comma)output<<',';comma=true;output<<"{\"index\":"<<j.index<<",\"pt\":"<<j.pt<<",\"eta\":"<<j.eta<<",\"flavor\":"<<flavors.at(j.index)<<",\"btag\":"<<j.tag<<'}';}output<<"]}\n";
 }
 InputEvent extra;require(!index.next(extra),"extra source index");return 0;
 }catch(const std::exception&e){std::cerr<<"INDEPENDENT_ROOT_FEATURE_QA_FAILED: "<<e.what()<<'\n';return 2;}}
