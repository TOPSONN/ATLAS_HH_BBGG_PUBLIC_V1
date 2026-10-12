#include "AtlasSidebandDiagnostics.h"
#include <algorithm>
#include <bit>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <limits>
#include <numeric>
#include <sstream>
#include <stdexcept>

namespace atlas::sidebands {
namespace {
void require(bool valid,const char* message) {if(!valid)throw std::invalid_argument(message);}
void finite(const std::vector<long double>& v) {for(auto x:v)require(std::isfinite(x),"Nonfinite diagnostic input");}
}
std::string sha256(std::string_view bytes) {
  require(bytes.size()<=64*1024*1024,"SHA256 input exceeds diagnostic bound");
  std::vector<std::uint8_t> data(bytes.begin(),bytes.end());
  const auto bits=static_cast<std::uint64_t>(data.size())*8;
  data.push_back(0x80);while(data.size()%64!=56)data.push_back(0);
  for(int i=7;i>=0;--i)data.push_back(static_cast<std::uint8_t>(bits>>(8*i)));
  std::array<std::uint32_t,8> h{0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
  constexpr std::array<std::uint32_t,64> k{
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
  for(std::size_t block=0;block<data.size();block+=64) {
    std::array<std::uint32_t,64> w{};
    for(std::size_t i=0;i<16;++i)for(std::size_t j=0;j<4;++j)w[i]=(w[i]<<8)|data[block+4*i+j];
    for(std::size_t i=16;i<64;++i) {
      const auto s0=std::rotr(w[i-15],7)^std::rotr(w[i-15],18)^(w[i-15]>>3);
      const auto s1=std::rotr(w[i-2],17)^std::rotr(w[i-2],19)^(w[i-2]>>10);
      w[i]=w[i-16]+s0+w[i-7]+s1;
    }
    auto a=h[0],b=h[1],c=h[2],d=h[3],e=h[4],f=h[5],g=h[6],hh=h[7];
    for(std::size_t i=0;i<64;++i) {
      const auto t1=hh+(std::rotr(e,6)^std::rotr(e,11)^std::rotr(e,25))+((e&f)^((~e)&g))+k[i]+w[i];
      const auto t2=(std::rotr(a,2)^std::rotr(a,13)^std::rotr(a,22))+((a&b)^(a&c)^(b&c));
      hh=g;g=f;f=e;e=d+t1;d=c;c=b;b=a;a=t1+t2;
    }
    h[0]+=a;h[1]+=b;h[2]+=c;h[3]+=d;h[4]+=e;h[5]+=f;h[6]+=g;h[7]+=hh;
  }
  std::ostringstream out;out<<std::hex<<std::setfill('0');for(auto x:h)out<<std::setw(8)<<x;return out.str();
}
std::string sha256_file(const std::filesystem::path& p,std::uint64_t limit) {
  require(limit<=64*1024*1024&&std::filesystem::is_regular_file(p)&&std::filesystem::file_size(p)<=limit,"Hash requires bounded regular file");
  std::ifstream in(p,std::ios::binary);require(static_cast<bool>(in),"Hash file unreadable");
  std::string bytes;bytes.reserve(static_cast<std::size_t>(std::filesystem::file_size(p)));char c=0;
  while(in.get(c)) {require(bytes.size()<limit,"File grew beyond hash bound");bytes.push_back(c);}
  require(!in.bad(),"Hash file read failed");return sha256(bytes);
}
std::string canonical_identity(std::uint32_t run,std::uint64_t event) {
  return "ATLAS_HH_BBGG_PUBLIC_V1|DATA93915|run="+std::to_string(run)+"|event="+std::to_string(event);
}
int identity_fold(std::uint32_t run,std::uint64_t event) {
  const auto digest=sha256(canonical_identity(run,event));
  // Last hex nibble of the first digest byte contains its low bit.
  const auto c=digest[1];const int nibble=c<='9'?c-'0':c-'a'+10;return nibble&1;
}
int mass_category(double mass) {
  require(std::isfinite(mass),"Mass category requires finite mass");
  for(std::size_t i=0;i<categories;++i)if(mass>=mass_low[i]&&(mass<mass_high[i]||(i+1==categories&&mass==160)))return static_cast<int>(i);
  return -1;
}
Statistic pearson(const std::vector<long double>& x,const std::vector<long double>& y) {
  require(x.size()==y.size(),"Correlation size mismatch");finite(x);finite(y);
  long double mx=0,my=0,xx=0,yy=0,xy=0;std::size_t n=0;
  for(std::size_t i=0;i<x.size();++i) {++n;const auto dx=x[i]-mx,dy=y[i]-my;mx+=dx/n;my+=dy/n;xx+=dx*(x[i]-mx);yy+=dy*(y[i]-my);xy+=dx*(y[i]-my);}
  Statistic s;s.n=n;
  if(n>=2&&xx>0&&yy>0) {s.value=xy/std::sqrt(xx*yy);require(std::isfinite(s.value),"Nonfinite correlation");s.defined=true;}return s;
}
std::vector<long double> tied_ranks(const std::vector<long double>& v) {
  finite(v);std::vector<std::size_t> order(v.size());std::iota(order.begin(),order.end(),0);
  std::stable_sort(order.begin(),order.end(),[&](auto a,auto b){return v[a]<v[b];});
  std::vector<long double> out(v.size());
  for(std::size_t i=0;i<v.size();) {auto j=i+1;while(j<v.size()&&v[order[j]]==v[order[i]])++j;
    const auto rank=static_cast<long double>(i+j-1)/2+1;for(auto k=i;k<j;++k)out[order[k]]=rank;i=j;}return out;
}
Statistic empirical_ks(std::vector<double> a,std::vector<double> b) {
  for(auto x:a)require(std::isfinite(x),"Nonfinite KS sample");
  for(auto x:b)require(std::isfinite(x),"Nonfinite KS sample");
  Statistic s;s.n=a.size();s.n_other=b.size();if(a.empty()||b.empty())return s;
  std::sort(a.begin(),a.end());std::sort(b.begin(),b.end());std::size_t i=0,j=0;
  while(i<a.size()||j<b.size()) {
    const auto x=i==a.size()?b[j]:(j==b.size()?a[i]:std::min(a[i],b[j]));
    while(i<a.size()&&a[i]<=x)++i;
    while(j<b.size()&&b[j]<=x)++j;
    s.value=std::max(s.value,std::abs(static_cast<long double>(i)/a.size()-static_cast<long double>(j)/b.size()));
  }
  s.defined=true;return s;
}
Contingency cramers_v(const std::array<std::size_t,categories>& a,const std::array<std::size_t,categories>& b) {
  Contingency r;for(std::size_t i=0;i<categories;++i) {r.row_totals[0]+=a[i];r.row_totals[1]+=b[i];r.populated_columns+=(a[i]+b[i])>0;r.zero_cells+=(a[i]==0)+(b[i]==0);r.cells_below_five+=(a[i]<5)+(b[i]<5);}
  auto& s=r.association;s.n=r.row_totals[0];s.n_other=r.row_totals[1];
  if(!s.n||!s.n_other||r.populated_columns<2)return r;
  const auto total=static_cast<long double>(s.n)+s.n_other;long double chi2=0;
  for(std::size_t i=0;i<categories;++i)if(a[i]+b[i])for(int row=0;row<2;++row) {
    const auto expected=static_cast<long double>(r.row_totals[row])*(a[i]+b[i])/total;
    const auto observed=static_cast<long double>(row==0?a[i]:b[i]);const auto d=observed-expected;chi2+=d*d/expected;
  }
  // min(rows-1, populated_columns-1)=1 for any defined 2-row table.
  s.value=std::sqrt(chi2/total);require(std::isfinite(s.value),"Nonfinite Cramers V");s.defined=true;return r;
}
Shape conditional_shape(const std::array<std::size_t,categories>& counts) {
  Shape s;s.total=std::accumulate(counts.begin(),counts.end(),std::size_t{});if(!s.total)return s;s.defined=true;
  for(std::size_t i=0;i<categories;++i)s.fraction[i]=static_cast<long double>(counts[i])/s.total;
  for(std::size_t i=0;i<categories;++i)for(std::size_t j=0;j<categories;++j)
    s.covariance[i][j]=((i==j?s.fraction[i]:0)-s.fraction[i]*s.fraction[j])/s.total;
  return s;
}
std::array<long double,2> wilson95(std::size_t successes,std::size_t n) {
  require(n>0&&successes<=n,"Invalid counting-fraction denominator");constexpr long double z=1.959963984540054L;
  const auto p=static_cast<long double>(successes)/n,den=1+z*z/n,centre=(p+z*z/(2*n))/den;
  const auto half=z*std::sqrt(p*(1-p)/n+z*z/(4*static_cast<long double>(n)*n))/den;
  return {std::max(0.L,centre-half),std::min(1.L,centre+half)};
}
}  // namespace atlas::sidebands
