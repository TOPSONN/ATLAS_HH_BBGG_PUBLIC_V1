// Real reader API test only. Never calls Pythia::next(), showers or writes events.
#include "TrackedLHA.hxx"
#include <iostream>
#include <memory>
#include <stdexcept>

int main(int argc,char**argv){
  try{
    if(argc!=6)throw std::runtime_error("xml settings input valid_index corrupt_index required");
    for(bool corrupt:{false,true}){
      Pythia8::Pythia p(argv[1],false);
      if(!p.readFile(argv[2])||!p.readString("Beams:LHEF = "+std::string(argv[3]))
        ||!p.readString("Random:seed = 610201"))throw std::runtime_error("reader settings rejected");
      p.readString("Init:showChangedSettings = off");p.readString("Init:showProcesses = off");
      auto source=std::make_shared<atlas_hh::TrackedLHA>(argv[3],argv[corrupt?5:4],1);
      if(!p.setLHAupPtr(source)||!p.init())throw std::runtime_error("reader initialization failed");
      if(source->cursor()!=0||source->verifiedCursor()!=0)throw std::runtime_error("initialization consumed input");
      source->beginAttempt();bool failed=false;
      try{if(!source->setEvent())throw std::runtime_error("reader unexpectedly returned false");}
      catch(const std::exception&){failed=true;}
      if(corrupt){
        if(!failed||source->cursor()!=1||source->verifiedCursor()!=0||source->identityErrors()!=1)
          throw std::runtime_error("failed comparison hid actual source consumption");
      }else{
        if(failed||source->cursor()!=1||source->verifiedCursor()!=1||source->identityErrors()!=0||source->consumed().size()!=1)
          throw std::runtime_error("actual verified source cursor mismatch");
        if(source->setEvent()||source->cursor()!=1||!source->intentional_limit)
          throw std::runtime_error("source reader consumed past explicit event limit");
      }
    }
    std::cout<<"PASS: real LHE reader valid/corrupt sidecar and limit API cases; no Pythia next() or output events\n";
    return 0;
  }catch(const std::exception&e){std::cerr<<"FAIL: "<<e.what()<<'\n';return 1;}
}
