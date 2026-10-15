#pragma once
#include "Authorization.hxx"
namespace zh {
class SingleSourceRead {
  bool read_=false;
  long denied_=0;
public:
  void begin(){read_=false;}
  void permit(){
    if(read_){++denied_;throw std::runtime_error("PARTIAL_INTERNAL_RETRY_BLOCKED: second source read in one next() call refused before consuming input");}
    read_=true;
  }
  long denied()const{return denied_;}
};
}
