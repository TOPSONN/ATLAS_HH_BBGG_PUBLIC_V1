// Read-only existing ROOT ledger. Never creates shower/detector/source events.
#define main retained_background_main
#include "../../../new_backgrounds/src/analyze_background_root.cxx"
#undef main
#include <functional>
int main(int argc,char**argv){try{
 require(argc==5,"ROOT/index/fresh-output/count required");
 long entries;Adapter a(argv[1],&entries);long count=std::stol(argv[4]);require(entries==count,"entry count mismatch");
 InputIndex index(argv[2]);auto output=out(argv[3]);
 for(long i=1;i<=count;++i){
  InputEvent s;require(index.next(s)&&s.ordinal==i,"source index mismatch");a.read(i-1);
  auto event=a.get<HepMCEvent>("Event");require(event.size()==1&&event[0]->Number==s.number&&event[0]->Weight==float(s.contribution),"Event weight mismatch");
  auto weights=a.get<Weight>("Weight");require(weights.size()==s.weights.size(),"named weight multiplicity");
  for(std::size_t j=0;j<weights.size();++j)require(weights[j]->Weight==float(s.weights[j]),"named weight mismatch");
  std::vector<double> photons,jets;int tags=0;
  for(auto*p:a.get<Photon>("Photon"))if(photon_fiducial(p->PT,p->Eta))photons.push_back(p->PT);
  for(auto*j:a.get<Jet>("Jet"))if(jet_fiducial(j->PT,j->Eta)){jets.push_back(j->PT);if(j->BTag&1U)++tags;}
  std::stable_sort(photons.begin(),photons.end(),std::greater<double>());
  std::stable_sort(jets.begin(),jets.end(),std::greater<double>());
  output<<"{\"source_event_index\":"<<i<<",\"source_event_sha256\":\""<<s.source_hash<<"\",\"source_contribution_pb\":"<<s.contribution;
  output<<",\"N_photons\":"<<photons.size()<<",\"N_jets\":"<<jets.size()<<",\"N_btags\":"<<tags;
  for(int j=0;j<2;++j){output<<",\"photon_pt_"<<j+1<<"\":";if(photons.size()>std::size_t(j))output<<photons[j];else output<<"null";
   output<<",\"jet_pt_"<<j+1<<"\":";if(jets.size()>std::size_t(j))output<<jets[j];else output<<"null";}
  output<<"}\n";
 }
 InputEvent extra;require(!index.next(extra),"extra input index row");
 std::cout<<"PASS_EXISTING_ROOT_OBJECT_PT_AND_ALL_NAMED_WEIGHTS "<<count<<'\n';return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 2;}}
