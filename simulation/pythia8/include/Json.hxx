#pragma once
#include <cmath>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <string>

namespace atlas_hh {
inline std::string quoted(const std::string& value) {
  std::ostringstream out;out << '"';
  for(unsigned char c:value) {
    switch(c) {case '"':out<<"\\\"";break;case '\\':out<<"\\\\";break;
      case '\n':out<<"\\n";break;case '\r':out<<"\\r";break;case '\t':out<<"\\t";break;
      default:if(c<32)out<<"\\u"<<std::hex<<std::setw(4)<<std::setfill('0')<<int(c)<<std::dec;
      else out<<c;}
  }
  out << '"';return out.str();
}
inline std::string real(double value) {
  if(!std::isfinite(value))throw std::runtime_error("non-finite diagnostic value");
  std::ostringstream out;out<<std::setprecision(17)<<value;return out.str();
}
}
