#pragma once
// The official LHEF reader supplies the physics. This wrapper checks and logs
// its actual setEvent() consumption, including reads during internal retries.
#include "Pythia8/Pythia.h"
#include <algorithm>
#include <cmath>
#include <fstream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace atlas_hh {
struct SourceParticle {
  int id,status,m1,m2,c1,c2;
  double px,py,pz,e,m,tau,spin;
};
struct SourceEvent {
  long index;
  std::string hash;
  int nup,process;
  double weight,scale,alpha_qed,alpha_qcd;
  std::vector<SourceParticle> particles;
};

class TrackedLHA : public Pythia8::LHAup {
  std::string input_name_;
  std::ifstream index_;
  std::unique_ptr<Pythia8::LHAupLHEF> reader_;
  long limit_,cursor_ = 0,verified_cursor_ = 0,identity_errors_ = 0;
  std::vector<SourceEvent> consumed_;
  static void require(bool ok,const std::string& reason) {
    if(!ok)throw std::runtime_error("EVENT_IDENTITY: "+reason);
  }
  static bool close(double a,double b) {
    return std::isfinite(a)&&std::isfinite(b)&&std::abs(a-b)<=1e-13*std::max({1.0,std::abs(a),std::abs(b)});
  }
public:
  bool intentional_limit=false,physical_eof=false;
  TrackedLHA(std::string input,std::string source_index,long limit)
    :input_name_(std::move(input)),index_(source_index),limit_(limit) {
    require(index_.good(),"source index could not be opened");
  }
  bool useExternal() override {return true;}
  bool fileFound() override {return index_.good();}
  bool setInit() override {
    // infoPtr is supplied by Pythia before setInit, avoiding a const_cast of
    // its public Info view. Keep Beams:frameType=4 and the real LHEF reader.
    reader_=std::make_unique<Pythia8::LHAupLHEF>(infoPtr,input_name_.c_str(),nullptr,true,false);
    if(!reader_->fileFound()||!reader_->setInit())return false;
    require(reader_->strategy()==-4,"validated baseline requires IDWTUP=-4");
    require(reader_->idBeamA()==2212&&reader_->idBeamB()==2212,"non-proton beams");
    require(close(reader_->eBeamA(),6500)&&close(reader_->eBeamB(),6500),"beam energy differs from 13 TeV baseline");
    setBeamA(reader_->idBeamA(),reader_->eBeamA(),reader_->pdfGroupBeamA(),reader_->pdfSetBeamA());
    setBeamB(reader_->idBeamB(),reader_->eBeamB(),reader_->pdfGroupBeamB(),reader_->pdfSetBeamB());
    setStrategy(reader_->strategy());
    for(int i=0;i<reader_->sizeProc();++i)addProcess(reader_->idProcess(i),reader_->xSec(i),reader_->xErr(i),reader_->xMax(i));
    return true;
  }
  void beginAttempt() {consumed_.clear();}
  long cursor() const {return cursor_;}
  long verifiedCursor() const {return verified_cursor_;}
  long identityErrors() const {return identity_errors_;}
  const std::vector<SourceEvent>& consumed() const {return consumed_;}
  bool setEvent(int process=0) override {
    if(cursor_>=limit_) {intentional_limit=true;return false;}
    if(!reader_->setEvent(process)) {physical_eof=true;return false;}
    // The official reader consumed an event even when the independent source
    // comparison below fails. Never hide that read behind a verified counter.
    ++cursor_;
    try {
    SourceEvent source{};std::string marker;
    require(bool(index_>>marker>>source.index>>source.hash>>source.nup>>source.process>>source.weight
      >>source.scale>>source.alpha_qed>>source.alpha_qcd),"truncated source index");
    require(marker=="E"&&source.index==cursor_&&source.hash.size()==64,"source index cursor/hash mismatch");
    require(source.nup>0&&source.nup<=100000,"unbounded or invalid source particle count");
    require(reader_->sizePart()==source.nup+1&&reader_->idProcess()==source.process,"actual LHE process/particle count mismatch");
    require(close(reader_->weight(),source.weight)&&close(reader_->scale(),source.scale)
      &&close(reader_->alphaQED(),source.alpha_qed)&&close(reader_->alphaQCD(),source.alpha_qcd),"actual LHE header mismatch");
    source.particles.reserve(source.nup);
    for(int i=1;i<=source.nup;++i) {
      SourceParticle p{};
      require(bool(index_>>marker>>p.id>>p.status>>p.m1>>p.m2>>p.c1>>p.c2
        >>p.px>>p.py>>p.pz>>p.e>>p.m>>p.tau>>p.spin)&&marker=="P","truncated source particle index");
      require(reader_->id(i)==p.id&&reader_->status(i)==p.status&&reader_->mother1(i)==p.m1
        &&reader_->mother2(i)==p.m2&&reader_->col1(i)==p.c1&&reader_->col2(i)==p.c2,"actual LHE particle identity/ancestry/color mismatch");
      require(close(reader_->px(i),p.px)&&close(reader_->py(i),p.py)&&close(reader_->pz(i),p.pz)
        &&close(reader_->e(i),p.e)&&close(reader_->m(i),p.m)&&close(reader_->tau(i),p.tau)
        &&close(reader_->spin(i),p.spin),"actual LHE particle momentum/mass mismatch");
      source.particles.push_back(p);
    }
    require(consumed_.size()<64,"more than 64 internal source reads in one next() call; stop with partial evidence");
    consumed_.push_back(source);
    ++verified_cursor_;
    setProcess(reader_->idProcess(),reader_->weight(),reader_->scale(),reader_->alphaQED(),reader_->alphaQCD());
    for(int i=1;i<reader_->sizePart();++i)addParticle(reader_->id(i),reader_->status(i),reader_->mother1(i),
      reader_->mother2(i),reader_->col1(i),reader_->col2(i),reader_->px(i),reader_->py(i),reader_->pz(i),
      reader_->e(i),reader_->m(i),reader_->tau(i),reader_->spin(i),reader_->scale(i));
    setIdX(reader_->id1(),reader_->id2(),reader_->x1(),reader_->x2());
    if(reader_->pdfIsSet())setPdf(reader_->id1pdf(),reader_->id2pdf(),reader_->x1pdf(),reader_->x2pdf(),
      reader_->scalePDF(),reader_->pdf1(),reader_->pdf2(),true);
    if(reader_->scaleShowersIsSet())setScaleShowers(reader_->scaleShowers(0),reader_->scaleShowers(1));
    return true;
    } catch(const std::exception&) {
      ++identity_errors_;
      throw;
    }
  }
};
}
